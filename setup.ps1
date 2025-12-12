# ========================================
# Script de Configuración Automática - Backend
# Soft PetPlace
# ========================================

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACION AUTOMATICA - BACKEND" -ForegroundColor Cyan
Write-Host "  Soft PetPlace" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PASO 1: Verificar Prerequisitos
# ============================================

Write-Host "[1/8] Verificando prerequisitos..." -ForegroundColor Yellow
Write-Host ""

# Verificar Docker
try {
    $dockerVersion = podman --version
    Write-Host "  [OK] Docker instalado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker no esta instalado" -ForegroundColor Red
    Write-Host "  Descarga Docker Desktop desde: https://www.podman.com/products/podman-desktop" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que Docker esté corriendo
try {
    podman ps | Out-Null
    Write-Host "  [OK] Docker esta corriendo" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker no esta corriendo" -ForegroundColor Red
    Write-Host "  Por favor, inicia Docker Desktop y vuelve a ejecutar este script" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar podman
try {
    $composeVersion = podman --version
    Write-Host "  [OK] Docker Compose instalado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker Compose no esta instalado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================
# PASO 2: Limpiar Instalación Anterior
# ============================================

Write-Host "[2/8] Limpiando instalacion anterior (si existe)..." -ForegroundColor Yellow

# Detener y eliminar contenedores
podman down -v 2>$null | Out-Null

# Limpiar contenedores específicos que pueden quedar huérfanos
$containersToClean = @(
    "distribuidora-sqlserver",
    "distribuidora-api", 
    "distribuidora-worker",
    "distribuidora-rabbitmq",
    "distribuidora-db-migrator",
    "sqlserver"
)

foreach ($containerName in $containersToClean) {
    $exists = podman ps -a --filter "name=$containerName" --format "{{.Names}}" 2>$null
    if ($exists) {
        Write-Host "  Eliminando contenedor: $containerName" -ForegroundColor Gray
        podman rm -f $containerName 2>$null | Out-Null
    }
}

Write-Host "  [OK] Limpieza completada" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 3: Configurar Archivos .env
# ============================================

Write-Host "[3/8] Configurando archivos de entorno..." -ForegroundColor Yellow
Write-Host ""

# Verificar y crear backend/api/.env
if (Test-Path "backend/api/.env.example") {
    if (Test-Path "backend/api/.env") {
        Write-Host "  [INFO] backend/api/.env ya existe" -ForegroundColor Blue
        $overwrite = Read-Host "  Deseas sobrescribirlo? (s/n)"
        if ($overwrite -eq "s" -or $overwrite -eq "S") {
            Copy-Item "backend/api/.env.example" "backend/api/.env" -Force
            Write-Host "  [OK] backend/api/.env actualizado" -ForegroundColor Green
        }
    } else {
        Copy-Item "backend/api/.env.example" "backend/api/.env"
        Write-Host "  [OK] Creado backend/api/.env" -ForegroundColor Green
    }
} else {
    Write-Host "  [ERROR] No se encontro backend/api/.env.example" -ForegroundColor Red
    exit 1
}

# Verificar y crear backend/worker/.env
if (Test-Path "backend/worker/.env.example") {
    if (Test-Path "backend/worker/.env") {
        Write-Host "  [INFO] backend/worker/.env ya existe" -ForegroundColor Blue
    } else {
        Copy-Item "backend/worker/.env.example" "backend/worker/.env"
        Write-Host "  [OK] Creado backend/worker/.env" -ForegroundColor Green
    }
} else {
    Write-Host "  [ERROR] No se encontro backend/worker/.env.example" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================
# PASO 4: Configuración de Email (Opcional)
# ============================================

Write-Host "[4/8] Configuracion de Email..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Para que funcione el envio de emails de verificacion," -ForegroundColor Gray
Write-Host "  necesitas configurar una cuenta de Gmail con una contrasena de aplicacion." -ForegroundColor Gray
Write-Host ""
Write-Host "  Puedes omitir esto ahora y configurarlo despues en:" -ForegroundColor Gray
Write-Host "    backend/api/.env" -ForegroundColor Cyan
Write-Host "    backend/worker/.env" -ForegroundColor Cyan
Write-Host ""

$configureEmail = Read-Host "  Deseas configurar el email ahora? (s/n)"

if ($configureEmail -eq "s" -or $configureEmail -eq "S") {
    Write-Host ""
    Write-Host "  Instrucciones para obtener contrasena de aplicacion de Gmail:" -ForegroundColor Yellow
    Write-Host "    1. Ve a https://myaccount.google.com/security" -ForegroundColor Gray
    Write-Host "    2. Activa la verificacion en 2 pasos" -ForegroundColor Gray
    Write-Host "    3. Busca 'Contrasenas de aplicaciones'" -ForegroundColor Gray
    Write-Host "    4. Genera una nueva contrasena para 'Correo'" -ForegroundColor Gray
    Write-Host ""
    
    $smtpUser = Read-Host "  Email de Gmail (ejemplo: tucorreo@gmail.com)"
    Write-Host "  Contrasena de aplicacion (16 caracteres sin espacios):" -NoNewline
    $smtpPassword = Read-Host -AsSecureString
    $smtpPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtpPassword))
    
    # Validar formato de email
    if ($smtpUser -notmatch "^[\w-\.]+@gmail\.com$") {
        Write-Host "  [ADVERTENCIA] El email no parece ser de Gmail" -ForegroundColor Yellow
    }
    
    # Actualizar backend/api/.env
    $envContent = Get-Content "backend/api/.env" -Raw
    $envContent = $envContent -replace 'SMTP_USER=.*', "SMTP_USER=$smtpUser"
    $envContent = $envContent -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$smtpPasswordPlain"
    $envContent = $envContent -replace 'EMAIL_FROM_ADDRESS=.*', "EMAIL_FROM_ADDRESS=$smtpUser"
    $envContent | Set-Content "backend/api/.env" -NoNewline
    
    # Actualizar backend/worker/.env
    $envContentWorker = Get-Content "backend/worker/.env" -Raw
    $envContentWorker = $envContentWorker -replace 'SMTP_USER=.*', "SMTP_USER=$smtpUser"
    $envContentWorker = $envContentWorker -replace 'SMTP_PASSWORD=.*', "SMTP_PASSWORD=$smtpPasswordPlain"
    $envContentWorker = $envContentWorker -replace 'SMTP_PASS=.*', "SMTP_PASS=$smtpPasswordPlain"
    $envContentWorker = $envContentWorker -replace 'EMAIL_FROM_ADDRESS=.*', "EMAIL_FROM_ADDRESS=$smtpUser"
    $envContentWorker | Set-Content "backend/worker/.env" -NoNewline
    
    Write-Host "  [OK] Email configurado correctamente" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Email no configurado. Puedes hacerlo despues." -ForegroundColor Blue
}

Write-Host ""

# ============================================
# PASO 5: Validar Archivos SQL
# ============================================

Write-Host "[5/8] Validando archivos de migracion..." -ForegroundColor Yellow

$requiredFiles = @(
    "sql/schema.sql",
    "sql/init-db.sh"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] Encontrado: $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Falta: $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "  [ERROR] Faltan archivos necesarios para la migracion" -ForegroundColor Red
    exit 1
}

# Contar migraciones
$migrationCount = (Get-ChildItem -Path "sql/migrations" -Filter "*.sql" -ErrorAction SilentlyContinue | Measure-Object).Count
$seederCount = (Get-ChildItem -Path "sql/seeders" -Filter "*.sql" -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host "  [INFO] Se aplicaran $migrationCount migraciones y $seederCount seeders" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PASO 6: Construir e Iniciar Contenedores
# ============================================

Write-Host "[6/8] Construyendo e iniciando contenedores..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Esto puede tomar 3-5 minutos la primera vez..." -ForegroundColor Gray
Write-Host "  - SQL Server tardara ~120 segundos en estar listo" -ForegroundColor Gray
Write-Host "  - Las migraciones se aplicaran automaticamente" -ForegroundColor Gray
Write-Host "  - El API iniciara despues de las migraciones" -ForegroundColor Gray
Write-Host ""

# Iniciar servicios
Write-Host "  Iniciando servicios..." -ForegroundColor Cyan
podman compose up -d --build

Write-Host "  [OK] Contenedores iniciados" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 7: Esperar y Verificar Servicios
# ============================================

Write-Host "[7/8] Esperando a que los servicios esten listos..." -ForegroundColor Yellow
Write-Host ""

# Esperar SQL Server
Write-Host "  [1/4] Esperando SQL Server..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

$sqlReady = $false
$attempts = 0
$maxAttempts = 24

while (-not $sqlReady -and $attempts -lt $maxAttempts) {
    $attempts++
    try {
        $healthCheck = podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -Q "SELECT 1" 2>&1
        if ($healthCheck -match "1" -or $healthCheck -match "affected") {
            $sqlReady = $true
            Write-Host "  [OK] SQL Server listo (intento $attempts/$maxAttempts)" -ForegroundColor Green
        } else {
            Write-Host "  [.] SQL Server iniciando... (intento $attempts/$maxAttempts)" -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    } catch {
        Write-Host "  [.] SQL Server iniciando... (intento $attempts/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $sqlReady) {
    Write-Host "  [ERROR] SQL Server no respondio a tiempo" -ForegroundColor Red
    Write-Host "  Verifica los logs: podman logs sqlserver" -ForegroundColor Yellow
}

Write-Host ""

# Esperar db-migrator
Write-Host "  [2/4] Esperando migracion de base de datos..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

$migratorStatus = podman ps -a --filter "name=distribuidora-db-migrator" --format "{{.Status}}" 2>$null
if ($migratorStatus -match "Exited \(0\)") {
    Write-Host "  [OK] Migraciones aplicadas exitosamente" -ForegroundColor Green
} else {
    Write-Host "  [ADVERTENCIA] Migrator status: $migratorStatus" -ForegroundColor Yellow
    Write-Host "  Ver logs: podman logs distribuidora-db-migrator" -ForegroundColor Gray
}

Write-Host ""

# Esperar API
Write-Host "  [3/4] Esperando API..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

$apiReady = $false
$attempts = 0
$maxAttempts = 12

while (-not $apiReady -and $attempts -lt $maxAttempts) {
    $attempts++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 3 2>$null
        if ($response.StatusCode -eq 200) {
            $apiReady = $true
            Write-Host "  [OK] API lista (intento $attempts/$maxAttempts)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [.] API iniciando... (intento $attempts/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $apiReady) {
    Write-Host "  [ADVERTENCIA] API no responde aun (puede tardar unos segundos mas)" -ForegroundColor Yellow
}

Write-Host ""

# Esperar Worker
Write-Host "  [4/4] Verificando Worker..." -ForegroundColor Cyan
$workerStatus = podman inspect distribuidora-worker --format='{{.State.Status}}' 2>$null
if ($workerStatus -eq "running") {
    Write-Host "  [OK] Worker corriendo" -ForegroundColor Green
} else {
    Write-Host "  [ADVERTENCIA] Worker no esta corriendo: $workerStatus" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# PASO 8: Verificación Final
# ============================================

Write-Host "[8/8] Verificacion final del sistema..." -ForegroundColor Yellow
Write-Host ""

# Listar contenedores
Write-Host "  Estado de contenedores:" -ForegroundColor Cyan
$containers = podman ps -a --filter "name=distribuidora-" --format "table {{.Names}}\t{{.Status}}" 2>$null
if ($containers) {
    $containers | ForEach-Object {
        if ($_ -match "Up") {
            Write-Host "    $_" -ForegroundColor Green
        } elseif ($_ -match "Exited \(0\)") {
            Write-Host "    $_" -ForegroundColor Green
        } else {
            Write-Host "    $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [ERROR] No se encontraron contenedores" -ForegroundColor Red
}

Write-Host ""

# Verificar tablas de calificaciones
Write-Host "  Verificando sistema de calificaciones..." -ForegroundColor Cyan
try {
    $tablesCheck = podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT name FROM sys.tables WHERE name IN ('Calificaciones', 'ProductoStats')" -h -1 2>&1
    
    if ($tablesCheck -match "Calificaciones" -and $tablesCheck -match "ProductoStats") {
        Write-Host "  [OK] Tablas de calificaciones creadas correctamente" -ForegroundColor Green
    } else {
        Write-Host "  [ADVERTENCIA] Verificar tablas de calificaciones" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ADVERTENCIA] No se pudo verificar las tablas" -ForegroundColor Yellow
}

Write-Host ""

# Crear usuario Administrador
Write-Host "  Creando usuario Administrador..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Ingresa los datos del usuario administrador:" -ForegroundColor Yellow
$adminEmail = Read-Host "    Email del administrador"
$adminPassword = Read-Host "    Contrasena del administrador" -AsSecureString
$adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword))

# Validar email
if ($adminEmail -notmatch "^[\w\.-]+@[\w\.-]+\.\w+$") {
    Write-Host "  [ADVERTENCIA] El formato del email puede no ser valido" -ForegroundColor Yellow
}

# Validar contraseña mínima
if ($adminPasswordPlain.Length -lt 6) {
    Write-Host "  [ADVERTENCIA] La contrasena deberia tener al menos 6 caracteres" -ForegroundColor Yellow
}

try {
    # Crear usuario via API
    $registerBody = @{
        email = $adminEmail
        password = $adminPasswordPlain
        nombre = "Administrador"
        apellido = "Sistema"
        telefono = "0000000000"
    } | ConvertTo-Json

    $registerResponse = Invoke-WebRequest `
        -Uri "http://localhost:8000/api/auth/register" `
        -Method POST `
        -ContentType "application/json" `
        -Body $registerBody `
        -UseBasicParsing `
        -TimeoutSec 10 2>$null

    if ($registerResponse.StatusCode -eq 200 -or $registerResponse.StatusCode -eq 201) {
        $responseData = $registerResponse.Content | ConvertFrom-Json
        $userId = $responseData.id
        
        Write-Host "  [OK] Usuario creado con ID: $userId" -ForegroundColor Green
        
        # Marcar email como verificado y asignar rol Admin
        $updateQuery = "UPDATE Usuarios SET email_verificado=1, rol='Admin' WHERE id=$userId"
        podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "$updateQuery" 2>&1 | Out-Null
        
        Write-Host "  [OK] Usuario configurado como Administrador" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Credenciales del administrador:" -ForegroundColor Cyan
        Write-Host "    Email:     $adminEmail" -ForegroundColor White
        Write-Host "    Rol:       Admin" -ForegroundColor White
        Write-Host "    Verificado: Si" -ForegroundColor White
    } else {
        Write-Host "  [ADVERTENCIA] Respuesta inesperada del API: $($registerResponse.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] No se pudo crear el usuario administrador" -ForegroundColor Red
    Write-Host "  Puedes crearlo manualmente despues desde http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host ""

# ============================================
# RESUMEN FINAL
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor White
Write-Host "  API (FastAPI):       http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Documentacion:       http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  RabbitMQ UI:         http://localhost:15672 (guest/guest)" -ForegroundColor Cyan
Write-Host "  SQL Server:          localhost:1433 (sa/yourStrongPassword123#)" -ForegroundColor Cyan
Write-Host ""

if ($configureEmail -ne "s" -and $configureEmail -ne "S") {
    Write-Host "[!] RECORDATORIO: Email no configurado" -ForegroundColor Yellow
    Write-Host "    Edita backend/api/.env y backend/worker/.env" -ForegroundColor Yellow
    Write-Host "    para habilitar el envio de codigos de verificacion." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Comandos utiles:" -ForegroundColor White
Write-Host "  Ver logs del API:      podman logs -f distribuidora-api" -ForegroundColor Gray
Write-Host "  Ver logs de SQL:       podman logs -f sqlserver" -ForegroundColor Gray
Write-Host "  Ver logs del Worker:   podman logs -f distribuidora-worker" -ForegroundColor Gray
Write-Host "  Ver logs de Migrator:  podman logs distribuidora-db-migrator" -ForegroundColor Gray
Write-Host "  Ver todos los logs:    podman logs -f" -ForegroundColor Gray
Write-Host "  Reiniciar servicios:   podman restart" -ForegroundColor Gray
Write-Host "  Detener servicios:     podman down" -ForegroundColor Gray
Write-Host ""

Write-Host "Verificacion rapida:" -ForegroundColor White
Write-Host "  Abre http://localhost:8000/docs para ver la documentacion del API" -ForegroundColor Gray
Write-Host ""

# Abrir navegador automáticamente
$openBrowser = Read-Host "Deseas abrir la documentacion del API en el navegador? (s/n)"
if ($openBrowser -eq "s" -or $openBrowser -eq "S") {
    Start-Process "http://localhost:8000/docs"
}

Write-Host ""
Write-Host "Presiona Enter para finalizar..." -ForegroundColor Cyan
Read-Host
