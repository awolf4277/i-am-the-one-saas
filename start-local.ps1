$ErrorActionPreference = "Stop"

$root        = "X:\i-am-the-one-saas"
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$runtimeDir  = Join-Path $root ".runtime"

$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"

$backendUrl  = "http://127.0.0.1:5000"
$frontendUrl = "http://127.0.0.1:5175"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $runtimeDir |
    Out-Null

$backendOut = Join-Path $runtimeDir "backend-local.log"
$backendErr = Join-Path $runtimeDir "backend-local-error.log"
$frontendOut = Join-Path $runtimeDir "frontend-local.log"
$frontendErr = Join-Path $runtimeDir "frontend-local-error.log"

Remove-Item `
    $backendOut,
    $backendErr,
    $frontendOut,
    $frontendErr `
    -Force `
    -ErrorAction SilentlyContinue


function Stop-LocalPort {
    param(
        [int]$Port
    )

    $connections = Get-NetTCPConnection `
        -LocalPort $Port `
        -ErrorAction SilentlyContinue

    $processIds = $connections |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object {
            $_ -and $_ -ne 0
        }

    foreach ($processId in $processIds) {

        Write-Host `
            "Stopping stale PID $processId on port $Port" `
            -ForegroundColor Yellow

        Stop-Process `
            -Id $processId `
            -Force `
            -ErrorAction SilentlyContinue
    }
}


function Show-LogTail {
    param(
        [string]$Path,
        [string]$Title
    )

    if (Test-Path $Path) {

        Write-Host ""
        Write-Host "=== $Title ===" -ForegroundColor Yellow

        Get-Content `
            $Path `
            -Tail 40 `
            -ErrorAction SilentlyContinue
    }
}


function Fail-Wolf {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "WOLF OS STARTUP FAILED" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red

    Show-LogTail $backendErr "BACKEND ERROR LOG"
    Show-LogTail $backendOut "BACKEND LOG"
    Show-LogTail $frontendErr "FRONTEND ERROR LOG"
    Show-LogTail $frontendOut "FRONTEND LOG"

    throw $Message
}


Clear-Host

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " I AM THE ONE / WOLF OS" -ForegroundColor Green
Write-Host " LOCAL IGNITION SEQUENCE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""


# ------------------------------------------------------------
# PREFLIGHT
# ------------------------------------------------------------

Write-Host "[1/7] PREFLIGHT" -ForegroundColor Cyan

if (-not (Test-Path $backendPython)) {
    Fail-Wolf "Backend Python venv was not found: $backendPython"
}

if (-not (Test-Path (Join-Path $backendDir "wsgi.py"))) {
    Fail-Wolf "backend\wsgi.py was not found."
}

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    Fail-Wolf "frontend\package.json was not found."
}

try {
    $npmPath = (Get-Command npm.cmd -ErrorAction Stop).Source
}
catch {
    Fail-Wolf "npm.cmd was not found in PATH."
}

Write-Host "Python: PASS" -ForegroundColor Green
Write-Host "Backend: PASS" -ForegroundColor Green
Write-Host "Frontend: PASS" -ForegroundColor Green
Write-Host "Node/npm: PASS" -ForegroundColor Green


# ------------------------------------------------------------
# STOP STALE LOCAL SERVERS
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/7] CLEARING PORTS" -ForegroundColor Cyan

Stop-LocalPort 5000
Stop-LocalPort 5175

Start-Sleep -Seconds 1

Write-Host "Ports 5000 and 5175 ready." -ForegroundColor Green


# ------------------------------------------------------------
# LOCAL-ONLY CONFIG
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/7] LOCAL CONFIGURATION" -ForegroundColor Cyan

$env:CORS_ORIGINS = @(
    "http://127.0.0.1:5175",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://localhost:5173"
) -join ","

# LOCAL DEVELOPMENT ONLY.
# This does not change production configuration.
$env:WOLF_ALLOW_INSECURE_LOCAL_AUTH = "1"

Set-Content `
    -Path (Join-Path $frontendDir ".env.local") `
    -Value "VITE_BACKEND_URL=http://127.0.0.1:5000" `
    -Encoding UTF8

Write-Host "API URL: $backendUrl" -ForegroundColor Green
Write-Host "Local auth mode enabled." -ForegroundColor Green


# ------------------------------------------------------------
# BACKEND
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/7] STARTING BACKEND" -ForegroundColor Cyan

try {

    $backendProcess = Start-Process `
        -FilePath $backendPython `
        -ArgumentList @(
            "-m",
            "flask",
            "--app",
            "wsgi:app",
            "run",
            "--host",
            "127.0.0.1",
            "--port",
            "5000"
        ) `
        -WorkingDirectory $backendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr `
        -PassThru

}
catch {
    Fail-Wolf "Could not launch backend: $($_.Exception.Message)"
}


$health = $null

for ($attempt = 1; $attempt -le 15; $attempt++) {

    try {

        $health = Invoke-RestMethod `
            -Uri "$backendUrl/api/health" `
            -Method GET `
            -TimeoutSec 3

        break

    }
    catch {

        if ($backendProcess.HasExited) {
            Fail-Wolf "Backend process exited during startup."
        }

        Start-Sleep -Seconds 1
    }
}


if (-not $health) {
    Fail-Wolf "Backend never became healthy on port 5000."
}

Write-Host "BACKEND HEALTH: PASS" -ForegroundColor Green


# ------------------------------------------------------------
# OWNER AUTH
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/7] OWNER AUTH CHECK" -ForegroundColor Cyan

$localOwnerPassword = if ($env:WOLF_LOCAL_OWNER_PASSWORD) {
    $env:WOLF_LOCAL_OWNER_PASSWORD
}
else {
    "WOLF-DEMO"
}

try {

    $ownerLogin = Invoke-RestMethod `
        -Method POST `
        -Uri "$backendUrl/api/owner/login" `
        -ContentType "application/json" `
        -Body (@{
            password = $localOwnerPassword
        } | ConvertTo-Json) `
        -TimeoutSec 10

    Write-Host "OWNER LOGIN: PASS" -ForegroundColor Green

}
catch {

    Write-Host ""
    Write-Host "OWNER LOGIN: FAIL" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
    }
    else {
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }

    Stop-Process `
        -Id $backendProcess.Id `
        -Force `
        -ErrorAction SilentlyContinue

    Fail-Wolf "Backend is healthy, but owner authentication failed."
}


# ------------------------------------------------------------
# FRONTEND
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/7] STARTING FRONTEND" -ForegroundColor Cyan

try {

    $frontendProcess = Start-Process `
        -FilePath $npmPath `
        -ArgumentList @(
            "run",
            "dev"
        ) `
        -WorkingDirectory $frontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr `
        -PassThru

}
catch {

    Stop-Process `
        -Id $backendProcess.Id `
        -Force `
        -ErrorAction SilentlyContinue

    Fail-Wolf "Could not launch frontend: $($_.Exception.Message)"
}


$frontendReady = $false

for ($attempt = 1; $attempt -le 15; $attempt++) {

    try {

        $response = Invoke-WebRequest `
            -Uri "$frontendUrl/" `
            -UseBasicParsing `
            -TimeoutSec 3

        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            $frontendReady = $true
            break
        }

    }
    catch {

        if ($frontendProcess.HasExited) {

            Stop-Process `
                -Id $backendProcess.Id `
                -Force `
                -ErrorAction SilentlyContinue

            Fail-Wolf "Frontend process exited during startup."
        }

        Start-Sleep -Seconds 1
    }
}


