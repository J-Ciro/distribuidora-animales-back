# ========================================
# Script de Configuración Automática - Backend
# Distribuidora Perros y Gatos
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN AUTOMÁTICA - BACKEND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker esté corriendo
Write-Host "✓ Verificando Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "  ✓ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "  ✗ ERROR: Docker no está corriendo" -ForegroundColor Red
    Write-Host "  Por favor, inicia Docker Desktop y vuelve a ejecutar este script" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Crear archivos .env desde los ejemplos
Write-Host "✓ Configurando archivos de entorno..." -ForegroundColor Yellow

# API .env
if (Test-Path "backend/api/.env") {
    Write-Host "  ℹ backend/api/.env ya existe (no se sobrescribirá)" -ForegroundColor Blue
} else {
    if (Test-Path "backend/api/.env.example") {
        Copy-Item "backend/api/.env.example" "backend/api/.env"
        Write-Host "  ✓ Creado backend/api/.env" -ForegroundColor Green
    } else {
        Write-Host "  ✗ No se encontró backend/api/.env.example" -ForegroundColor Red
    }
}

# Worker .env
if (Test-Path "backend/worker/.env") {
    Write-Host "  ℹ backend/worker/.env ya existe (no se sobrescribirá)" -ForegroundColor Blue
} else {
    if (Test-Path "backend/worker/.env.example") {
        Copy-Item "backend/worker/.env.example" "backend/worker/.env"
        Write-Host "  ✓ Creado backend/worker/.env" -ForegroundColor Green
    } else {
        Write-Host "  ✗ No se encontró backend/worker/.env.example" -ForegroundColor Red
    }
}

Write-Host ""

# Preguntar por configuración de email
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN DE EMAIL (OPCIONAL)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para que funcione el envío de emails de verificación," -ForegroundColor Yellow
Write-Host "necesitas configurar una cuenta de Gmail." -ForegroundColor Yellow
Write-Host ""
Write-Host "Si no lo configuras ahora, puedes hacerlo después editando:" -ForegroundColor Gray
Write-Host "  backend/api/.env" -ForegroundColor Gray
Write-Host ""

$configureEmail = Read-Host "¿Deseas configurar el email ahora? (s/n)"

if ($configureEmail -eq "s" -or $configureEmail -eq "S") {
    Write-Host ""
    $smtpUser = Read-Host "Email de Gmail (ejemplo: tucorreo@gmail.com)"
    $smtpPassword = Read-Host "Contraseña de aplicación de Gmail" -AsSecureString
    $smtpPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtpPassword))
    
    # Actualizar backend/api/.env
    $envContent = Get-Content "backend/api/.env"
    $envContent = $envContent -replace 'SMTP_USER=.*', "SMTP_USER=$smtpUser"
    $envContent = $envContent -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$smtpPasswordPlain"
    $envContent = $envContent -replace 'SMTP_FROM=.*', "SMTP_FROM=$smtpUser"
    $envContent | Set-Content "backend/api/.env"
    
    # Actualizar backend/worker/.env
    $envContentWorker = Get-Content "backend/worker/.env"
    $envContentWorker = $envContentWorker -replace 'SMTP_USER=.*', "SMTP_USER=$smtpUser"
    $envContentWorker = $envContentWorker -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$smtpPasswordPlain"
    $envContentWorker = $envContentWorker -replace 'SMTP_FROM=.*', "SMTP_FROM=$smtpUser"
    $envContentWorker | Set-Content "backend/worker/.env"
    
    Write-Host "  ✓ Email configurado correctamente" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "  ℹ Email no configurado. El registro de usuarios no enviará emails." -ForegroundColor Blue
    Write-Host "  Podrás configurarlo después en backend/api/.env" -ForegroundColor Gray
    Write-Host ""
}

# Detener contenedores si ya están corriendo
Write-Host "✓ Deteniendo contenedores existentes (si hay)..." -ForegroundColor Yellow
docker-compose down 2>$null | Out-Null

Write-Host ""

# Iniciar contenedores
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIANDO CONTENEDORES DOCKER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esto puede tomar unos minutos la primera vez..." -ForegroundColor Yellow
Write-Host ""

docker-compose up -d

Write-Host ""

# Esperar a que los servicios estén listos
Write-Host "✓ Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar estado de contenedores
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ESTADO DE LOS SERVICIOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$containers = docker-compose ps --format json | ConvertFrom-Json

foreach ($container in $containers) {
    $name = $container.Service
    $status = $container.State
    
    if ($status -eq "running") {
        Write-Host "  ✓ $name : corriendo" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $name : $status" -ForegroundColor Red
    }
}

Write-Host ""

# Verificar API
Write-Host "✓ Verificando API..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ API respondiendo correctamente en http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ API aún no responde (puede tomar unos segundos más)" -ForegroundColor Yellow
}

Write-Host ""

# Resumen final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✓ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor White
Write-Host "  • API (FastAPI):     http://localhost:8000" -ForegroundColor White
Write-Host "  • Documentación:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • RabbitMQ UI:       http://localhost:15672 (guest/guest)" -ForegroundColor White
Write-Host "  • SQL Server:        localhost:1433 (sa/YourStrong@Passw0rd)" -ForegroundColor White
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor White
Write-Host "  • Ver logs:          docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • Reiniciar:         docker-compose restart" -ForegroundColor Gray
Write-Host "  • Detener:           docker-compose down" -ForegroundColor Gray
Write-Host ""

if ($configureEmail -ne "s" -and $configureEmail -ne "S") {
    Write-Host "⚠ RECORDATORIO: Configura el email en backend/api/.env" -ForegroundColor Yellow
    Write-Host "  para habilitar el envío de códigos de verificación." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Presiona Enter para continuar..." -ForegroundColor Cyan
Read-Host
