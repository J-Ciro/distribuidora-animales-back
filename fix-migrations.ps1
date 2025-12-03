# ========================================
# Script de Corrección de Migraciones SQL
# Soft PetPlace
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CORRECCION DE ARCHIVOS SQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# ============================================
# 1. Corregir CRLF en init-db.sh
# ============================================

Write-Host "[1/3] Corrigiendo line endings en init-db.sh..." -ForegroundColor Yellow

$initDbPath = "sql\init-db.sh"
if (Test-Path $initDbPath) {
    $content = Get-Content $initDbPath -Raw
    
    # Detectar tipo de line ending actual
    if ($content -match "`r`n") {
        Write-Host "  [INFO] Detectado CRLF (Windows)" -ForegroundColor Gray
        $contentLF = $content -replace "`r`n", "`n"
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($contentLF)
        [System.IO.File]::WriteAllBytes((Resolve-Path $initDbPath).Path, $bytes)
        Write-Host "  [OK] Convertido a LF (Unix)" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Ya tiene LF (Unix)" -ForegroundColor Green
    }
} else {
    Write-Host "  [ERROR] No se encontro $initDbPath" -ForegroundColor Red
}

Write-Host ""

# ============================================
# 2. Renombrar Migraciones Duplicadas
# ============================================

Write-Host "[2/3] Renombrando migraciones duplicadas..." -ForegroundColor Yellow

$migrationsPath = "sql\migrations"

# Mapeo de renombres
$renames = @{
    "002_add_user_columns.sql" = "003_add_user_columns.sql"
    "002_create_carts_cartitems.sql" = "004_create_carts_cartitems.sql"
    "002_update_categorias_subcategorias.sql" = "005_update_categorias_subcategorias.sql"
    "003_add_on_delete_cascade_producto_subcategoria.sql" = "006_add_on_delete_cascade.sql"
    "003_normalize_cart_columns.sql" = "007_normalize_cart_columns.sql"
    "004_add_metodo_pago_to_pedidos.sql" = "008_add_metodo_pago_to_pedidos.sql"
    "005_add_location_fields_to_pedidos.sql" = "009_add_location_fields_to_pedidos.sql"
}

foreach ($oldName in $renames.Keys) {
    $newName = $renames[$oldName]
    $oldPath = Join-Path $migrationsPath $oldName
    $newPath = Join-Path $migrationsPath $newName
    
    if (Test-Path $oldPath) {
        if (Test-Path $newPath) {
            Write-Host "  [SKIP] $newName ya existe" -ForegroundColor Yellow
        } else {
            Rename-Item $oldPath $newName
            Write-Host "  [OK] $oldName -> $newName" -ForegroundColor Green
        }
    }
}

Write-Host ""

# ============================================
# 3. Limpiar Seeders Duplicados
# ============================================

Write-Host "[3/3] Limpiando seeders duplicados..." -ForegroundColor Yellow

$seedersPath = "sql\seeders"

# Verificar si existe el archivo antiguo
$oldSeeder = Join-Path $seedersPath "002_sample_products.sql"
$fixedSeeder = Join-Path $seedersPath "002_sample_products_fixed.sql"

if ((Test-Path $oldSeeder) -and (Test-Path $fixedSeeder)) {
    # Comparar tamaños para decidir cuál eliminar
    $oldSize = (Get-Item $oldSeeder).Length
    $fixedSize = (Get-Item $fixedSeeder).Length
    
    Write-Host "  [INFO] Encontrados 2 seeders de productos:" -ForegroundColor Gray
    Write-Host "    002_sample_products.sql       ($oldSize bytes)" -ForegroundColor Gray
    Write-Host "    002_sample_products_fixed.sql ($fixedSize bytes)" -ForegroundColor Gray
    
    if ($fixedSize -gt $oldSize) {
        Remove-Item $oldSeeder
        Rename-Item $fixedSeeder "002_sample_products.sql"
        Write-Host "  [OK] Usando version 'fixed' (mas grande)" -ForegroundColor Green
    } else {
        Remove-Item $fixedSeeder
        Write-Host "  [OK] Manteniendo version original" -ForegroundColor Green
    }
} elseif (Test-Path $fixedSeeder) {
    Rename-Item $fixedSeeder "002_sample_products.sql"
    Write-Host "  [OK] Renombrado 002_sample_products_fixed.sql" -ForegroundColor Green
} else {
    Write-Host "  [OK] No hay seeders duplicados" -ForegroundColor Green
}

Write-Host ""

# ============================================
# 4. Resumen Final
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CORRECCION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Listar migraciones en orden
Write-Host "Migraciones (en orden):" -ForegroundColor White
Get-ChildItem -Path $migrationsPath -Filter "*.sql" | Sort-Object Name | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor Cyan
}

Write-Host ""

# Listar seeders
Write-Host "Seeders:" -ForegroundColor White
Get-ChildItem -Path $seedersPath -Filter "*.sql" | Sort-Object Name | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Ahora puedes ejecutar:" -ForegroundColor White
Write-Host "  .\setup.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Enter para continuar..." -ForegroundColor Gray
Read-Host
