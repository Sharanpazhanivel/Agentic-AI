param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

function Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Die {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

Step "Preparing environment file"
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Warn ".env created from .env.example. Update secrets if needed."
    } else {
        Die "Missing .env and .env.example."
    }
}

Step "Ensuring Docker is available"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Die "Docker command not found. Install Docker Desktop and retry."
}

Step "Starting Docker services"
docker compose up -d | Out-Null

Step "Installing Python dependencies"
if (-not $SkipInstall) {
    python -m pip install -e . | Out-Null
} else {
    Warn "Skipping dependency install because -SkipInstall was provided."
}

Step "Stopping existing local API process on port 8000 (if any)"
try {
    $line = netstat -ano | Select-String ":8000" | Select-Object -First 1
    if ($line) {
        $pid = ($line.ToString() -split "\s+")[-1]
        if ($pid -match "^\d+$") {
            Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
    Warn "Could not inspect/stop existing process on port 8000."
}

Step "Starting API server in background"
$pythonExe = (Get-Command python).Source
$args = @("-m", "uvicorn", "app.main:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8000")
Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory (Get-Location) | Out-Null

Start-Sleep -Seconds 3

Step "Running health check"
& ".\health-check.ps1" -BaseUrl $BaseUrl
if ($LASTEXITCODE -ne 0) {
    Die "Startup completed, but health checks failed."
}

Write-Host ""
Write-Host "All systems are up." -ForegroundColor Green
Write-Host "API docs: $BaseUrl/docs" -ForegroundColor Green
