# 🚀 Script de Verificación Rápida de Migración
# Este script verifica automáticamente que el sistema de migración funcionó correctamente

Write-Host "=================================="  -ForegroundColor Cyan
Write-Host "🔍 Verificación del Sistema de Migración" -ForegroundColor Cyan
Write-Host "=================================="  -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $true

# Verificación 1: Contenedores en ejecución
Write-Host "1️⃣  Verificando estado de contenedores..." -ForegroundColor Yellow
$containers = docker-compose ps --format json | ConvertFrom-Json

$requiredContainers = @("distribuidora-api", "distribuidora-worker", "sqlserver", "rabbitmq")
$runningContainers = @()

foreach ($container in $containers) {
    if ($container.State -eq "running") {
        $runningContainers += $container.Service
    }
}

foreach ($required in $requiredContainers) {
    if ($runningContainers -contains $required) {
        Write-Host "   ✅ $required - Running" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $required - NOT Running" -ForegroundColor Red
        $allChecksPassed = $false
    }
}
Write-Host ""

# Verificación 2: Estado del Migrator
Write-Host "2️⃣  Verificando estado de db-migrator..." -ForegroundColor Yellow
$migratorStatus = docker ps -a --filter "name=distribuidora-db-migrator" --format "{{.Status}}"

if ($migratorStatus -like "*Exited (0)*") {
    Write-Host "   ✅ db-migrator completó exitosamente (exit code 0)" -ForegroundColor Green
} elseif ($migratorStatus -like "*Exited*") {
    Write-Host "   ❌ db-migrator falló (exit code != 0)" -ForegroundColor Red
    Write-Host "   💡 Ver logs: docker logs distribuidora-db-migrator" -ForegroundColor Yellow
    $allChecksPassed = $false
} else {
    Write-Host "   ⏳ db-migrator aún ejecutándose o no iniciado" -ForegroundColor Yellow
    $allChecksPassed = $false
}
Write-Host ""

# Verificación 3: Logs de Migración
Write-Host "3️⃣  Verificando logs de migración..." -ForegroundColor Yellow
$migratorLogs = docker logs distribuidora-db-migrator 2>&1

if ($migratorLogs -like "*Database initialization complete!*") {
    Write-Host "   ✅ Mensaje de éxito encontrado en logs" -ForegroundColor Green
} else {
    Write-Host "   ❌ No se encontró mensaje de éxito" -ForegroundColor Red
    $allChecksPassed = $false
}

if ($migratorLogs -like "*Schema applied successfully*") {
    Write-Host "   ✅ Schema aplicado correctamente" -ForegroundColor Green
} else {
    Write-Host "   ❌ Schema no aplicado" -ForegroundColor Red
    $allChecksPassed = $false
}

# Contar migraciones aplicadas
$migrationCount = ($migratorLogs | Select-String "Applying migration:").Count
Write-Host "   📋 Migraciones aplicadas: $migrationCount" -ForegroundColor Cyan

# Contar seeders aplicados
$seederCount = ($migratorLogs | Select-String "Applying seeder:").Count
Write-Host "   🌱 Seeders aplicados: $seederCount" -ForegroundColor Cyan
Write-Host ""

# Verificación 4: API funcionando
Write-Host "4️⃣  Verificando API..." -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Dar tiempo a la API para estar lista

