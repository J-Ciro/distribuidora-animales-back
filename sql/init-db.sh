#!/bin/bash

set -e
set -u
set -x

DB_SERVER="${DB_SERVER:-sqlserver}"
DB_USER="SA"
<<<<<<< HEAD
DB_PASSWORD="yourStrongPassword123#"
DB_NAME="distribuidora_db"
=======
DB_PASSWORD="${SA_PASSWORD:-yourStrongPassword123#}"
DB_NAME="${DB_NAME:-distribuidora_db}"

echo "=================================="
echo "Database Migration System v2.0"
echo "=================================="
echo "Server: $DB_SERVER"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "=================================="
>>>>>>> 125b786d3b1dd8f99495e4149cf969ee3116670b

echo "Waiting for SQL Server to be ready..."

<<<<<<< HEAD
MAX_RETRIES=30
ATTEMPT=0

until /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" > /dev/null 2> connection_error.log
=======
# Incrementamos a 60 intentos (300 segundos = 5 minutos) para asegurar que SQL Server arranque completamente
# SQL Server en Docker puede tardar 2-3 minutos en estar completamente listo
MAX_RETRIES=60
RETRY_INTERVAL=5
ATTEMPT=0

# Intentar verificar conectividad con sqlcmd
until /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" > /dev/null 2>&1
>>>>>>> 125b786d3b1dd8f99495e4149cf969ee3116670b
do
    ATTEMPT=$((ATTEMPT + 1))

    if [ "$ATTEMPT" -ge "$MAX_RETRIES" ]; then
<<<<<<< HEAD
        echo "--- ERROR FATAL DE CONEXION ---"
        cat connection_error.log || true
        echo "El servidor SQL no respondio despues de $MAX_RETRIES intentos."
=======
        echo "=================================="
        echo "âŒ ERROR FATAL DE CONEXIÃ“N"
        echo "=================================="
        echo "El servidor SQL no respondiÃ³ despuÃ©s de $MAX_RETRIES intentos ($((MAX_RETRIES * RETRY_INTERVAL)) segundos)."
        echo ""
        echo "PASOS PARA DIAGNOSTICAR:"
        echo "1. Verificar logs del contenedor SQL Server:"
        echo "   docker logs sqlserver"
        echo ""
        echo "2. Verificar que SQL Server tenga suficiente memoria:"
        echo "   docker stats sqlserver"
        echo ""
        echo "3. Intentar conexiÃ³n manual:"
        echo "   docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#'"
        echo ""
        echo "4. Revisar healthcheck de SQL Server:"
        echo "   docker inspect sqlserver | grep -A 10 Health"
        echo "=================================="
>>>>>>> 125b786d3b1dd8f99495e4149cf969ee3116670b
        exit 1
    fi

    echo "â³ SQL Server not ready yet (Attempt $ATTEMPT/$MAX_RETRIES). Waiting $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
done

echo "âœ… SQL Server is ready and accepting connections!"
echo ""

<<<<<<< HEAD
echo "Ensuring database $DB_NAME exists..."
/opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d master -Q "IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];" -o /dev/stdout
=======
# Crear la base de datos si no existe
echo "ðŸ“¦ Ensuring database '$DB_NAME' exists..."
/opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d master \
    -Q "IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];" \
    || { echo "âŒ Failed to create database"; exit 1; }
echo "âœ… Database '$DB_NAME' is ready"
echo ""
>>>>>>> 125b786d3b1dd8f99495e4149cf969ee3116670b

if [ -f /docker-entrypoint-initdb.d/schema.sql ]; then
    echo "ðŸ“‹ Applying schema..."
    /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
        -i /docker-entrypoint-initdb.d/schema.sql \
        || { echo "âŒ Schema application failed"; exit 1; }
    echo "âœ… Schema applied successfully"
    echo ""
else
    echo "âš ï¸  No schema.sql found, skipping schema step."
    echo ""
fi

if [ -d /docker-entrypoint-initdb.d/migrations ]; then
    echo "ðŸ”„ Applying migrations..."
    MIGRATION_COUNT=0
    for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
        [ -e "$f" ] || continue
        MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
        echo "  ðŸ“„ Applying migration: $(basename "$f")"
        /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
            -i "$f" \
            || { echo "âŒ Migration failed: $f"; exit 1; }
    done
    echo "âœ… Applied $MIGRATION_COUNT migration(s) successfully"
    echo ""
else
    echo "âš ï¸  No migrations folder found, skipping migrations."
    echo ""
fi

if [ -d /docker-entrypoint-initdb.d/seeders ]; then
    echo "ðŸŒ± Applying seeders..."
    SEEDER_COUNT=0
    for f in /docker-entrypoint-initdb.d/seeders/*.sql; do
        [ -e "$f" ] || continue
        SEEDER_COUNT=$((SEEDER_COUNT + 1))
        echo "  ðŸ“„ Applying seeder: $(basename "$f")"
        /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
            -i "$f" \
            || { echo "âŒ Seeder failed: $f"; exit 1; }
    done
    echo "âœ… Applied $SEEDER_COUNT seeder(s) successfully"
    echo ""
else
    echo "âš ï¸  No seeders folder found, skipping seeders."
    echo ""
fi

<<<<<<< HEAD
echo "Database initialization complete."
=======
echo "=================================="
echo "âœ… Database initialization complete!"
echo "=================================="
echo "Database: $DB_NAME"
echo "Status: All migrations and seeders applied successfully"
echo "=================================="
>>>>>>> 125b786d3b1dd8f99495e4149cf969ee3116670b
