# Script para orquestar Podman y ejecutar pruebas del BACKEND

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ciclo Podman + Pytest (BACKEND)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variables de control
$ErrorActionPreference = "Continue"
$testsPassed = $false
$podmanReady = $false

# Variables de entorno para pruebas
if (-not $env:ADMIN_EMAIL) { $env:ADMIN_EMAIL = "admin@gmail.com" }
if (-not $env:ADMIN_PASS) { $env:ADMIN_PASS = "Admin123!@#" }
if (-not $env:BACKEND_BASE_URL) { $env:BACKEND_BASE_URL = "http://localhost:8000" }
if (-not $env:BACKEND_LOG_FILE) { $env:BACKEND_LOG_FILE = (Join-Path (Join-Path $PWD "logs") "backend\app.log") }
if (-not $env:BACKEND_WAIT_SECONDS) { $env:BACKEND_WAIT_SECONDS = "60" }

function Wait-For-Health {
    param(
        [string] $Url,
        [int] $TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Method GET -Uri $Url -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { return $true }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

# Podman lifecycle
try {
    Write-Host "  Podman: down --volumes" -ForegroundColor Yellow
    podman compose down --volumes | Out-Null

    Write-Host "  Podman: build" -ForegroundColor Yellow
    podman compose build | Out-Null

    Write-Host "  Podman: up -d" -ForegroundColor Yellow
    podman compose up -d | Out-Null

    Write-Host "  Esperando health del backend..." -ForegroundColor Yellow
    $healthOk = Wait-For-Health -Url "$env:BACKEND_BASE_URL/health" -TimeoutSeconds [int]$env:BACKEND_WAIT_SECONDS
    if (-not $healthOk) { throw "Backend no saludable tras el arranque" }

    # Reinicio para generar logs de idempotencia antes de correr pytest
    Write-Host "  Podman: restart" -ForegroundColor Yellow
    podman compose restart | Out-Null

    Write-Host "  Verificando health tras restart..." -ForegroundColor Yellow
    $healthOk2 = Wait-For-Health -Url "$env:BACKEND_BASE_URL/health" -TimeoutSeconds [int]$env:BACKEND_WAIT_SECONDS
    if (-not $healthOk2) { throw "Backend no saludable tras el restart" }

    $podmanReady = $true
} catch {
    Write-Host "  ERROR en ciclo Podman: $_" -ForegroundColor Red
}

# Verificar si existe el entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "  Activando entorno virtual..." -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
    
    Write-Host "  Instalando/verificando dependencias de pruebas..." -ForegroundColor Green
    pip install pytest pytest-asyncio pytest-cov httpx aiosqlite requests --quiet
    
    Write-Host ""
    Write-Host "  Ejecutando pytest..." -ForegroundColor Cyan
    Write-Host ""
    
    # Ejecutar pytest en backend\tests
    Push-Location backend\tests
    
    try {
        if ($podmanReady) {
            pytest -v --tb=short
        } else {
            Write-Host "  Saltando pruebas: Podman no listo" -ForegroundColor Red
            $exitCode = 1
        }
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    
    Write-Host ""
    
    if ($exitCode -eq 0) {
        $testsPassed = $true
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  TODAS LAS PRUEBAS PASARON" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  ALGUNAS PRUEBAS FALLARON" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
    }
    
    # Desactivar entorno virtual
    deactivate
} else {
    Write-Host "  ERROR: No se encontro entorno virtual." -ForegroundColor Red
    Write-Host "  Ejecute: python -m venv venv" -ForegroundColor Yellow
    Write-Host "  Luego: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  Y: pip install -r backend\api\requirements.txt" -ForegroundColor Yellow
}

Write-Host ""

if ($testsPassed) {
    exit 0
} else {
    exit 1
}
