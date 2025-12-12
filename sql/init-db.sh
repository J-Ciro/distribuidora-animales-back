#!/bin/bash

set -euo pipefail
set -x # Muestra cada comando ejecutado

DB_SERVER="${DB_SERVER:-sqlserver}"
DB_USER="SA"
DB_PASSWORD="${SA_PASSWORD:-yourStrongPassword123#}"
DB_NAME="${DB_NAME:-distribuidora_db}"

echo "=================================="
echo "Database Migration System v2.0"
echo "=================================="
echo "Server: $DB_SERVER"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "=================================="

# Esperar a que SQL Server esté listo
echo "Waiting for SQL Server to be ready..."

# Incrementamos a 60 intentos (300 segundos = 5 minutos) para asegurar que SQL Server arranque completamente
# SQL Server en Docker puede tardar 2-3 minutos en estar completamente listo
MAX_RETRIES=60
RETRY_INTERVAL=5
ATTEMPT=0

# Intentar verificar conectividad con sqlcmd
until /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -Q "SELECT 1" > /dev/null 2>&1
do
    ATTEMPT=$((ATTEMPT + 1))

    if [ "$ATTEMPT" -ge "$MAX_RETRIES" ]; then
        echo "=================================="
        echo "❌ ERROR FATAL DE CONEXIÓN"
        echo "=================================="
        echo "El servidor SQL no respondió después de $MAX_RETRIES intentos ($((MAX_RETRIES * RETRY_INTERVAL)) segundos)."
        echo ""
        echo "PASOS PARA DIAGNOSTICAR:"
        echo "1. Verificar logs del contenedor SQL Server:"
        echo "   docker logs sqlserver"
        echo ""
        echo "2. Verificar que SQL Server tenga suficiente memoria:"
        echo "   docker stats sqlserver"
        echo ""
        echo "3. Intentar conexión manual:"
        echo "   docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#'"
        echo ""
        echo "4. Revisar healthcheck de SQL Server:"
        echo "   docker inspect sqlserver | grep -A 10 Health"
        echo "=================================="
        exit 1
    fi

    echo "⏳ SQL Server not ready yet (Attempt $ATTEMPT/$MAX_RETRIES). Waiting $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
done

echo "✅ SQL Server is ready and accepting connections!"
echo ""

# Crear la base de datos si no existe
echo "📦 Ensuring database '$DB_NAME' exists..."
/opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d master \
    -Q "IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];" \
    || { echo "❌ Failed to create database"; exit 1; }
echo "✅ Database '$DB_NAME' is ready"
echo ""

# Aplicar schema
if [ -f /docker-entrypoint-initdb.d/schema.sql ]; then
    echo "📋 Applying schema..."
    /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
        -i /docker-entrypoint-initdb.d/schema.sql \
        || { echo "❌ Schema application failed"; exit 1; }
    echo "✅ Schema applied successfully"
    echo ""
else
    echo "⚠️  No schema.sql found, skipping schema step."
    echo ""
fi

# Aplicar migraciones
if [ -d /docker-entrypoint-initdb.d/migrations ]; then
    echo "🔄 Applying migrations..."
    MIGRATION_COUNT=0
    for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
        [ -e "$f" ] || continue
        MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
        echo "  📄 Applying migration: $(basename "$f")"
        /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
            -i "$f" \
            || { echo "❌ Migration failed: $f"; exit 1; }
    done
    echo "✅ Applied $MIGRATION_COUNT migration(s) successfully"
    echo ""
else
    echo "⚠️  No migrations folder found, skipping migrations."
    echo ""
fi

# Aplicar seeders
if [ -d /docker-entrypoint-initdb.d/seeders ]; then
    echo "🌱 Applying seeders..."
    SEEDER_COUNT=0
    for f in /docker-entrypoint-initdb.d/seeders/*.sql; do
        [ -e "$f" ] || continue
        SEEDER_COUNT=$((SEEDER_COUNT + 1))
        echo "  📄 Applying seeder: $(basename "$f")"
        /opt/mssql-tools/bin/sqlcmd -S "$DB_SERVER" -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" \
            -i "$f" \
            || { echo "❌ Seeder failed: $f"; exit 1; }
    done
    echo "✅ Applied $SEEDER_COUNT seeder(s) successfully"
    echo ""
else
    echo "⚠️  No seeders folder found, skipping seeders."
    echo ""
fi

echo "=================================="
echo "✅ Database initialization complete!"
echo "=================================="
echo "Database: $DB_NAME"
echo "Status: All migrations and seeders applied successfully"
echo "=================================="