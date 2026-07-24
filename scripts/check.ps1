$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repositoryRoot "backend"
$frontendPath = Join-Path $repositoryRoot "frontend"
$pythonPath = Join-Path $backendPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "backend/.venv does not exist. Follow the README setup steps first."
}

Push-Location $backendPath
try {
    & $pythonPath -m compileall -q app tests
    & $pythonPath -m pytest -q
}
finally {
    Pop-Location
}

Push-Location $frontendPath
try {
    npm run type-check
    npm run build
}
finally {
    Pop-Location
}

Write-Host "All repository checks passed."
