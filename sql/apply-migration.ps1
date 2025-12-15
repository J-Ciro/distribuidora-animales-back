# PowerShell script to apply migration to SQL Server

$DbServer = "localhost"
$DbUser = "sa"
$DbPassword = "YourStrongPassword123!"
$DbName = "distribuidora_db"

# Path to the migration file
$MigrationFile = "c:\Users\juan.ciro\Documents\Taller-11\distribuidora-animales-back\sql\migrations\011_add_missing_usuario_columns.sql"

Write-Host "===================================="
Write-Host "Applying Migration: 011_add_missing_usuario_columns.sql"
Write-Host "===================================="
Write-Host "Server: $DbServer"
Write-Host "Database: $DbName"
Write-Host "===================================="

# Load the migration SQL
try {
    $SqlScript = Get-Content -Path $MigrationFile -Raw
    Write-Host "Migration file loaded successfully"
}
catch {
    Write-Host "Error loading migration file: $_"
    exit 1
}

# Try to execute the migration
try {
    # Use sqlcmd
    $SqlCmdPath = "sqlcmd"
    
    # Create a temporary file with the SQL script
    $TempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.sql'
    Set-Content -Path $TempFile -Value $SqlScript
    
    Write-Host "Executing migration..."
    & $SqlCmdPath -S $DbServer -U $DbUser -P $DbPassword -d $DbName -i $TempFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Migration applied successfully!"
    }
    else {
        Write-Host "Migration failed with exit code: $LASTEXITCODE"
        Remove-Item -Path $TempFile -Force -ErrorAction SilentlyContinue
        exit 1
    }
    
    # Clean up temp file
    Remove-Item -Path $TempFile -Force -ErrorAction SilentlyContinue
}
catch {
    Write-Host "Error executing migration: $_"
    exit 1
}

Write-Host "===================================="
Write-Host "Migration completed successfully!"
Write-Host "===================================="

