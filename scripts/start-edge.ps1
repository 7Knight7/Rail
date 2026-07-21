# Start Microsoft Edge with CDP on port 9222 for RailMadad automation.
# Waits for backend (8000) and frontend (5173) before launching Edge.
param(
    [int]$Port = 9222,
    [string]$UserDataDir = "C:\EdgeDebug",
    [string]$EdgeExecutablePath = $env:EDGE_EXECUTABLE_PATH,
    [string]$RailMadadUrl = "https://railmadad.indianrail.gov.in",
    [string]$AppUrl = "http://127.0.0.1:5173",
    [string]$BackendHealthUrl = "http://127.0.0.1:8000/api/v1/health",
    [int]$ServiceTimeoutSeconds = 120,
    [switch]$SkipServiceChecks
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WaitScript = Join-Path $ScriptDir "wait-for-service.ps1"

function Resolve-EdgeExecutable {
    param([string]$ExplicitPath)

    if ($ExplicitPath -and (Test-Path $ExplicitPath)) {
        return $ExplicitPath
    }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    Write-Error "Microsoft Edge not found. Install Edge or set EDGE_EXECUTABLE_PATH."
}

function Test-HttpReady {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
    } catch {
        return $false
    }
}

function Close-StaleEdgeDebugProcesses {
    param([string]$ProfileDir)
    $escaped = [regex]::Escape($ProfileDir)
    Get-CimInstance Win32_Process -Filter "name='msedge.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match $escaped } |
        ForEach-Object {
            Write-Host "Closing stale Edge automation process PID $($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

Write-Host "=== RailMadad Edge automation startup ==="
Write-Host ""

if (-not $SkipServiceChecks) {
    Write-Host "Step 1/3: Checking backend..."
    if (-not (Test-HttpReady -Url $BackendHealthUrl)) {
        Write-Host "Backend not ready yet. Waiting up to ${ServiceTimeoutSeconds}s..."
        $backendReady = & $WaitScript -Url $BackendHealthUrl -Name "Backend API" -TimeoutSeconds $ServiceTimeoutSeconds
        if (-not $backendReady) {
            Write-Error @"
Backend API is unavailable at $BackendHealthUrl.

Start the backend first:
  cd backend
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Ensure PostgreSQL is running:
  docker compose up -d postgres redis
"@
        }
    } else {
        Write-Host "OK: Backend API is ready at $BackendHealthUrl"
    }

    Write-Host ""
    Write-Host "Step 2/3: Checking frontend..."
    if (-not (Test-HttpReady -Url $AppUrl)) {
        Write-Host "Frontend not ready yet. Waiting up to ${ServiceTimeoutSeconds}s..."
        $frontendReady = & $WaitScript -Url $AppUrl -Name "Frontend (Vite)" -TimeoutSeconds $ServiceTimeoutSeconds
        if (-not $frontendReady) {
            Write-Error @"
Frontend is unavailable at $AppUrl.

Start the frontend first:
  npm run dev

Vite is configured with strictPort on 5173 — it will not silently switch to another port.
"@
        }
    } else {
        Write-Host "OK: Frontend is ready at $AppUrl"
    }
} else {
    Write-Host "Skipping backend/frontend checks (SkipServiceChecks)."
}

Write-Host ""
Write-Host "Step 3/3: Starting Microsoft Edge with CDP..."

$edge = Resolve-EdgeExecutable -ExplicitPath $EdgeExecutablePath
Write-Host "Using Edge executable: $edge"

if (-not (Test-Path $UserDataDir)) {
    Write-Host "Creating Edge user data directory: $UserDataDir"
    New-Item -ItemType Directory -Path $UserDataDir -Force | Out-Null
}

$cdpVersionUrl = "http://127.0.0.1:$Port/json/version"
$cdpListUrl = "http://127.0.0.1:$Port/json/list"

if (Test-HttpReady -Url $cdpVersionUrl) {
    Write-Host "OK: Edge CDP is already ready on port $Port."
    try {
        $probe = Invoke-WebRequest -Uri $cdpVersionUrl -UseBasicParsing -TimeoutSec 3
        Write-Host $probe.Content
        $listResp = Invoke-WebRequest -Uri $cdpListUrl -UseBasicParsing -TimeoutSec 3
        $tabs = $listResp.Content | ConvertFrom-Json
        Write-Host "Open tabs: $($tabs.Count)"
    } catch {
        Write-Host "CDP is ready but could not fetch tab list."
    }
    Write-Host ""
    Write-Host "Next: log in to RailMadad in this Edge window, then click Generate in the app at $AppUrl"
    exit 0
}

Close-StaleEdgeDebugProcesses -ProfileDir $UserDataDir
Start-Sleep -Seconds 2

Write-Host "Launching Edge (user-data-dir: $UserDataDir, CDP port: $Port)..."
Start-Process -FilePath $edge -ArgumentList @(
    "--remote-debugging-port=$Port",
    "--remote-debugging-address=127.0.0.1",
    "--user-data-dir=$UserDataDir",
    $RailMadadUrl,
    $AppUrl
)

Write-Host "Waiting for CDP at $cdpVersionUrl ..."
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-HttpReady -Url $cdpVersionUrl) {
        try {
            $resp = Invoke-WebRequest -Uri $cdpVersionUrl -UseBasicParsing -TimeoutSec 3
            Write-Host "OK: Edge CDP is ready."
            Write-Host $resp.Content
            $listResp = Invoke-WebRequest -Uri $cdpListUrl -UseBasicParsing -TimeoutSec 3
            $tabs = $listResp.Content | ConvertFrom-Json
            Write-Host ""
            Write-Host "Open tabs: $($tabs.Count)"
        } catch {
            Write-Host "OK: Edge CDP is ready (could not fetch tab list)."
        }
        Write-Host ""
        Write-Host "Service summary:"
        Write-Host "  Backend:  $BackendHealthUrl"
        Write-Host "  Frontend: $AppUrl"
        Write-Host "  CDP:      $cdpVersionUrl"
        Write-Host ""
        Write-Host "Next: log in to RailMadad in this Edge window, then click Generate in the app."
        exit 0
    }
}

Write-Error @"
Edge started but CDP is not reachable on port $Port.

Close the Edge debug window and run this script again:
  .\scripts\start-edge.ps1
"@
