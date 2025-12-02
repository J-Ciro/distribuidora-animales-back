#!/usr/bin/env pwsh
# =============================================================================
# Script de Instalación Completa desde Cero
# =============================================================================
# Este script instala TODO el proyecto automáticamente
# Ideal para nuevos desarrolladores o instalación limpia
# Ejecutar como: .\SETUP-COMPLETO.ps1
# =============================================================================

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  INSTALACIÓN COMPLETA - DISTRIBUIDORA PERROS Y GATOS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este script instalará y configurará:" -ForegroundColor White
Write-Host "  ✓ Backend (Docker + SQL Server + RabbitMQ)" -ForegroundColor Green
Write-Host "  ✓ Frontend (React + dependencias npm)" -ForegroundColor Green
Write-Host "  ✓ Base de datos (schema y configuración)" -ForegroundColor Green
Write-Host ""
Write-Host "Tiempo estimado: 8-12 minutos (primera vez)" -ForegroundColor Yellow
Write-Host ""

$continue = Read-Host "¿Deseas continuar? (S/N)"
if ($continue -ne "S" -and $continue -ne "s") {
    Write-Host "Instalación cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startTime = Get-Date

# ==================== BACKEND ====================
if (-not $SkipBackend) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  PASO 1/2: INSTALACIÓN DEL BACKEND" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    $backendPath = Join-Path $scriptPath "Distribuidora_Perros_Gatos_back"
    
    if (-not (Test-Path $backendPath)) {
        Write-Host "✗ Error: No se encontró la carpeta del backend" -ForegroundColor Red
        Write-Host "  Esperado en: $backendPath" -ForegroundColor DarkGray
        exit 1
    }
    
    Set-Location $backendPath
    
    if (Test-Path ".\INSTALL.ps1") {
        Write-Host "Ejecutando instalación del backend..." -ForegroundColor Yellow
        & .\INSTALL.ps1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Error en la instalación del backend" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✗ Error: No se encontró INSTALL.ps1 en el backend" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✓ Backend instalado correctamente" -ForegroundColor Green
}

# ==================== FRONTEND ====================
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  PASO 2/2: INSTALACIÓN DEL FRONTEND" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    $frontendPath = Join-Path $scriptPath "Distribuidora_Perros_Gatos_front"
    
    if (-not (Test-Path $frontendPath)) {
        Write-Host "✗ Error: No se encontró la carpeta del frontend" -ForegroundColor Red
        Write-Host "  Esperado en: $frontendPath" -ForegroundColor DarkGray
        exit 1
    }
    
    Set-Location $frontendPath
    
    if (Test-Path ".\INSTALL.ps1") {
        Write-Host "Ejecutando instalación del frontend..." -ForegroundColor Yellow
        & .\INSTALL.ps1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Error en la instalación del frontend" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✗ Error: No se encontró INSTALL.ps1 en el frontend" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✓ Frontend instalado correctamente" -ForegroundColor Green
}

# ==================== VERIFICACIÓN ====================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VERIFICACIÓN FINAL" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Set-Location $scriptPath

if (Test-Path ".\HEALTH-CHECK.ps1") {
    Write-Host "Ejecutando verificación de salud..." -ForegroundColor Yellow
    Write-Host ""
    & .\HEALTH-CHECK.ps1
}

# ==================== RESUMEN ====================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ INSTALACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Tiempo total: $($duration.Minutes) minutos $($duration.Seconds) segundos" -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "  PRÓXIMOS PASOS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host ""
Write-Host "1. Iniciar la aplicación:" -ForegroundColor Cyan
Write-Host "   .\START.ps1" -ForegroundColor White
Write-Host ""
Write-Host "   O manualmente:" -ForegroundColor DarkGray
Write-Host "   cd Distribuidora_Perros_Gatos_front" -ForegroundColor DarkGray
Write-Host "   npm start" -ForegroundColor DarkGray
Write-Host ""
Write-Host "2. Acceder a la aplicación:" -ForegroundColor Cyan
Write-Host "   Frontend:        http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API:     http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "   RabbitMQ Admin:  http://localhost:15672" -ForegroundColor White
Write-Host ""
Write-Host "3. Comandos útiles:" -ForegroundColor Cyan
Write-Host "   .\HEALTH-CHECK.ps1  - Verificar estado del sistema" -ForegroundColor White
Write-Host "   .\START.ps1         - Iniciar todos los servicios" -ForegroundColor White
Write-Host "   .\STOP.ps1          - Detener todos los servicios" -ForegroundColor White
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host ""
Write-Host "¡El proyecto está listo para usar! 🚀" -ForegroundColor Green
Write-Host ""
Write-Host "Para más información, consulta:" -ForegroundColor Yellow
Write-Host "  • README.md" -ForegroundColor White
Write-Host "  • INSTALACION_RAPIDA.md" -ForegroundColor White
Write-Host "  • CONFIGURACION.md" -ForegroundColor White
Write-Host ""
