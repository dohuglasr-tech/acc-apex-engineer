# =============================================================================
# ACC Apex Engineer Pro - Empaquetador del Ejecutable Único (.exe)
# Usa siempre el entorno virtual local (.venv) siguiendo las buenas prácticas
# =============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==> [1/4] Verificando entorno virtual Python (.venv)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

Write-Host "==> [2/4] Instalando dependencias en .venv..." -ForegroundColor Cyan
& ".venv\Scripts\pip.exe" install --upgrade pip
& ".venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "==> [3/4] Compilando ACC_Apex_Engineer.exe con PyInstaller..." -ForegroundColor Cyan
& ".venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --onefile `
    --windowed `
    --name "ACC_Apex_Engineer" `
    main.py

Write-Host "==> [4/4] Copiando ejecutable a apps/web/public/downloads para descarga desde la Web..." -ForegroundColor Cyan
$WebDownloadsDir = Join-Path $ScriptDir "..\web\public\downloads"
if (-not (Test-Path $WebDownloadsDir)) {
    New-Item -ItemType Directory -Force -Path $WebDownloadsDir | Out-Null
}
Copy-Item -Force "dist\ACC_Apex_Engineer.exe" (Join-Path $WebDownloadsDir "ACC_Apex_Engineer.exe")

Write-Host "✅ Compilación completada: dist\ACC_Apex_Engineer.exe" -ForegroundColor Green
