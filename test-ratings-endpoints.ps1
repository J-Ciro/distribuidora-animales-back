# Script de prueba para verificar endpoints de calificaciones
# Ejecutar desde el directorio raíz del backend

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Probando Endpoints de Calificaciones" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Obtener estadísticas de un producto sin calificaciones
Write-Host "Test 1: Estadísticas de producto sin calificaciones" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/calificaciones/producto/1/stats" -Method GET
    Write-Host "✅ Respuesta recibida:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode -ForegroundColor Red
}

Write-Host ""
Write-Host "------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Test 2: Obtener calificaciones de un producto
Write-Host "Test 2: Calificaciones de un producto" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/calificaciones/producto/1" -Method GET
    Write-Host "✅ Respuesta recibida:" -ForegroundColor Green
    if ($response.length -eq 0) {
        Write-Host "  (Sin calificaciones)" -ForegroundColor Gray
    } else {
        $response | ConvertTo-Json -Depth 3
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Test 3: Verificar que el servidor responde
Write-Host "Test 3: Health check del servidor" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/docs" -Method GET
    Write-Host "✅ Servidor funcionando correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Servidor no responde" -ForegroundColor Red
    Write-Host "Por favor verifica que el backend esté corriendo en el puerto 8000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Tests completados" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Notas:" -ForegroundColor Yellow
Write-Host "- Si ves errores 404, verifica que la migración se haya aplicado" -ForegroundColor White
Write-Host "- Si ves errores de conexión, asegúrate de que el backend esté corriendo" -ForegroundColor White
Write-Host "- Los productos sin calificaciones deben retornar stats con valores en 0" -ForegroundColor White
Write-Host ""
