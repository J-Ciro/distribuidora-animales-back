# Script para resetear la base de datos completamente

Write-Host "========================================"
Write-Host "Resetting Database..."
Write-Host "========================================" -ForegroundColor Cyan

# Stop and remove containers
Write-Host "[1/3] Stopping Docker containers..." -ForegroundColor Yellow
docker-compose down -v

# Wait for cleanup
Start-Sleep -Seconds 5

# Start SQL Server only
Write-Host "[2/3] Starting SQL Server container..." -ForegroundColor Yellow
docker-compose up -d sqlserver

# Wait for SQL Server to be ready
Write-Host "[3/3] Waiting for SQL Server to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "✅ Database reset complete. You can now run: docker-compose up distribuidora-api" -ForegroundColor Green
