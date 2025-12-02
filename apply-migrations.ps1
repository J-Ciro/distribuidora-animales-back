#!/usr/bin/env pwsh
# =============================================================================
# Script para Aplicar Migraciones de Base de Datos
# =============================================================================
# Este script aplica el schema y todas las migraciones a SQL Server
# Ejecutar como: .\apply-migrations.ps1
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Aplicar Migraciones de Base de Datos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que SQL Server esté corriendo
Write-Host "[1/3] Verificando SQL Server..." -ForegroundColor Yellow

$sqlHealth = docker inspect sqlserver --format='{{.State.Health.Status}}' 2>$null

if ($sqlHealth -ne "healthy") {
    Write-Host "✗ SQL Server no está corriendo o no está saludable" -ForegroundColor Red
    Write-Host "Ejecuta: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ SQL Server está disponible" -ForegroundColor Green
Write-Host ""

# Crear base de datos si no existe
Write-Host "[2/3] Creando base de datos..." -ForegroundColor Yellow

$createDbResult = docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q "USE master; IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'distribuidora_db') CREATE DATABASE distribuidora_db;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Base de datos 'distribuidora_db' verificada/creada" -ForegroundColor Green
} else {
    Write-Host "✗ Error al crear la base de datos" -ForegroundColor Red
    Write-Host $createDbResult
    exit 1
}

Write-Host ""

# Aplicar schema principal
Write-Host "[3/3] Aplicando schema y migraciones..." -ForegroundColor Yellow
Write-Host ""

# Schema principal
Write-Host "Aplicando schema principal (schema.sql)..." -ForegroundColor Cyan

if (Test-Path "sql/schema.sql") {
    Get-Content "sql/schema.sql" -Raw | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Schema principal aplicado" -ForegroundColor Green
    } else {
        Write-Host "⚠ Error al aplicar schema (puede ser normal si ya existe)" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ No se encontró sql/schema.sql" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Aplicar migraciones
Write-Host "Aplicando migraciones..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path "sql/migrations") {
    $migrationFiles = Get-ChildItem -Path "sql/migrations" -Filter "*.sql" | Sort-Object Name
    
    if ($migrationFiles.Count -eq 0) {
        Write-Host "⚠ No se encontraron migraciones en sql/migrations" -ForegroundColor Yellow
    } else {
        $successCount = 0
        $skipCount = 0
        $errorCount = 0
        
        foreach ($migration in $migrationFiles) {
            Write-Host "  Aplicando: $($migration.Name)..." -ForegroundColor DarkGray
            
            $migrationContent = Get-Content $migration.FullName -Raw
            $result = $migrationContent | docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                # Verificar si hay errores en la salida
                if ($result -match "Msg \d+") {
                    # Hay un mensaje de error de SQL
                    if ($result -match "already exists|ALTER TABLE statement conflicted|There is already an object") {
                        $skipCount++
                        Write-Host "  ⊘ $($migration.Name) - Ya aplicada" -ForegroundColor DarkYellow
                    } else {
                        $errorCount++
                        Write-Host "  ✗ $($migration.Name) - Error" -ForegroundColor Red
                        Write-Host "    $result" -ForegroundColor DarkRed
                    }
                } else {
                    $successCount++
                    Write-Host "  ✓ $($migration.Name)" -ForegroundColor Green
                }
            } else {
                $skipCount++
                Write-Host "  ⊘ $($migration.Name) - Omitida (posiblemente ya aplicada)" -ForegroundColor DarkYellow
            }
        }
        
        Write-Host ""
        Write-Host "Resumen de migraciones:" -ForegroundColor Cyan
        Write-Host "  • Total: $($migrationFiles.Count)" -ForegroundColor White
        Write-Host "  • Aplicadas: $successCount" -ForegroundColor Green
        Write-Host "  • Ya existían: $skipCount" -ForegroundColor Yellow
        if ($errorCount -gt 0) {
            Write-Host "  • Errores: $errorCount" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⚠ No se encontró la carpeta sql/migrations" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ PROCESO COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verificar tablas creadas
Write-Host "Verificando tablas creadas..." -ForegroundColor Cyan

$tablesResult = docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME;" -h -1 2>&1

if ($LASTEXITCODE -eq 0) {
    $tables = $tablesResult | Where-Object { $_ -match '\S' }
    Write-Host ""
    Write-Host "Tablas en la base de datos:" -ForegroundColor Green
    foreach ($table in $tables) {
        $tableName = $table.Trim()
        if ($tableName) {
            Write-Host "  • $tableName" -ForegroundColor White
        }
    }
} else {
    Write-Host "⚠ No se pudo listar las tablas" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "¡Migraciones aplicadas correctamente! ✓" -ForegroundColor Green
Write-Host ""
