# setup.ps1 - instalador Windows 11 (ESPEC 6)
param([switch]$SkipPython)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not $SkipPython) {
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
    winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
    winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
}

# venv principal
$venv = Join-Path $Root "venv"
if (-not (Test-Path $venv)) { python -m venv $venv }
& (Join-Path $venv "Scripts\pip.exe") install --upgrade pip
& (Join-Path $venv "Scripts\pip.exe") install -r (Join-Path $Root "requirements.txt")

# env
$envFile = Join-Path $Root ".env"
@"
HF_HOME=$Root\modelos\hf
HF_HUB_DISABLE_SYMLINKS_WARNING=1
VRAM_BUDGET_GB=7.2
"@ | Set-Content -Path $envFile -Encoding UTF8

Write-Host "Setup concluido. Execute iniciar.bat"
