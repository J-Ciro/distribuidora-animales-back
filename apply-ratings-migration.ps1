# Script para aplicar la migración de calificaciones
# Ejecutar desde el directorio raíz del proyecto backend

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Aplicando migración de Sistema de Calificaciones" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Configuración de la base de datos
$Server = "localhost"
$Database = "distribuidora_db"
$Username = "sa"

# Solicitar contraseña de forma segura
$Password = Read-Host "Ingrese la contraseña de SQL Server" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Ruta de la migración
$MigrationFile = ".\sql\migrations\010_create_ratings.sql"

# Verificar que existe el archivo
if (-not (Test-Path $MigrationFile)) {
    Write-Host "❌ Error: No se encontró el archivo de migración en $MigrationFile" -ForegroundColor Red
    exit 1
}

Write-Host "📄 Archivo de migración: $MigrationFile" -ForegroundColor Green
Write-Host "🗄️  Base de datos: $Database" -ForegroundColor Green
Write-Host ""

# Intentar ejecutar con sqlcmd
Write-Host "Ejecutando migración..." -ForegroundColor Yellow

try {
    # Construir el comando sqlcmd
    $sqlcmdPath = "sqlcmd"
    
    # Verificar si sqlcmd está disponible
    $sqlcmdExists = Get-Command sqlcmd -ErrorAction SilentlyContinue
    
    if (-not $sqlcmdExists) {
        Write-Host "❌ Error: sqlcmd no está instalado o no está en el PATH" -ForegroundColor Red
        Write-Host "Por favor instale SQL Server Command Line Utilities" -ForegroundColor Yellow
        exit 1
    }
    
    # Ejecutar la migración
    $result = & sqlcmd -S $Server -U $Username -P $PlainPassword -d $Database -i $MigrationFile 2>&1
    
    # Mostrar resultado
    Write-Host $result
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Migración aplicada exitosamente!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Tablas creadas:" -ForegroundColor Cyan
        Write-Host "  - Calificaciones" -ForegroundColor White
        Write-Host "  - ProductoStats" -ForegroundColor White
        Write-Host ""
        Write-Host "Triggers creados:" -ForegroundColor Cyan
        Write-Host "  - trg_calificaciones_after_insert" -ForegroundColor White
        Write-Host "  - trg_calificaciones_after_update" -ForegroundColor White
        Write-Host "  - trg_calificaciones_after_delete" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ Error al aplicar la migración. Revise los mensajes anteriores." -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Error durante la ejecución: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Sistema de calificaciones listo para usar" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor Yellow
Write-Host "  Reinicie el servidor backend para cargar los nuevos endpoints" -ForegroundColor White
Write-Host ""
