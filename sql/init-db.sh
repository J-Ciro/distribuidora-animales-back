#!/bin/bash

set -e
set -o pipefail
set -x # Muestra cada comando ejecutado

DB_SERVER="sqlserver"
DB_USER="SA"
DB_PASSWORD="yourStrongPassword123#" # Debe coincidir con docker-compose.yml
DB_NAME="distribuidora_db" # Añadimos el nombre de la base de datos para futuras referencias

# --- INICIO DEPURACIÓN ---
# Esperar a que SQL Server esté listo
echo "Waiting for SQL Server to be ready..."

# Mantenemos los reintentos a 30 (150 segundos) para manejar el arranque lento de SQL Server.
MAX_RETRIES=30
ATTEMPT=0

# NOTA IMPORTANTE: Hemos cambiado la ruta de /opt/mssql-tools18/bin/sqlcmd a /opt/mssql-tools/bin/sqlcmd
# para corregir el error "No such file or directory" reportado en el log.
until /opt/mssql-tools/bin/sqlcmd -S $DB_SERVER -U $DB_USER -P $DB_PASSWORD -Q "SELECT 1" > /dev/null 2> connection_error.log
do
    ATTEMPT=$((ATTEMPT + 1))
    
    if [ $ATTEMPT -ge $MAX_RETRIES ]; then
        echo "--- ERROR FATAL DE CONEXIÓN ---"
        cat connection_error.log # Muestra el error de sqlcmd (si existe)
        echo "El servidor SQL no respondió después de $MAX_RETRIES intentos. La inicialización ha fallado por timeout."
        echo "VERIFIQUE: 1. Los límites de memoria/CPU en docker-compose. 2. Los logs del contenedor 'sqlserver' para ver si está en recuperación."
        exit 1
    fi
    
    echo "SQL Server not ready yet (Attempt $ATTEMPT/$MAX_RETRIES). Waiting 5 seconds..."
    sleep 5
done

echo "SQL Server is ready."
# --- FIN DEPURACIÓN ---

# Crear la base de datos si no existe. Usamos -d master para asegurar el contexto.
echo "Ensuring database $DB_NAME exists..."
/opt/mssql-tools/bin/sqlcmd -S $DB_SERVER -U $DB_USER -P $DB_PASSWORD -d master -Q "IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];" -o /dev/stdout

# Aplicar schema
if [ -f /docker-entrypoint-initdb.d/schema.sql ]; then
    echo "Applying schema..."
    # Usamos -d para apuntar a la base de datos de destino
    /opt/mssql-tools/bin/sqlcmd -S $DB_SERVER -U $DB_USER -P $DB_PASSWORD -d $DB_NAME -i /docker-entrypoint-initdb.d/schema.sql -o /dev/stdout
else
    echo "No schema.sql found, skipping schema step."
fi

# Aplicar migraciones
if [ -d /docker-entrypoint-initdb.d/migrations ]; then
    echo "Applying migrations..."
    for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
        [ -e "$f" ] || continue # Salta si no hay archivos
        echo "Applying migration $f"
        /opt/mssql-tools/bin/sqlcmd -S $DB_SERVER -U $DB_USER -P $DB_PASSWORD -d $DB_NAME -i "$f" -o /dev/stdout
    done
else
    echo "No migrations folder found, skipping migrations."
fi

# Aplicar seeders
if [ -d /docker-entrypoint-initdb.d/seeders ]; then
    echo "Applying seeders..."
    for f in /docker-entrypoint-initdb.d/seeders/*.sql; do
        [ -e "$f" ] || continue
        echo "Applying seeder $f"
        /opt/mssql-tools/bin/sqlcmd -S $DB_SERVER -U $DB_USER -P $DB_PASSWORD -d $DB_NAME -i "$f" -o /dev/stdout
    done
else
    echo "No seeders folder found, skipping seeders."
fi

echo "Database initialization complete."