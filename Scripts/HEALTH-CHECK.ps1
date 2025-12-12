#!/usr/bin/env pwsh
# =============================================================================
# Script de Verificación de Salud del Sistema
# =============================================================================
# Verifica que todos los servicios estén funcionando correctamente
# Ejecutar como: .\HEALTH-CHECK.ps1
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verificación de Salud del Sistema" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Verificar Docker
Write-Host "[1/7] Verificando Docker..." -ForegroundColor Yellow
try {
    docker --version > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker está instalado" -ForegroundColor Green
        
        docker ps > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Docker está corriendo" -ForegroundColor Green
        } else {
            Write-Host "✗ Docker no está corriendo" -ForegroundColor Red
            $allHealthy = $false
        }
    } else {
        Write-Host "✗ Docker no está instalado" -ForegroundColor Red
        $allHealthy = $false
    }
} catch {
    Write-Host "✗ Error al verificar Docker" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# 2. Verificar Contenedores Docker
Write-Host "[2/7] Verificando contenedores..." -ForegroundColor Yellow
$expectedContainers = @("distribuidora-api", "distribuidora-worker", "sqlserver", "rabbitmq")
foreach ($container in $expectedContainers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>$null
    if ($status) {
        Write-Host "✓ $container está corriendo" -ForegroundColor Green
    } else {
        Write-Host "✗ $container NO está corriendo" -ForegroundColor Red
        $allHealthy = $false
    }
}
Write-Host ""

# 3. Verificar SQL Server
Write-Host "[3/7] Verificando SQL Server..." -ForegroundColor Yellow
$health = docker inspect sqlserver --format='{{.State.Health.Status}}' 2>$null
if ($health -eq "healthy") {
    Write-Host "✓ SQL Server está saludable" -ForegroundColor Green
    
    # Verificar conexión a la base de datos
    $dbTest = docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q "SELECT DB_NAME()" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Conexión a base de datos funcional" -ForegroundColor Green
    } else {
        Write-Host "⚠ No se pudo conectar a la base de datos" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ SQL Server NO está saludable (estado: $health)" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# 4. Verificar RabbitMQ
Write-Host "[4/7] Verificando RabbitMQ..." -ForegroundColor Yellow
$health = docker inspect rabbitmq --format='{{.State.Health.Status}}' 2>$null
if ($health -eq "healthy") {
    Write-Host "✓ RabbitMQ está saludable" -ForegroundColor Green
    
    # Verificar admin UI
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:15672" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ RabbitMQ Admin UI accesible" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠ RabbitMQ Admin UI no responde" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ RabbitMQ NO está saludable (estado: $health)" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# 5. Verificar API Backend
Write-Host "[5/7] Verificando API Backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ API Backend accesible en http://localhost:8000" -ForegroundColor Green
        Write-Host "✓ Swagger UI disponible" -ForegroundColor Green
    } else {
        Write-Host "✗ API Backend no responde correctamente" -ForegroundColor Red
        $allHealthy = $false
    }
} catch {
    Write-Host "✗ No se puede conectar a la API Backend" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor DarkRed
    $allHealthy = $false
}
Write-Host ""

# 6. Verificar Node.js y npm (para Frontend)
Write-Host "[6/7] Verificando Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node.js instalado: $nodeVersion" -ForegroundColor Green
        
        $npmVersion = npm --version 2>$null
        Write-Host "✓ npm instalado: v$npmVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Node.js no está instalado" -ForegroundColor Red
        $allHealthy = $false
    }
} catch {
    Write-Host "✗ Error al verificar Node.js" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# 7. Verificar Frontend
Write-Host "[7/7] Verificando Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $scriptPath "distribuidora-animales-front"

if (Test-Path $frontendPath) {
    # Verificar que node_modules existe
    $nodeModulesPath = Join-Path $frontendPath "node_modules"
    if (Test-Path $nodeModulesPath) {
        Write-Host "✓ Dependencias de npm instaladas" -ForegroundColor Green
    } else {
        Write-Host "⚠ Dependencias de npm no instaladas" -ForegroundColor Yellow
        Write-Host "  Ejecuta: cd distribuidora-animales-front; .\INSTALL.ps1" -ForegroundColor DarkGray
    }
    
    # Verificar .env
    $envPath = Join-Path $frontendPath ".env"
    if (Test-Path $envPath) {
        Write-Host "✓ Archivo .env existe" -ForegroundColor Green
        
        # Verificar contenido
        $envContent = Get-Content $envPath -Raw
        if ($envContent -match "REACT_APP_API_URL") {
            Write-Host "✓ Variable REACT_APP_API_URL configurada" -ForegroundColor Green
        } else {
            Write-Host "⚠ Variable REACT_APP_API_URL no encontrada en .env" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ Archivo .env no existe" -ForegroundColor Yellow
        Write-Host "  Ejecuta: cd distribuidora-animales-front; .\INSTALL.ps1" -ForegroundColor DarkGray
    }
    
    # Verificar si está corriendo
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Frontend corriendo en http://localhost:3000" -ForegroundColor Green
        } else {
            Write-Host "⚠ Frontend no está corriendo" -ForegroundColor Yellow
            Write-Host "  Ejecuta: cd distribuidora-animales-front; npm start" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "⚠ Frontend no está corriendo" -ForegroundColor Yellow
        Write-Host "  Ejecuta: cd distribuidora-animales-front; npm start" -ForegroundColor DarkGray
    }
} else {
    Write-Host "✗ Carpeta del frontend no encontrada" -ForegroundColor Red
    $allHealthy = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Resumen de Estado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allHealthy) {
    Write-Host "✓ Todos los servicios críticos están funcionando correctamente" -ForegroundColor Green
} else {
    Write-Host "✗ Algunos servicios tienen problemas" -ForegroundColor Red
    Write-Host ""
    Write-Host "Acciones recomendadas:" -ForegroundColor Yellow
    Write-Host "1. Si el backend tiene problemas:" -ForegroundColor White
    Write-Host "   cd distribuidora-animales-back" -ForegroundColor DarkGray
    Write-Host "   .\INSTALL.ps1" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "2. Si el frontend tiene problemas:" -ForegroundColor White
    Write-Host "   cd distribuidora-animales-front" -ForegroundColor DarkGray
    Write-Host "   .\INSTALL.ps1" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "3. Ver logs de Docker:" -ForegroundColor White
    Write-Host "   docker-compose logs -f" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "URLs de Acceso:" -ForegroundColor Cyan
Write-Host "  • Frontend:          http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend API:       http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:          http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • RabbitMQ Admin:    http://localhost:15672" -ForegroundColor White
Write-Host ""
