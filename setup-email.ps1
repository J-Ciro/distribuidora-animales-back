# Script de configuración rápida SMTP
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    📧 CONFIGURACIÓN RÁPIDA DE EMAIL SMTP" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "INSTRUCCIONES:" -ForegroundColor Green
Write-Host "1. Se abrirá tu navegador en Google" -ForegroundColor White
Write-Host "2. Genera una contraseña de aplicación:" -ForegroundColor White
Write-Host "   - Selecciona 'Correo'" -ForegroundColor White
Write-Host "   - Selecciona 'Otro' y escribe: Distribuidora" -ForegroundColor White
Write-Host "   - Copia la contraseña de 16 caracteres" -ForegroundColor White
Write-Host ""

# Abrir navegador
Write-Host "⏳ Abriendo navegador..." -ForegroundColor Yellow
Start-Process "https://myaccount.google.com/apppasswords"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Red
Write-Host "   - Copia la contraseña SIN espacios" -ForegroundColor Yellow
Write-Host "   - Ejemplo: abcdefghijklmnop" -ForegroundColor Yellow
Write-Host ""

# Pedir contraseña
$password = Read-Host "Pega aquí tu contraseña de aplicación"

if ([string]::IsNullOrWhiteSpace($password)) {
    Write-Host ""
    Write-Host "❌ No ingresaste contraseña. Abortando..." -ForegroundColor Red
    exit 1
}

# Limpiar espacios
$password = $password.Trim() -replace '\s', ''

Write-Host ""
Write-Host "✅ Contraseña recibida ($($password.Length) caracteres)" -ForegroundColor Green

# Actualizar .env
Write-Host ""
Write-Host "⏳ Actualizando archivo .env..." -ForegroundColor Yellow

$envPath = "backend\api\.env"
$content = Get-Content $envPath -Raw
$newContent = $content -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$password"
Set-Content -Path $envPath -Value $newContent -NoNewline

Write-Host "✅ Archivo .env actualizado" -ForegroundColor Green

# Reiniciar contenedor
Write-Host ""
Write-Host "⏳ Reiniciando contenedor API..." -ForegroundColor Yellow
docker-compose restart api | Out-Null
Start-Sleep -Seconds 5

Write-Host "✅ Contenedor reiniciado" -ForegroundColor Green

# Test de conexión
Write-Host ""
Write-Host "⏳ Probando conexión SMTP..." -ForegroundColor Yellow
Write-Host ""

$output = docker exec distribuidora-api python /app/test_smtp.py 2>&1

if ($output -match "Login successful" -and $output -match "Test email sent") {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "    ✅ ¡CONFIGURACIÓN EXITOSA!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "El sistema de emails está funcionando correctamente." -ForegroundColor White
    Write-Host ""
    Write-Host "PRÓXIMOS PASOS:" -ForegroundColor Yellow
    Write-Host "1. Ve a http://localhost:3000/registro" -ForegroundColor White
    Write-Host "2. Regístrate con tu email" -ForegroundColor White
    Write-Host "3. Recibirás un código de 6 dígitos" -ForegroundColor White
    Write-Host "4. Ingrésalo en la página de verificación" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "    ❌ ERROR EN LA CONFIGURACIÓN" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "Salida del test:" -ForegroundColor Yellow
    Write-Host $output
    Write-Host ""
    Write-Host "POSIBLES SOLUCIONES:" -ForegroundColor Yellow
    Write-Host "1. Verifica que la contraseña no tenga espacios" -ForegroundColor White
    Write-Host "2. Asegúrate de tener 2FA activado en Gmail" -ForegroundColor White
    Write-Host "3. Genera una nueva contraseña de aplicación" -ForegroundColor White
    Write-Host "4. Ejecuta nuevamente: .\setup-email.ps1" -ForegroundColor White
    Write-Host ""
}
