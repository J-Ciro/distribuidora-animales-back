#!/usr/bin/env pwsh
# =============================================================================
# Script de Inicio Rápido - Proyecto Completo
# =============================================================================
# Este script inicia tanto el backend como el frontend
# Ejecutar como: .\START.ps1
# =============================================================================

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "  Inicio Rápido del Proyecto" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Detectar ubicación actual
$currentPath = Get-Location
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Función para verificar si el backend está corriendo
function Test-BackendRunning {
    try {
        $containers = docker ps --filter "name=distribuidora-api" --format "{{.Names}}"
        return $containers -match "distribuidora-api"
    } catch {
        return $false
    }
}

# Función para verificar si el frontend está corriendo
function Test-FrontendRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Iniciar Backend
if (-not $FrontendOnly) {
    Write-Host "[Backend] Verificando estado..." -ForegroundColor Yellow
    
    $backendPath = Join-Path $scriptPath "distribuidora-animales-back"
    
    if (-not (Test-Path $backendPath)) {
        Write-Host "✗ No se encontró la carpeta del backend en: $backendPath" -ForegroundColor Red
        exit 1
    }
    
    Set-Location $backendPath
    
    if (Test-BackendRunning) {
        Write-Host "✓ Backend ya está corriendo" -ForegroundColor Green
    } else {
        Write-Host "Iniciando servicios Docker..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Error al iniciar el backend" -ForegroundColor Red
            Write-Host "Intenta ejecutar: .\INSTALL.ps1" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "✓ Backend iniciado" -ForegroundColor Green
        
        # Esperar a que la API esté lista
        Write-Host "Esperando a que la API esté lista..." -ForegroundColor Yellow
        $maxAttempts = 30
        $attempt = 0
        $apiReady = $false
        
        while ($attempt -lt $maxAttempts -and -not $apiReady) {
            $attempt++
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $apiReady = $true
                    Write-Host "✓ API lista en http://localhost:8000" -ForegroundColor Green
                }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        
        if (-not $apiReady) {
            Write-Host "⚠ La API está tardando en iniciar, pero puedes continuar" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

# Iniciar Frontend
if (-not $BackendOnly) {
    Write-Host "[Frontend] Verificando estado..." -ForegroundColor Yellow
    
    $frontendPath = Join-Path $scriptPath "distribuidora-animales-front"
    
    if (-not (Test-Path $frontendPath)) {
        Write-Host "✗ No se encontró la carpeta del frontend en: $frontendPath" -ForegroundColor Red
        exit 1
    }
    
    Set-Location $frontendPath
    
    # Verificar que node_modules existe
    if (-not (Test-Path "node_modules")) {
        Write-Host "⚠ Dependencias no instaladas. Ejecutando instalación..." -ForegroundColor Yellow
        Write-Host "Esto puede tardar unos minutos..." -ForegroundColor Cyan
        npm install
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Error al instalar dependencias" -ForegroundColor Red
            Write-Host "Intenta ejecutar: .\INSTALL.ps1" -ForegroundColor Yellow
            exit 1
        }
    }
    
    if (Test-FrontendRunning) {
        Write-Host "✓ Frontend ya está corriendo en http://localhost:3000" -ForegroundColor Green
    } else {
        Write-Host "Iniciando servidor de desarrollo React..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  El navegador se abrirá automáticamente" -ForegroundColor Green
        Write-Host "  Presiona Ctrl+C para detener" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        # Iniciar npm start
        npm start
    }
}

# Restaurar ubicación original
Set-Location $currentPath