if (-not $frontendReady) {

    Stop-Process `
        -Id $frontendProcess.Id `
        -Force `
        -ErrorAction SilentlyContinue

    Stop-Process `
        -Id $backendProcess.Id `
        -Force `
        -ErrorAction SilentlyContinue

    Fail-Wolf "Frontend never became available on port 5175."
}


# ------------------------------------------------------------
# FINAL PORT VERIFICATION
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/7] FINAL SYSTEM CHECK" -ForegroundColor Cyan

$backendListening = Get-NetTCPConnection `
    -LocalPort 5000 `
    -State Listen `
    -ErrorAction SilentlyContinue

$frontendListening = Get-NetTCPConnection `
    -LocalPort 5175 `
    -State Listen `
    -ErrorAction SilentlyContinue


if (-not $backendListening) {
    Fail-Wolf "Port 5000 is not listening."
}

if (-not $frontendListening) {
    Fail-Wolf "Port 5175 is not listening."
}


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " WOLF OS -- ENGINE ONLINE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend Health : PASS" -ForegroundColor Green
Write-Host "Owner Auth     : PASS" -ForegroundColor Green
Write-Host "Backend : $backendUrl" -ForegroundColor Cyan
Write-Host "Frontend: $frontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend PID : $($backendProcess.Id)" -ForegroundColor DarkGray
Write-Host "Frontend PID: $($frontendProcess.Id)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "ONE WINDOW STARTUP: PASS" -ForegroundColor Green
Write-Host ""

Start-Process $frontendUrl
