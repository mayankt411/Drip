"""Stage 2 network: a small CNN over a 16x16x6 tank chip, pooled radiometrically."""
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F


def geom_vec(sun_elev, sun_az):
    e, a = np.radians(sun_elev), np.radians(sun_az)
    return torch.tensor([np.sin(a), np.cos(a), np.sin(e), np.cos(e)], dtype=torch.float32)


class ChipNet(nn.Module):
    """chip (N,6,H,W) + sun geometry -> fill fraction in (0,1) per tank."""

    def __init__(self, arch="convnet", in_ch=6, geom_dim=4, dropout=0.3):
        super().__init__()
        self.register_buffer("mean", torch.zeros(in_ch))
        self.register_buffer("std", torch.ones(in_ch))
        self.arch = arch
        if arch == "resnet18":
            from torchvision.models import resnet18
            net = resnet18(weights=None)
            net.conv1 = nn.Conv2d(in_ch, 64, 3, 1, 1, bias=False)
            net.maxpool = nn.Identity()
            net.fc = nn.Identity()
            self.body, feat = net, 512
        else:
            self.body = nn.Sequential(
                nn.Conv2d(in_ch, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(),
                nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
                nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU())
            feat = 32 * 3
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(feat + in_ch + geom_dim, 32),
                                  nn.ReLU(), nn.Dropout(dropout), nn.Linear(32, 1))

    def set_norm(self, mean, std):
        self.mean.copy_(torch.as_tensor(mean, dtype=torch.float32))
        self.std.copy_(torch.as_tensor(std, dtype=torch.float32).clamp_min(1e-4))

    def forward(self, chips, geom):
        x = (chips - self.mean[None, :, None, None]) / self.std[None, :, None, None]
        f = self.body(x)
        if self.arch != "resnet18":
            f = torch.cat([f.mean((2, 3)), f.amax((2, 3)), f.amin((2, 3))], dim=1)
        raw = chips.mean((2, 3))
        g = geom.expand(chips.shape[0], -1)
        return torch.sigmoid(self.head(torch.cat([f, (raw - self.mean) / self.std, g], 1))).squeeze(1)


class HubModel(nn.Module):
    """Area-weighted mean fill over the valid tanks, then a positive affine map to stocks."""

    def __init__(self, **kw):
        super().__init__()
        self.net = ChipNet(**kw)
        self.a_raw = nn.Parameter(torch.tensor(0.5))
        self.b = nn.Parameter(torch.tensor(0.0))

    def mean_fill(self, chips, geom, weights):
        fill = self.net(chips, geom)
        return (fill * weights).sum() / weights.sum()

    def forward(self, chips, geom, weights):
        m = self.mean_fill(chips, geom, weights)
        return F.softplus(self.a_raw) * m + self.b, m
