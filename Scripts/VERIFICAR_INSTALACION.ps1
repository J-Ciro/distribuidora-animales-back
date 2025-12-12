#!/usr/bin/env pwsh
# =============================================================================
# Script de Verificación de Instalación
# =============================================================================
# Este script verifica que todo esté correctamente instalado y configurado
# Ejecutar: .\VERIFICAR_INSTALACION.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICACIÓN DE INSTALACIÓN" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Get-Location
$errorsFound = 0
$warningsFound = 0

# =============================================================================
# VERIFICAR REQUISITOS
# =============================================================================
Write-Host "[1/8] Verificando Requisitos del Sistema..." -ForegroundColor Yellow
Write-Host ""

# Node.js
Write-Host "  Node.js:" -NoNewline
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Instalado ($nodeVersion)" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ✗ NO INSTALADO" -ForegroundColor Red
    $errorsFound++
}

# npm
Write-Host "  npm:" -NoNewline
try {
    $npmVersion = npm --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Instalado (v$npmVersion)" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ✗ NO INSTALADO" -ForegroundColor Red
    $errorsFound++
}

# Docker
Write-Host "  Docker:" -NoNewline
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Instalado" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ✗ NO INSTALADO" -ForegroundColor Red
    $errorsFound++
}

# Docker corriendo
Write-Host "  Docker en ejecución:" -NoNewline
try {
    docker ps >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Corriendo" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ✗ NO ESTÁ CORRIENDO" -ForegroundColor Red
    $errorsFound++
}

Write-Host ""

# =============================================================================
# VERIFICAR ESTRUCTURA DE DIRECTORIOS
# =============================================================================
Write-Host "[2/8] Verificando Estructura de Directorios..." -ForegroundColor Yellow
Write-Host ""

$requiredDirs = @(
    "distribuidora-animales-back",
    "distribuidora-animales-front",
    "distribuidora-animales-back\backend\api",
    "distribuidora-animales-back\backend\worker",
    "distribuidora-animales-front\src",
    "distribuidora-animales-front\public"
)

foreach ($dir in $requiredDirs) {
    Write-Host "  $dir :" -NoNewline
    if (Test-Path $dir) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗ NO EXISTE" -ForegroundColor Red
        $errorsFound++
    }
}

Write-Host ""

# =============================================================================
# VERIFICAR ARCHIVOS .env.example
# =============================================================================
Write-Host "[3/8] Verificando Plantillas .env.example..." -ForegroundColor Yellow
Write-Host ""

$envExamples = @(
    "distribuidora-animales-front\.env.example",
    "distribuidora-animales-back\backend\api\.env.example",
    "distribuidora-animales-back\backend\worker\.env.example"
)

foreach ($envFile in $envExamples) {
    Write-Host "  $envFile :" -NoNewline
    if (Test-Path $envFile) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗ FALTA" -ForegroundColor Red
        $errorsFound++
    }
}

Write-Host ""

# =============================================================================
# VERIFICAR ARCHIVOS .env (creados por scripts)
# =============================================================================
Write-Host "[4/8] Verificando Archivos .env (creados por instalación)..." -ForegroundColor Yellow
Write-Host ""

$envFiles = @(
    "distribuidora-animales-front\.env",
    "distribuidora-animales-back\backend\api\.env",
    "distribuidora-animales-back\backend\worker\.env"
)

foreach ($envFile in $envFiles) {
    Write-Host "  $envFile :" -NoNewline
    if (Test-Path $envFile) {
        Write-Host " ✓ Existe" -ForegroundColor Green
    } else {
        Write-Host " ⚠ NO EXISTE (se creará al ejecutar scripts)" -ForegroundColor Yellow
        $warningsFound++
    }
}

Write-Host ""

# =============================================================================
# VERIFICAR CONTENEDORES DOCKER
# =============================================================================
Write-Host "[5/8] Verificando Contenedores Docker..." -ForegroundColor Yellow
Write-Host ""

$containers = @("sqlserver", "rabbitmq", "distribuidora-api", "distribuidora-worker")

Set-Location "$rootDir\distribuidora-animales-back" -ErrorAction SilentlyContinue

foreach ($container in $containers) {
    Write-Host "  $container :" -NoNewline
    $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>$null
    if ($status) {
        $health = docker inspect $container --format='{{.State.Health.Status}}' 2>$null
        if ($health -eq "healthy") {
            Write-Host " ✓ Running (healthy)" -ForegroundColor Green
        } elseif ($health -eq "starting") {
            Write-Host " ⚠ Running (starting...)" -ForegroundColor Yellow
            $warningsFound++
        } else {
            Write-Host " ✓ Running" -ForegroundColor Green
        }
    } else {
        Write-Host " ✗ NO ESTÁ CORRIENDO" -ForegroundColor Red
        $errorsFound++
    }
}

