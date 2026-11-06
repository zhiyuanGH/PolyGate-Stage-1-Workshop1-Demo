param(
    [int]$Port = 8000,
    [string]$Python = "python",
    [switch]$SetupOnly
)
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    $venvPython = Join-Path $PSScriptRoot ".venv/Scripts/python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $Python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
        if ($LASTEXITCODE -ne 0) { throw "Install Python 3.11 or newer first." }
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
    }
    $dependencyHash = ((Get-FileHash requirements.txt, requirements-dev.txt, constraints.txt).Hash -join "|")
    $stampPath = Join-Path $PSScriptRoot ".dependencies.sha256"
    $previousHash = if (Test-Path -LiteralPath $stampPath) { (Get-Content -LiteralPath $stampPath -Raw).Trim() } else { "" }
    if ($dependencyHash -ne $previousHash) {
        & $venvPython -m pip --disable-pip-version-check install -r requirements-dev.txt
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Check the internet connection and retry." }
        Set-Content -LiteralPath $stampPath -Value $dependencyHash -Encoding ascii
    }
    if ($SetupOnly) { Write-Host "Setup complete." }
    else {
        Write-Host "Open http://127.0.0.1:$Port/docs . Stop with Ctrl+C."
        & $venvPython -m booking_demo --port $Port
        if ($LASTEXITCODE -ne 0) { throw "The API service stopped with an error." }
    }
}
finally { Pop-Location }
