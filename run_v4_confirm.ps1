# Confirmation run: same frozen radar model, scored on July 2024 onward (weeks nobody has inspected).
# Safe to rerun: finished steps are skipped.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force logs | Out-Null

function Step($name, $cmd, $tries = 24) {
    $done = "logs\$name.done"
    if (Test-Path $done) { Write-Host "skip $name"; return }
    for ($try = 1; $try -le $tries; $try++) {
        Write-Host "== $name (attempt $try)" -ForegroundColor Cyan
        & cmd /c "$cmd 2>&1" | Tee-Object -FilePath "logs\$name.log"
        if ($LASTEXITCODE -eq 0) { New-Item -ItemType File $done | Out-Null; return }
        if ($try -lt $tries) { Write-Host "step $name failed; retrying in 10 min" -ForegroundColor Yellow; Start-Sleep -Seconds 600 }
    }
    throw "step $name kept failing, see logs\$name.log"
}

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "No .venv found. Run run_ml_local.ps1 once first." }
$today = Get-Date -Format "yyyy-MM-dd"

Step "v4c_00_tests"    "$py -m pytest tests/ml -q" 2
Step "v4c_01_eia"      "$py -c ""from src.ml.eia import fetch_eia; fetch_eia('2024-07-01','$today')""" 3
Step "v4c_02_download" "$py -m src.ml.radar run"
Step "v4c_03_repeat"   "$py -m src.ml.evaluate_radar test" 3
Step "v4c_04_confirm"  "$py -m src.ml.evaluate_radar confirm" 3
Write-Host "Finished. Confirmation verdict:" -ForegroundColor Green
Get-Content results\h3_radar_confirm_verdict.json
Write-Host "Then run: git add src results data/manifest.csv configs tests run_v4_confirm.ps1 ; git status --short" -ForegroundColor Green
