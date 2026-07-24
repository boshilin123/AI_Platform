$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repositoryRoot "backend"
$frontendPath = Join-Path $repositoryRoot "frontend"
$pythonPath = Join-Path $backendPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    python -m venv (Join-Path $backendPath ".venv")
    & $pythonPath -m pip install -e "${backendPath}[dev]"
}

Write-Host "Starting API on http://localhost:8080"
$apiProcess = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8080" `
    -WorkingDirectory $backendPath `
    -WindowStyle Hidden `
    -PassThru

try {
    Push-Location $frontendPath
    if (-not (Test-Path -LiteralPath (Join-Path $frontendPath "node_modules"))) {
        npm install
    }
    Write-Host "Starting web console on http://localhost:5173"
    npm run dev
}
finally {
    Pop-Location
    if (-not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id
    }
}