try {
    $apiResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($apiResponse.StatusCode -eq 200) {
        Write-Host "   ✅ API responde correctamente (200 OK)" -ForegroundColor Green
        Write-Host "   🌐 Documentación disponible en: http://localhost:8000/docs" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ API no responde o está caída" -ForegroundColor Red
    Write-Host "   💡 Ver logs: docker logs distribuidora-api" -ForegroundColor Yellow
    $allChecksPassed = $false
}
Write-Host ""

# Verificación 5: Logs de API (sin errores de BD)
Write-Host "5️⃣  Verificando conexión de API a base de datos..." -ForegroundColor Yellow
$apiLogs = docker logs distribuidora-api --tail 50 2>&1

if ($apiLogs -like "*Database connection pool initialized successfully*") {
    Write-Host "   ✅ API conectada a base de datos exitosamente" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No se encontró mensaje de conexión exitosa" -ForegroundColor Yellow
}

if ($apiLogs -like "*ERROR*" -or $apiLogs -like "*CRITICAL*") {
    Write-Host "   ⚠️  Se encontraron errores en logs de API" -ForegroundColor Yellow
    Write-Host "   💡 Revisar logs completos: docker logs distribuidora-api" -ForegroundColor Yellow
}
Write-Host ""

# Verificación 6: Tablas en Base de Datos
Write-Host "6️⃣  Verificando tablas en base de datos..." -ForegroundColor Yellow
try {
    $tableQuery = "SET NOCOUNT ON; USE distribuidora_db; SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
    $tableCountOutput = docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q $tableQuery -h -1 2>&1
    
    # Extraer el número de tablas (última línea no vacía)
    $tableCount = ($tableCountOutput | Where-Object { $_ -match "^\s*\d+\s*$" } | Select-Object -Last 1).Trim()
    
    if ($tableCount -eq "14") {
        Write-Host "   ✅ 14 tablas creadas correctamente" -ForegroundColor Green
    } elseif ($tableCount) {
        Write-Host "   ⚠️  $tableCount tablas creadas (esperado: 14)" -ForegroundColor Yellow
        $allChecksPassed = $false
    } else {
        Write-Host "   ❌ No se pudo verificar tablas" -ForegroundColor Red
        $allChecksPassed = $false
    }
} catch {
    Write-Host "   ❌ Error al consultar base de datos" -ForegroundColor Red
    $allChecksPassed = $false
}
Write-Host ""

# Verificación 7: Datos de Ejemplo
Write-Host "7️⃣  Verificando datos de ejemplo..." -ForegroundColor Yellow
try {
    # Verificar categorías
    $categoriaQuery = "SET NOCOUNT ON; USE distribuidora_db; SELECT COUNT(*) FROM Categorias;"
    $categoriaCountOutput = docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q $categoriaQuery -h -1 2>&1
    $categoriaCount = ($categoriaCountOutput | Where-Object { $_ -match "^\s*\d+\s*$" } | Select-Object -Last 1).Trim()
    
    if ([int]$categoriaCount -ge 2) {
        Write-Host "   ✅ Categorías iniciales: $categoriaCount" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Categorías encontradas: $categoriaCount (esperado: 2+)" -ForegroundColor Yellow
    }
    
    # Verificar productos
    $productoQuery = "SET NOCOUNT ON; USE distribuidora_db; SELECT COUNT(*) FROM Productos;"
    $productoCountOutput = docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q $productoQuery -h -1 2>&1
    $productoCount = ($productoCountOutput | Where-Object { $_ -match "^\s*\d+\s*$" } | Select-Object -Last 1).Trim()
    
    if ([int]$productoCount -ge 5) {
        Write-Host "   ✅ Productos de ejemplo: $productoCount" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Productos encontrados: $productoCount (esperado: 5+)" -ForegroundColor Yellow
    }
    
    # Verificar carrusel
    $carruselQuery = "SET NOCOUNT ON; USE distribuidora_db; SELECT COUNT(*) FROM CarruselImagenes;"
    $carruselCountOutput = docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q $carruselQuery -h -1 2>&1
    $carruselCount = ($carruselCountOutput | Where-Object { $_ -match "^\s*\d+\s*$" } | Select-Object -Last 1).Trim()
    
    if ([int]$carruselCount -ge 5) {
        Write-Host "   ✅ Imágenes de carrusel: $carruselCount" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Imágenes de carrusel: $carruselCount (esperado: 5)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  No se pudieron verificar todos los datos de ejemplo" -ForegroundColor Yellow
}
Write-Host ""

# Resumen Final
Write-Host "=================================="  -ForegroundColor Cyan
if ($allChecksPassed) {
    Write-Host "✅ TODAS LAS VERIFICACIONES PASARON" -ForegroundColor Green
    Write-Host "=================================="  -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 ¡Sistema de migración funcionando perfectamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 Enlaces Útiles:" -ForegroundColor Cyan
    Write-Host "   • Documentación API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   • RabbitMQ Management: http://localhost:15672 (guest/guest)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  ALGUNAS VERIFICACIONES FALLARON" -ForegroundColor Red
    Write-Host "=================================="  -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📖 Consulta la guía de troubleshooting:" -ForegroundColor Yellow
    Write-Host "   • VERIFICACION_MIGRACION.md" -ForegroundColor White
    Write-Host "   • MIGRACION_BASE_DATOS.md" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 Comandos de diagnóstico:" -ForegroundColor Yellow
    Write-Host "   docker logs distribuidora-db-migrator" -ForegroundColor White
    Write-Host "   docker logs distribuidora-api" -ForegroundColor White
    Write-Host "   docker logs sqlserver" -ForegroundColor White
    Write-Host ""
}

Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
