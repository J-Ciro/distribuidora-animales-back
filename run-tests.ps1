# Script para ejecutar todas las pruebas del proyecto

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Ejecutando Pruebas del Proyecto" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Variables de control
$ErrorActionPreference = "Continue"
$backendPassed = $false
$frontendPassed = $false

# ==========================================
# PRUEBAS BACKEND
# ==========================================

Write-Host "[1/2] Ejecutando pruebas del BACKEND..." -ForegroundColor Yellow
Write-Host ""

# Ya estamos en el directorio del backend

# Verificar si existe el entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "  Activando entorno virtual..." -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
    
    Write-Host "  Instalando/verificando dependencias de pruebas..." -ForegroundColor Green
    pip install pytest pytest-asyncio pytest-cov httpx --quiet
    
    Write-Host ""
    Write-Host "  → Ejecutando pytest..." -ForegroundColor Cyan
    Write-Host ""
    
    # Cambiar al directorio donde está el .env antes de ejecutar pytest
    Push-Location backend\api
    
    try {
        pytest -v --tb=short
        $backendExitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    
    if ($backendExitCode -eq 0) {
        $backendPassed = $true
        Write-Host ""
        Write-Host "  Pruebas del BACKEND: EXITOSAS" -ForegroundColor Green
        Write-Host "  Reporte de cobertura: Distribuidora_Perros_Gatos_back\htmlcov\index.html" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "  Pruebas del BACKEND: FALLARON" -ForegroundColor Red
    }
    
    # Desactivar entorno virtual
    deactivate
} else {
    Write-Host "  No se encontro entorno virtual. Ejecute setup.ps1 primero." -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""

# ==========================================
# PRUEBAS FRONTEND
# ==========================================

Write-Host "[2/2] Ejecutando pruebas del FRONTEND..." -ForegroundColor Yellow
Write-Host ""

# Volver al directorio padre para ir al frontend
Set-Location ".."
Set-Location "Distribuidora_Perros_Gatos_front"

# Verificar si existe node_modules
if (Test-Path "node_modules") {
    Write-Host "  Instalando/verificando dependencias de pruebas..." -ForegroundColor Green
    npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event redux-mock-store --silent
    
    Write-Host ""
    Write-Host "  → Ejecutando Jest..." -ForegroundColor Cyan
    Write-Host ""
    
    # Ejecutar tests con cobertura (sin watch mode)
    npm test -- --coverage --watchAll=false --verbose
    
    if ($LASTEXITCODE -eq 0) {
        $frontendPassed = $true
        Write-Host ""
        Write-Host "  Pruebas del FRONTEND: EXITOSAS" -ForegroundColor Green
        Write-Host "  Reporte de cobertura: Distribuidora_Perros_Gatos_front\coverage\lcov-report\index.html" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "  Pruebas del FRONTEND: FALLARON" -ForegroundColor Red
    }
} else {
    Write-Host "  No se encontro node_modules. Ejecute 'npm install' primero." -ForegroundColor Yellow
}

# Volver al directorio del backend
Set-Location ".."
Set-Location "Distribuidora_Perros_Gatos_back"

Write-Host ""
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "       RESUMEN DE PRUEBAS" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

if ($backendPassed) {
    Write-Host "  Backend:  TODAS LAS PRUEBAS PASARON" -ForegroundColor Green
} else {
    Write-Host "  Backend:  ALGUNAS PRUEBAS FALLARON" -ForegroundColor Red
}

if ($frontendPassed) {
    Write-Host "  Frontend: TODAS LAS PRUEBAS PASARON" -ForegroundColor Green
} else {
    Write-Host "  Frontend: ALGUNAS PRUEBAS FALLARON" -ForegroundColor Red
}

Write-Host ""

if ($backendPassed -and $frontendPassed) {
    Write-Host "TODAS LAS PRUEBAS EXITOSAS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Reportes de cobertura generados:" -ForegroundColor Cyan
    Write-Host "  - Backend:  Distribuidora_Perros_Gatos_back\htmlcov\index.html" -ForegroundColor White
    Write-Host "  - Frontend: Distribuidora_Perros_Gatos_front\coverage\lcov-report\index.html" -ForegroundColor White
    exit 0
} else {
    Write-Host "Algunas pruebas fallaron. Revise los logs arriba." -ForegroundColor Yellow
    exit 1
}
