# Script para ejecutar pruebas del BACKEND

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ejecutando Pruebas del BACKEND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variables de control
$ErrorActionPreference = "Continue"
$testsPassed = $false

# Verificar si existe el entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "  Activando entorno virtual..." -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
    
    Write-Host "  Instalando/verificando dependencias de pruebas..." -ForegroundColor Green
    pip install pytest pytest-asyncio pytest-cov httpx aiosqlite --quiet
    
    Write-Host ""
    Write-Host "  Ejecutando pytest..." -ForegroundColor Cyan
    Write-Host ""
    
    # Cambiar al directorio donde está el .env antes de ejecutar pytest
    Push-Location backend\api
    
    try {
        pytest -v --tb=short
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
