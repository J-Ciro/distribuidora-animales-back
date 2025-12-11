# Script para configurar contraseña SMTP de Gmail
# Ejecutar: .\configurar-smtp.ps1

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  📧 Configurador de Gmail SMTP" -ForegroundColor Yellow
Write-Host "  Distribuidora Perros y Gatos" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar 2FA
Write-Host "📋 PASO 1: Verificar 2FA en Gmail" -ForegroundColor Green
Write-Host ""
Write-Host "   1. Abre: https://myaccount.google.com/security" -ForegroundColor White
Write-Host "   2. Busca 'Verificación en dos pasos'" -ForegroundColor White
Write-Host "   3. Actívala si no lo está" -ForegroundColor White
Write-Host ""

$continue = Read-Host "¿Ya tienes 2FA activado? (s/n)"
if ($continue -ne "s" -and $continue -ne "S") {
    Write-Host ""
    Write-Host "❌ Por favor, activa 2FA primero y vuelve a ejecutar este script." -ForegroundColor Red
    exit
}

# Paso 2: Generar contraseña
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 PASO 2: Generar Contraseña de Aplicación" -ForegroundColor Green
Write-Host ""
Write-Host "   1. Abre: https://myaccount.google.com/apppasswords" -ForegroundColor White
Write-Host "   2. Selecciona 'Correo' como aplicación" -ForegroundColor White
Write-Host "   3. Selecciona 'Otro' como dispositivo" -ForegroundColor White
Write-Host "   4. Escribe: Distribuidora Perros Gatos" -ForegroundColor White
Write-Host "   5. Haz clic en 'Generar'" -ForegroundColor White
Write-Host "   6. COPIA la contraseña de 16 caracteres" -ForegroundColor Yellow
Write-Host ""

Start-Process "https://myaccount.google.com/apppasswords"

Write-Host "⏳ Esperando que generes la contraseña..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$password = Read-Host "Pega aquí la contraseña de aplicación (sin espacios)"

if ([string]::IsNullOrWhiteSpace($password)) {
    Write-Host ""
    Write-Host "❌ No ingresaste ninguna contraseña. Saliendo..." -ForegroundColor Red
    exit
}

# Limpiar espacios
$password = $password -replace '\s', ''

Write-Host ""
Write-Host "✅ Contraseña recibida: $('*' * $password.Length) caracteres" -ForegroundColor Green

# Paso 3: Actualizar .env
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 PASO 3: Actualizar archivo .env" -ForegroundColor Green
Write-Host ""

$envPath = "backend\api\.env"

if (-not (Test-Path $envPath)) {
    Write-Host "❌ No se encontró el archivo .env en: $envPath" -ForegroundColor Red
    Write-Host "   Asegúrate de ejecutar este script desde la carpeta raíz del backend" -ForegroundColor Yellow
    exit
}

# Leer contenido actual
$content = Get-Content $envPath -Raw

# Reemplazar contraseña
$newContent = $content -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$password"

# Guardar
Set-Content -Path $envPath -Value $newContent -NoNewline

Write-Host "✅ Archivo .env actualizado" -ForegroundColor Green

# Paso 4: Reiniciar contenedor
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 PASO 4: Reiniciar contenedor API" -ForegroundColor Green
Write-Host ""

$restart = Read-Host "¿Reiniciar el contenedor ahora? (s/n)"
if ($restart -eq "s" -or $restart -eq "S") {
    Write-Host ""
    Write-Host "⏳ Reiniciando contenedor..." -ForegroundColor Yellow
    docker-compose restart api
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Contenedor reiniciado exitosamente" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  Hubo un problema al reiniciar. Intenta manualmente:" -ForegroundColor Yellow
        Write-Host "   docker-compose restart api" -ForegroundColor White
    }
}

# Paso 5: Test
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 PASO 5: Probar conexión SMTP" -ForegroundColor Green
Write-Host ""

$test = Read-Host "¿Ejecutar test de SMTP ahora? (s/n)"
if ($test -eq "s" -or $test -eq "S") {
    Write-Host ""
    Write-Host "⏳ Ejecutando test SMTP..." -ForegroundColor Yellow
    Write-Host ""
    
    docker exec distribuidora-api python /app/test_smtp.py
    
    Write-Host ""
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🎉 ¡Configuración exitosa!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Hay algún problema. Revisa los errores arriba." -ForegroundColor Yellow
    }
}

# Resumen final
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ CONFIGURACIÓN COMPLETA" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Ve a http://localhost:3000/registro" -ForegroundColor White
Write-Host "2. Regístrate con tu email" -ForegroundColor White
Write-Host "3. Revisa tu bandeja de entrada (o spam)" -ForegroundColor White
Write-Host "4. Ingresa el código de 6 dígitos" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentación completa: SOLUCION_EMAIL_NO_ENVIA.md" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
