param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Write-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details
    )

    if ($Passed) {
        Write-Host "[PASS] $Name - $Details" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $Name - $Details" -ForegroundColor Red
    }
}

$failures = 0

# 1) API health
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10
    $ok = ($health.status -eq "ok")
    Write-Check -Name "API health endpoint" -Passed $ok -Details "GET /health returned status='$($health.status)'"
    if (-not $ok) { $failures++ }
} catch {
    Write-Check -Name "API health endpoint" -Passed $false -Details $_.Exception.Message
    $failures++
}

# 2) Swagger docs
try {
    $docs = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method GET -TimeoutSec 10
    $ok = ($docs.StatusCode -eq 200)
    Write-Check -Name "Swagger docs endpoint" -Passed $ok -Details "GET /docs returned HTTP $($docs.StatusCode)"
    if (-not $ok) { $failures++ }
} catch {
    Write-Check -Name "Swagger docs endpoint" -Passed $false -Details $_.Exception.Message
    $failures++
}

# 3) Docker services
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        $composeOut = docker compose ps 2>&1 | Out-String
        $postgresOk = ($composeOut -match "(?im)postgres.*Up")
        $qdrantOk = ($composeOut -match "(?im)qdrant.*Up")
        Write-Check -Name "Docker postgres service" -Passed $postgresOk -Details "docker compose ps contains postgres Up state"
        if (-not $postgresOk) { $failures++ }
        Write-Check -Name "Docker qdrant service" -Passed $qdrantOk -Details "docker compose ps contains qdrant Up state"
        if (-not $qdrantOk) { $failures++ }
    } catch {
        Write-Check -Name "Docker services" -Passed $false -Details $_.Exception.Message
        $failures++
    }
} else {
    Write-Check -Name "Docker command availability" -Passed $false -Details "docker command not found in PATH"
    $failures++
}

# 4) Functional check: triage creates case_id, recent contains case_id
$sampleId = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$sampleTitle = "health-check-$sampleId"
$createdCaseId = $null

try {
    $triageBody = @{
        source = "manual"
        title = $sampleTitle
        description = "Synthetic health-check incident."
        logs = @("TimeoutError redis", "retry budget exhausted")
        metadata = @{
            service = "health-check"
            environment = "local"
        }
    } | ConvertTo-Json -Depth 6

    $triageResult = Invoke-RestMethod -Uri "$BaseUrl/v1/incidents/triage" -Method POST -TimeoutSec 20 -ContentType "application/json" -Body $triageBody
    $createdCaseId = $triageResult.case_id
    $ok = -not [string]::IsNullOrWhiteSpace($createdCaseId)
    Write-Check -Name "Triage endpoint persistence" -Passed $ok -Details "POST /v1/incidents/triage returned case_id='$createdCaseId'"
    if (-not $ok) { $failures++ }
} catch {
    Write-Check -Name "Triage endpoint persistence" -Passed $false -Details $_.Exception.Message
    $failures++
}

try {
    $recent = Invoke-RestMethod -Uri "$BaseUrl/v1/incidents/recent?limit=20" -Method GET -TimeoutSec 10
    $found = $false
    foreach ($row in $recent) {
        if ($row.case_id -eq $createdCaseId) {
            $found = $true
            break
        }
    }
    Write-Check -Name "Recent incidents readback" -Passed $found -Details "GET /v1/incidents/recent contains new case_id"
    if (-not $found) { $failures++ }
} catch {
    Write-Check -Name "Recent incidents readback" -Passed $false -Details $_.Exception.Message
    $failures++
}

Write-Host ""
if ($failures -eq 0) {
    Write-Host "Overall result: HEALTH CHECK PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Overall result: HEALTH CHECK FAILED ($failures checks failed)" -ForegroundColor Red
    exit 1
}
