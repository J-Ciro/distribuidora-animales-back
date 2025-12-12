# Script de Limpieza de Archivos Obsoletos
# Elimina archivos redundantes y crea backup

param(
    [switch]$DryRun = $false,
    [switch]$NoBackup = $false
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "  Limpieza de Archivos Obsoletos - Backend" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Crear timestamp para backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "..\backup_cleanup_$timestamp"

if (-not $NoBackup) {
    Write-Host "Creando backup en: $backupDir" -ForegroundColor Yellow
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Write-Host "   Directorio de backup creado`n" -ForegroundColor Green
    }
    else {
        Write-Host "   [DRY RUN] Backup se crearía en: $backupDir`n" -ForegroundColor Gray
    }
}

# Archivos .md a eliminar (raiz del backend)
$mdFilesToDelete = @(
    "RESUMEN_ORIGINAL.md",
    "RESUMEN_HISTORIAS_USUARIO.md",
    "RESUMEN_IMPLEMENTACION_PRUEBAS.md",
    "COMO_OBTENER_CODIGO_VERIFICACION.md",
    "taskipy.instructions.md"
)

# Scripts .ps1 a eliminar
$ps1FilesToDelete = @(
    "run-tests.ps1",
    "setup-email.ps1",
    "verify-migration.ps1"
)

# Archivos .md en subdirectorios a eliminar
$nestedMdFilesToDelete = @(
    "backend/api/IMPLEMENTACION_HU_REGISTER_USER.md",
    "backend/api/README_INICIO.md",
    "backend/api/app/services/README.md",
    "backend/api/app/middleware/README.md"
)

# Contador de archivos eliminados
$totalDeleted = 0
$totalBackedUp = 0

Write-Host "ARCHIVOS .md A ELIMINAR (RAIZ):" -ForegroundColor Yellow
Write-Host "───────────────────────────────" -ForegroundColor Yellow
foreach ($file in $mdFilesToDelete) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] $file" -ForegroundColor Gray
        }
        else {
            if (-not $NoBackup) {
                Copy-Item $file -Destination $backupDir | Out-Null
                $totalBackedUp++
            }
            Remove-Item $file -Force | Out-Null
            Write-Host "  Eliminado: $file" -ForegroundColor Green
            $totalDeleted++
        }
    }
    else {
        Write-Host "  No existe: $file" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "SCRIPTS .ps1 A ELIMINAR:" -ForegroundColor Yellow
Write-Host "───────────────────────" -ForegroundColor Yellow
foreach ($file in $ps1FilesToDelete) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] $file" -ForegroundColor Gray
        }
        else {
            if (-not $NoBackup) {
                Copy-Item $file -Destination $backupDir | Out-Null
                $totalBackedUp++
            }
            Remove-Item $file -Force | Out-Null
            Write-Host "  Eliminado: $file" -ForegroundColor Green
            $totalDeleted++
        }
    }
    else {
        Write-Host "  No existe: $file" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "ARCHIVOS .md EN SUBDIRECTORIOS A ELIMINAR:" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────" -ForegroundColor Yellow
foreach ($file in $nestedMdFilesToDelete) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] $file" -ForegroundColor Gray
        }
        else {
            if (-not $NoBackup) {
                $dir = Split-Path $file -Parent
                New-Item -ItemType Directory -Path "$backupDir/$dir" -Force -ErrorAction SilentlyContinue | Out-Null
                Copy-Item $file -Destination "$backupDir/$file" -Force | Out-Null
                $totalBackedUp++
            }
            Remove-Item $file -Force | Out-Null
            Write-Host "  Eliminado: $file" -ForegroundColor Green
            $totalDeleted++
        }
    }
    else {
        Write-Host "  No existe: $file" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  [DRY RUN] - Sin cambios realizados" -ForegroundColor Yellow
    Write-Host "  Para aplicar cambios, ejecuta sin -DryRun" -ForegroundColor White
}
else {
    Write-Host "  Limpieza completada" -ForegroundColor Green
    Write-Host "  Archivos eliminados: $totalDeleted" -ForegroundColor Green
    if (-not $NoBackup) {
        Write-Host "  Archivos respaldados: $totalBackedUp" -ForegroundColor Green
        Write-Host "  Backup en: $backupDir" -ForegroundColor Cyan
    }
}
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
