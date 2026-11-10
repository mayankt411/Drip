# Radar study, start to finish, no input needed. Safe to rerun: finished steps are skipped.
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
if (-not (Test-Path $py)) { throw "No .venv found. Run run_ml_local.ps1 once first (it builds the environment)." }
& $py -m pip install -q --only-binary :all: pystac-client planetary-computer affine
if ($LASTEXITCODE -ne 0) { throw "package install failed" }

Step "v4_00_tests"     "$py -m pytest tests/ml -q" 2
Step "v4_01_eia_early" "$py -c ""from src.ml.eia import fetch_eia; fetch_eia('2018-01-01','2020-12-31')""" 3
Step "v4_02_check"     "$py -m src.ml.radar check" 2
Step "v4_03_download"  "$py -m src.ml.radar run"
Step "v4_04_evaluate"  "$py -m src.ml.evaluate_radar" 3
Step "v4_05_report"    "$py -m src.ml.report_v4" 3
Write-Host "Finished. Verdict: results\h3_radar_verdict.json" -ForegroundColor Green
Get-Content results\h3_radar_verdict.json
Write-Host "Then run: git add src results paper data/manifest.csv configs tests run_v4_auto.ps1 ; git status --short" -ForegroundColor Green
