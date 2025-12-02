#!/usr/bin/env pwsh
# =============================================================================
# Script de Instalación Automática - Distribuidora Perros y Gatos (Backend)
# =============================================================================
# Este script configura automáticamente el proyecto backend con Docker
# Ejecutar como: .\INSTALL.ps1
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalación Automática - Backend" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker está instalado y corriendo
Write-Host "[1/6] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está instalado"
    }
    Write-Host "✓ Docker encontrado: $dockerVersion" -ForegroundColor Green
    
    docker ps >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está corriendo"
    }
    Write-Host "✓ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    Write-Host "Por favor instala Docker Desktop y asegúrate de que esté corriendo." -ForegroundColor Red
    Write-Host "Descarga desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar docker-compose
Write-Host "[2/6] Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose no está disponible"
    }
    Write-Host "✓ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Detener contenedores existentes
Write-Host "[3/6] Limpiando contenedores antiguos..." -ForegroundColor Yellow
$existingContainers = docker ps -a --filter "name=distribuidora" --format "{{.Names}}" 2>$null
if ($existingContainers) {
    Write-Host "Deteniendo contenedores existentes..." -ForegroundColor Yellow
    docker-compose down 2>$null
    Write-Host "✓ Contenedores anteriores detenidos" -ForegroundColor Green
} else {
    Write-Host "✓ No hay contenedores previos" -ForegroundColor Green
}

Write-Host ""

# Construir imágenes de Docker
Write-Host "[4/6] Construyendo imágenes Docker..." -ForegroundColor Yellow
Write-Host "Esto puede tardar varios minutos la primera vez..." -ForegroundColor Cyan

docker-compose build --no-cache 2>&1 | ForEach-Object {
    if ($_ -match "Step \d+/\d+") {
        Write-Host $_ -ForegroundColor DarkGray
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al construir las imágenes" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Imágenes Docker construidas exitosamente" -ForegroundColor Green
Write-Host ""

# Iniciar servicios
Write-Host "[5/6] Iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al iniciar los servicios" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Servicios iniciados" -ForegroundColor Green
Write-Host ""

# Esperar a que SQL Server esté listo
Write-Host "[6/6] Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Write-Host "Esto puede tardar hasta 2 minutos..." -ForegroundColor Cyan

$maxAttempts = 40
$attempt = 0
$sqlReady = $false

while ($attempt -lt $maxAttempts -and -not $sqlReady) {
    $attempt++
    Write-Host "Intento $attempt/$maxAttempts - Verificando SQL Server..." -ForegroundColor DarkGray
    
    $health = docker inspect sqlserver --format='{{.State.Health.Status}}' 2>$null
    if ($health -eq "healthy") {
        $sqlReady = $true
        Write-Host "✓ SQL Server está listo" -ForegroundColor Green
    } else {
        Start-Sleep -Seconds 3
    }
}

if (-not $sqlReady) {
    Write-Host "⚠ SQL Server está tardando más de lo esperado" -ForegroundColor Yellow
    Write-Host "Puedes verificar el estado con: docker-compose logs sqlserver" -ForegroundColor Yellow
}

# Verificar RabbitMQ
$rabbitHealth = docker inspect rabbitmq --format='{{.State.Health.Status}}' 2>$null
if ($rabbitHealth -eq "healthy") {
    Write-Host "✓ RabbitMQ está listo" -ForegroundColor Green
} else {
    Write-Host "⚠ RabbitMQ aún se está inicializando" -ForegroundColor Yellow
}

Write-Host ""

# Aplicar migraciones de base de datos
Write-Host "Aplicando schema de base de datos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -i /dev/stdin < sql/schema.sql 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Schema de base de datos aplicado" -ForegroundColor Green
} else {
    Write-Host "⚠ Puede que necesites aplicar el schema manualmente" -ForegroundColor Yellow
    Write-Host "Ejecuta: docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C < sql/schema.sql" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor Cyan
Write-Host "  • API Backend:       http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:          http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • RabbitMQ Admin:    http://localhost:15672" -ForegroundColor White
Write-Host "    (user: guest, pass: guest)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Estado de contenedores:" -ForegroundColor Cyan
docker ps --filter "name=distribuidora" --filter "name=sqlserver" --filter "name=rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "  • Ver logs:          docker-compose logs -f" -ForegroundColor White
Write-Host "  • Detener:           docker-compose down" -ForegroundColor White
Write-Host "  • Reiniciar:         docker-compose restart" -ForegroundColor White
Write-Host "  • Estado:            docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "¡El backend está listo para usar! 🚀" -ForegroundColor Green
Write-Host ""