Set-Location $rootDir

Write-Host ""

# =============================================================================
# VERIFICAR DEPENDENCIAS FRONTEND
# =============================================================================
Write-Host "[6/8] Verificando Dependencias del Frontend..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\distribuidora-animales-front" -ErrorAction SilentlyContinue

Write-Host "  node_modules:" -NoNewline
if (Test-Path "node_modules") {
    $packageCount = (Get-ChildItem "node_modules" -Directory).Count
    Write-Host " ✓ Instaladas ($packageCount paquetes)" -ForegroundColor Green
} else {
    Write-Host " ✗ NO INSTALADAS (ejecuta: npm install)" -ForegroundColor Red
    $errorsFound++
}

Write-Host "  package.json:" -NoNewline
if (Test-Path "package.json") {
    Write-Host " ✓ Existe" -ForegroundColor Green
} else {
    Write-Host " ✗ FALTA" -ForegroundColor Red
    $errorsFound++
}

Set-Location $rootDir

Write-Host ""

# =============================================================================
# VERIFICAR BASE DE DATOS
# =============================================================================
Write-Host "[7/8] Verificando Base de Datos..." -ForegroundColor Yellow
Write-Host ""

$dbCheck = docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q "SELECT name FROM sys.databases WHERE name = 'distribuidora_db';" 2>$null

if ($dbCheck -match "distribuidora_db") {
    Write-Host "  Base de datos 'distribuidora_db':" -NoNewline
    Write-Host " ✓ Existe" -ForegroundColor Green
    
    # Verificar tablas
    $tableCount = docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db -Q "SELECT COUNT(*) as total FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';" 2>$null
    
    if ($tableCount -match "\d+") {
        $count = [regex]::Match($tableCount, "\d+").Value
        Write-Host "  Tablas en la base de datos:" -NoNewline
        if ([int]$count -gt 0) {
            Write-Host " ✓ $count tablas creadas" -ForegroundColor Green
        } else {
            Write-Host " ⚠ 0 tablas (ejecuta migraciones)" -ForegroundColor Yellow
            $warningsFound++
        }
    }
} else {
    Write-Host "  Base de datos:" -NoNewline
    Write-Host " ✗ NO EXISTE (ejecuta: .\INSTALL.ps1)" -ForegroundColor Red
    $errorsFound++
}

Write-Host ""

# =============================================================================
# VERIFICAR SERVICIOS WEB
# =============================================================================
Write-Host "[8/8] Verificando Servicios Web..." -ForegroundColor Yellow
Write-Host ""

# Backend API
Write-Host "  Backend API (http://localhost:8000):" -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 3 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host " ✓ Responde" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ✗ NO RESPONDE" -ForegroundColor Red
    $errorsFound++
}

# API Docs
Write-Host "  API Docs (http://localhost:8000/docs):" -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 3 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host " ✓ Disponible" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ⚠ NO DISPONIBLE" -ForegroundColor Yellow
    $warningsFound++
}

# RabbitMQ
Write-Host "  RabbitMQ (http://localhost:15672):" -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:15672/" -UseBasicParsing -TimeoutSec 3 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host " ✓ Disponible" -ForegroundColor Green
    } else {
        throw
    }
} catch {
    Write-Host " ⚠ NO DISPONIBLE" -ForegroundColor Yellow
    $warningsFound++
}

Write-Host ""

# =============================================================================
# RESUMEN
# =============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN DE VERIFICACIÓN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($errorsFound -eq 0 -and $warningsFound -eq 0) {
    Write-Host "✓✓✓ TODO ESTÁ CORRECTAMENTE INSTALADO ✓✓✓" -ForegroundColor Green
    Write-Host ""
    Write-Host "El sistema está listo para usar:" -ForegroundColor White
    Write-Host "  • Backend: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  • Frontend: ejecuta 'npm start' en distribuidora-animales-front" -ForegroundColor Cyan
} elseif ($errorsFound -eq 0) {
    Write-Host "✓ INSTALACIÓN COMPLETA CON ADVERTENCIAS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Advertencias encontradas: $warningsFound" -ForegroundColor Yellow
    Write-Host "El sistema debería funcionar, pero revisa las advertencias arriba." -ForegroundColor Yellow
} else {
    Write-Host "✗ SE ENCONTRARON PROBLEMAS" -ForegroundColor Red
    Write-Host ""
    Write-Host "Errores: $errorsFound" -ForegroundColor Red
    Write-Host "Advertencias: $warningsFound" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "RECOMENDACIÓN:" -ForegroundColor Yellow
    Write-Host "Ejecuta el script de instalación completa:" -ForegroundColor White
    Write-Host "  .\INSTALACION_COMPLETA.ps1" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($errorsFound -gt 0) {
    exit 1
} else {
    exit 0
}
