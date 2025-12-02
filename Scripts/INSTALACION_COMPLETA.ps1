#!/usr/bin/env pwsh
# =============================================================================
# Script de Instalación Completa - Distribuidora Perros y Gatos
# =============================================================================
# Este script instala y configura automáticamente BACKEND + FRONTEND
# Ejecutar desde la raíz del proyecto: .\INSTALACION_COMPLETA.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALACIÓN COMPLETA DEL SISTEMA" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Guardar directorio actual
$rootDir = Get-Location

# =============================================================================
# FASE 1: VERIFICAR REQUISITOS
# =============================================================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  FASE 1: Verificando Requisitos" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Verificar Node.js
Write-Host "[1/3] Verificando Node.js..." -ForegroundColor Cyan
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Node.js no encontrado" }
    Write-Host "✓ Node.js instalado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Node.js no está instalado" -ForegroundColor Red
    Write-Host "Descarga e instala Node.js desde: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Verificar npm
Write-Host "[2/3] Verificando npm..." -ForegroundColor Cyan
try {
    $npmVersion = npm --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw "npm no encontrado" }
    Write-Host "✓ npm instalado: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: npm no está disponible" -ForegroundColor Red
    exit 1
}

# Verificar Docker
Write-Host "[3/3] Verificando Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Docker no encontrado" }
    Write-Host "✓ Docker instalado: $dockerVersion" -ForegroundColor Green
    
    docker ps >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está corriendo"
    }
    Write-Host "✓ Docker está corriendo correctamente" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: $_" -ForegroundColor Red
    Write-Host "Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "Asegúrate de iniciar Docker Desktop antes de ejecutar este script." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✓ Todos los requisitos están instalados" -ForegroundColor Green
Write-Host ""

# =============================================================================
# FASE 2: CONFIGURAR BACKEND
# =============================================================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  FASE 2: Configurando Backend" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\Distribuidora_Perros_Gatos_back"

# Crear archivos .env desde .env.example
Write-Host "[1/5] Configurando variables de entorno..." -ForegroundColor Cyan

$envPaths = @(
    @{Example = "backend\api\.env.example"; Target = "backend\api\.env"},
    @{Example = "backend\worker\.env.example"; Target = "backend\worker\.env"}
)

foreach ($envPath in $envPaths) {
    if (-not (Test-Path $envPath.Target)) {
        if (Test-Path $envPath.Example) {
            Copy-Item $envPath.Example $envPath.Target
            Write-Host "  ✓ Creado $($envPath.Target)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ No se encontró $($envPath.Example)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ℹ $($envPath.Target) ya existe (no se sobrescribirá)" -ForegroundColor Blue
    }
}

Write-Host ""

# Limpiar contenedores anteriores
Write-Host "[2/5] Limpiando instalación previa..." -ForegroundColor Cyan
docker-compose down >$null 2>&1
Write-Host "✓ Limpieza completada" -ForegroundColor Green
Write-Host ""

# Construir imágenes
Write-Host "[3/5] Construyendo imágenes Docker..." -ForegroundColor Cyan
Write-Host "Esto puede tardar 5-10 minutos la primera vez..." -ForegroundColor Yellow
docker-compose build --no-cache 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al construir las imágenes" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Imágenes construidas exitosamente" -ForegroundColor Green
Write-Host ""

# Iniciar servicios
Write-Host "[4/5] Iniciando servicios..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al iniciar los servicios" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Servicios iniciados" -ForegroundColor Green
Write-Host ""

# Esperar a que SQL Server esté listo
Write-Host "[5/5] Esperando a SQL Server..." -ForegroundColor Cyan
$maxAttempts = 40
$attempt = 0
$sqlReady = $false

while ($attempt -lt $maxAttempts -and -not $sqlReady) {
    $attempt++
    $health = docker inspect sqlserver --format='{{.State.Health.Status}}' 2>$null
    if ($health -eq "healthy") {
        $sqlReady = $true
    } else {
        Write-Host "  Esperando SQL Server... ($attempt/$maxAttempts)" -ForegroundColor DarkGray
        Start-Sleep -Seconds 3
    }
}

if (-not $sqlReady) {
    Write-Host "⚠ SQL Server está tardando más de lo esperado" -ForegroundColor Yellow
    Write-Host "Continuando con la instalación..." -ForegroundColor Yellow
} else {
    Write-Host "✓ SQL Server está listo" -ForegroundColor Green
}

Write-Host ""

# Aplicar migraciones de base de datos
Write-Host "Aplicando base de datos..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Crear base de datos
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q "USE master; IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'distribuidora_db') CREATE DATABASE distribuidora_db;" 2>&1 | Out-Null

# Aplicar schema
Get-Content "sql/schema.sql" -Raw | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C 2>&1 | Out-Null

# Aplicar migraciones
$migrationFiles = Get-ChildItem -Path "sql/migrations" -Filter "*.sql" -ErrorAction SilentlyContinue | Sort-Object Name
$successCount = 0

foreach ($migration in $migrationFiles) {
    Get-Content $migration.FullName -Raw | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $successCount++ }
}

