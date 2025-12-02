#!/usr/bin/env pwsh
# =============================================================================
# Script de Detención - Proyecto Completo
# =============================================================================
# Este script detiene todos los servicios del proyecto
# Ejecutar como: .\STOP.ps1
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deteniendo Servicios" -ForegroundColor Cyan
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "Distribuidora_Perros_Gatos_back"

# Detener Backend (Docker)
Write-Host "[1/2] Deteniendo servicios Docker..." -ForegroundColor Yellow

if (Test-Path $backendPath) {
    Set-Location $backendPath
    
    $containers = docker ps --filter "name=distribuidora" --filter "name=sqlserver" --filter "name=rabbitmq" --format "{{.Names}}"
    
    if ($containers) {
        docker-compose down
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Servicios Docker detenidos" -ForegroundColor Green
        } else {
            Write-Host "⚠ Hubo un problema al detener algunos servicios" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✓ No hay servicios Docker corriendo" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ Carpeta del backend no encontrada" -ForegroundColor Yellow
}

Write-Host ""

# Detener Frontend (Node)
Write-Host "[2/2] Deteniendo servidor React..." -ForegroundColor Yellow

$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*react*" -or 
    ($_.CommandLine -and $_.CommandLine -like "*react-scripts*")
}

if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Servidor React detenido" -ForegroundColor Green
} else {
    Write-Host "✓ No hay servidor React corriendo" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Todos los servicios detenidos" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