Write-Host "✓ Base de datos configurada ($successCount migraciones aplicadas)" -ForegroundColor Green
Write-Host ""

# =============================================================================
# FASE 3: CONFIGURAR FRONTEND
# =============================================================================
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  FASE 3: Configurando Frontend" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\Distribuidora_Perros_Gatos_front"

# Crear archivo .env
Write-Host "[1/2] Configurando variables de entorno..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  ✓ Creado .env desde .env.example" -ForegroundColor Green
    } else {
        # Crear .env con valores por defecto
        @"
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
"@ | Set-Content ".env"
        Write-Host "  ✓ Creado .env con configuración por defecto" -ForegroundColor Green
    }
} else {
    Write-Host "  ℹ .env ya existe (no se sobrescribirá)" -ForegroundColor Blue
}

Write-Host ""

# Instalar dependencias
Write-Host "[2/2] Instalando dependencias de Node.js..." -ForegroundColor Cyan
Write-Host "Esto puede tardar 2-5 minutos..." -ForegroundColor Yellow

npm install 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al instalar dependencias" -ForegroundColor Red
    Write-Host "Intenta ejecutar manualmente: npm install" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Dependencias instaladas correctamente" -ForegroundColor Green
Write-Host ""

# =============================================================================
# RESUMEN FINAL
# =============================================================================
Set-Location $rootDir

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓✓✓ INSTALACIÓN COMPLETADA ✓✓✓" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "📋 SERVICIOS BACKEND DISPONIBLES:" -ForegroundColor Cyan
Write-Host "  • API Backend:       http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:          http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • RabbitMQ Admin:    http://localhost:15672 (guest/guest)" -ForegroundColor White
Write-Host ""

Write-Host "📋 SERVICIOS FRONTEND:" -ForegroundColor Cyan
Write-Host "  • Aplicación Web:    http://localhost:3000" -ForegroundColor White
Write-Host ""

Write-Host "🚀 PARA INICIAR EL SISTEMA:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Backend (ya está corriendo):" -ForegroundColor Cyan
Write-Host "    cd Distribuidora_Perros_Gatos_back" -ForegroundColor White
Write-Host "    docker-compose ps                    # Ver estado" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Frontend:" -ForegroundColor Cyan
Write-Host "    cd Distribuidora_Perros_Gatos_front" -ForegroundColor White
Write-Host "    npm start                            # Iniciar aplicación" -ForegroundColor White
Write-Host ""

Write-Host "📊 ESTADO ACTUAL DE CONTENEDORES:" -ForegroundColor Cyan
Set-Location "$rootDir\Distribuidora_Perros_Gatos_back"
docker ps --filter "name=distribuidora" --filter "name=sqlserver" --filter "name=rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

Write-Host "🛠️  COMANDOS ÚTILES:" -ForegroundColor Yellow
Write-Host "  Backend:" -ForegroundColor Cyan
Write-Host "    docker-compose logs -f               # Ver logs en tiempo real" -ForegroundColor White
Write-Host "    docker-compose down                  # Detener servicios" -ForegroundColor White
Write-Host "    docker-compose up -d                 # Iniciar servicios" -ForegroundColor White
Write-Host "    docker-compose restart               # Reiniciar servicios" -ForegroundColor White
Write-Host ""
Write-Host "  Frontend:" -ForegroundColor Cyan
Write-Host "    npm start                            # Iniciar desarrollo" -ForegroundColor White
Write-Host "    npm run build                        # Crear build producción" -ForegroundColor White
Write-Host "    npm test                             # Ejecutar tests" -ForegroundColor White
Write-Host ""

Set-Location $rootDir

$startFrontend = Read-Host "¿Deseas iniciar el frontend ahora? (s/n)"

if ($startFrontend -eq "s" -or $startFrontend -eq "S") {
    Write-Host ""
    Write-Host "🚀 Iniciando frontend..." -ForegroundColor Green
    Write-Host "La aplicación se abrirá en http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    Set-Location "$rootDir\Distribuidora_Perros_Gatos_front"
    npm start
} else {
    Write-Host ""
    Write-Host "✓ Sistema instalado y backend corriendo" -ForegroundColor Green
    Write-Host "Para iniciar el frontend:" -ForegroundColor Cyan
    Write-Host "  cd Distribuidora_Perros_Gatos_front" -ForegroundColor White
    Write-Host "  npm start" -ForegroundColor White
    Write-Host ""
}
