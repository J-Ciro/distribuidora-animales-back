# 📚 Database Migration Guide

**Distribuidora Perros y Gatos** - Professional Database Migration System

---

## 🎯 Overview

This guide explains how to work with the professional database migration system for this project. The system is similar to **Flyway** and **Alembic**, providing:

- ✅ Deterministic ordering (001, 002, ... 010)
- ✅ Idempotent execution (safe to re-run)
- ✅ Transaction support (automatic rollback on error)
- ✅ Migration history tracking
- ✅ Exponential backoff for connection retries

---

## 🚀 Quick Start

### Setup

1. **Copy environment template**:
   ```bash
   cp backend/api/.env.example backend/api/.env
   ```

2. **Configure your environment** (optional - defaults are provided for local development):
   ```bash
   # Edit backend/api/.env with your values
   vim backend/api/.env
   ```

3. **Start all services** (migrations run automatically):
   ```bash
   docker-compose up
   ```

That's it! The system will:
1. Wait for SQL Server to be ready
2. Apply all pending migrations
3. Create the default admin user
4. Start the FastAPI API server

---

## 📋 Migration System Architecture

### Directory Structure

```
distribuidora-animales-back/
├── backend/api/
│   ├── app/
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── migrator.py          # Core migration engine
│   │   └── scripts/
│   │       ├── __init__.py
│   │       ├── migrate.py           # Executable migration script
│   │       └── seed_admin.py        # Admin user seeder
│   ├── entrypoint.sh                # Container initialization script
│   └── main.py
├── sql/
│   └── migrations/
│       ├── __0_init_migrations_table.sql
│       ├── 001_add_indexes.sql
│       ├── 002_add_metodo_pago.sql
│       ├── ... (003-010)
│       └── 010_create_ratings.sql
└── docker-compose.yml
```

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ docker-compose up                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Container Starts                                            │
│ ├─ Entrypoint: /app/entrypoint.sh                           │
│ │  ├─ STEP 1: python /app/app/scripts/migrate.py           │
│ │  │  └─ Runs migrator.py (applies pending migrations)     │
│ │  ├─ STEP 2: python /app/app/scripts/seed_admin.py        │
│ │  │  └─ Creates default admin if doesn't exist            │
│ │  └─ STEP 3: uvicorn main:app                             │
│ │     └─ Starts FastAPI API server                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Creating New Migrations

### Naming Convention

Migrations must follow this naming pattern:

```
NNN_descriptive_name.sql
```

Where:
- `NNN` = Sequential number (001, 002, ..., 010, 011, 012, etc.)
- Use the **next available number** after the last migration
- Use **snake_case** for the description

### Example Migrations

```
✅ CORRECT:
  - 011_add_users_email_index.sql
  - 012_create_refresh_tokens_table.sql
  - 013_add_cart_items_constraints.sql

❌ INCORRECT:
  - 11_add_users_email_index.sql           (leading zero missing)
  - add_users_email_index.sql              (no number prefix)
  - 011_AddUsersEmailIndex.sql             (should use snake_case)
```

### Migration Template

Create a new file in `sql/migrations/` with this template:

```sql
-- ============================================================
-- Migration: Brief description of what this migration does
-- Purpose: Explain the business reason for this change
-- Date: YYYY-MM-DD
-- ============================================================

-- Add your SQL statements below
-- Note: All SQL must be compatible with SQL Server 2022

-- Example 1: Create a new table
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'YourNewTable')
BEGIN
    CREATE TABLE YourNewTable (
        id INT PRIMARY KEY IDENTITY(1,1),
        name NVARCHAR(100) NOT NULL,
        created_at DATETIME DEFAULT GETUTCDATE()
    );
    
    PRINT '[✓] Table YourNewTable created successfully';
END
ELSE
BEGIN
    PRINT '[ℹ] Table YourNewTable already exists, skipping creation';
END
GO

-- Example 2: Add a new column
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE TABLE_NAME='ExistingTable' AND COLUMN_NAME='new_column'
)
BEGIN
    ALTER TABLE ExistingTable
    ADD new_column NVARCHAR(255) NULL;
    
    PRINT '[✓] Column new_column added to ExistingTable';
END
ELSE
BEGIN
    PRINT '[ℹ] Column new_column already exists, skipping';
END
GO

-- Example 3: Create an index
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_column_name')
BEGIN
    CREATE INDEX idx_column_name ON TableName(column_name);
    
    PRINT '[✓] Index idx_column_name created successfully';
END
ELSE
BEGIN
    PRINT '[ℹ] Index idx_column_name already exists, skipping';
END
GO
```

### Key Rules for Migrations

1. **Be Idempotent**: Use `IF NOT EXISTS` or `IF EXISTS` checks
   - Migrations must be safe to run multiple times
   - Don't fail if table already exists
   - Don't fail if column already exists

2. **Use Transactions**: Wrap changes for atomic behavior
   ```sql
   BEGIN TRANSACTION
   -- your statements here
   COMMIT TRANSACTION
   ```

3. **Add Descriptive Comments**: Explain what and why
   ```sql
   -- Adds email verification tracking for audit compliance
   ```

4. **Test Against SQL Server 2022**: Ensure compatibility
   - This project uses SQL Server 2022 (no PostgreSQL/MySQL specifics)

5. **Include Rollback Information** (optional but recommended)
   ```sql
   -- ROLLBACK SCRIPT (manual, if needed):
   -- DROP TABLE YourNewTable;
   ```

---

## 🧪 Testing Migrations Locally

### Prerequisites

- Docker and Docker Compose installed
- `.env` file configured (copy from `.env.example`)

### Run Migrations

```bash
# Start services and run migrations automatically
docker-compose up

# Or restart with clean database
docker-compose down -v
docker-compose up
```

### Verify Migrations

```bash
# Check migration history in the database
docker exec -it sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost \
  -U SA \
  -P "yourStrongPassword123#" \
  -Q "SELECT migration_name, applied_at, status FROM __migrations_history ORDER BY applied_at;"
```

### Debug Issues

```bash
# View API container logs
docker logs distribuidora-api

# Access SQL Server directly
docker exec -it sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost \
  -U SA \
  -P "yourStrongPassword123#" \
  -Q "SELECT * FROM __migrations_history;"

# Check pending migrations
docker logs distribuidora-api | grep "pending\|Applying\|Error"
```

---

## 📊 Migration History Table

The system automatically creates and maintains this table:

```sql
CREATE TABLE __migrations_history (
    id INT PRIMARY KEY IDENTITY(1,1),
    migration_name NVARCHAR(255) NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT GETUTCDATE(),
    status NVARCHAR(50) DEFAULT 'success',
    error_message NVARCHAR(MAX) NULL,
    execution_time_ms INT NULL
);
```

### Columns

- **id**: Unique identifier
- **migration_name**: Name of the SQL migration file (e.g., "011_add_column.sql")
- **applied_at**: When the migration was executed
- **status**: 'success' or 'failed'
- **error_message**: Error details if migration failed
- **execution_time_ms**: How long migration took to execute

---

## ⚙️ Environment Variables

### Required for Migrations

```bash
DB_SERVER=sqlserver          # SQL Server hostname
DB_PORT=1433                 # SQL Server port
DB_NAME=distribuidora_db     # Database name
DB_USER=SA                   # Database user
DB_PASSWORD=...              # Database password (REQUIRED)
```

### Required for Admin Seeding

```bash
ADMIN_EMAIL=admin@distribuidora.local       # Email for default admin
ADMIN_PASSWORD=Admin123!@#                  # Password for default admin
```

---

## 🔄 Idempotency & Safety

### What Happens on Each Run

| Scenario | Behavior |
|----------|----------|
| Migration already applied | Skipped (checked in `__migrations_history`) |
| New migration exists | Applied in order (001, 002, 003, ...) |
| Migration fails | Rolled back automatically (transaction) |
| Database unreachable | Retries with exponential backoff (max 300s) |
| Admin already exists | Seeding skipped (no error) |

### Example: Safe Idempotent Migration

```sql
-- This migration is safe to run multiple times
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Promotions')
BEGIN
    CREATE TABLE Promotions (
        id INT PRIMARY KEY IDENTITY(1,1),
        code NVARCHAR(50) NOT NULL UNIQUE,
        discount_percent DECIMAL(5,2) NOT NULL,
        active BIT DEFAULT 1
    );
    
    PRINT '[✓] Table Promotions created';
END
ELSE
BEGIN
    PRINT '[ℹ] Table Promotions already exists';
END
GO
```

**Why it's safe:**
- ✅ Checks if table exists before creating
- ✅ Won't fail if run twice
- ✅ Clear logging messages
- ✅ No hardcoded data assumptions

---

## 🚨 Troubleshooting

### Problem: "Connection timeout"

```
Error: Could not connect after 60 attempts (300s)
```

**Solutions:**
1. Verify SQL Server is running: `docker ps | grep sqlserver`
2. Check logs: `docker logs sqlserver`
3. Ensure sufficient memory: `docker stats sqlserver`
4. Increase retry timeout in `migrator.py` if needed

### Problem: "Migration failed"

```
❌ Migration failed: Syntax error in statement
```

**Solutions:**
1. Check SQL syntax in the migration file
2. Verify SQL Server 2022 compatibility
3. Test SQL manually: `docker exec sqlserver sqlcmd -U SA ...`
4. Check `__migrations_history` for error details

### Problem: "Admin not created"

```
❌ Admin seeding failed: User already exists
```

**Solutions:**
1. Check existing admin: Query `Usuarios` table
2. Change `ADMIN_EMAIL` in `.env` and restart
3. Manually verify/fix admin credentials in database

---

## 📚 References

- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/sql-server/)
- [Flyway (Inspirational Tool)](https://flywaydb.org/)
- [Alembic (Inspirational Tool)](https://alembic.sqlalchemy.org/)
- [ACID Transactions](https://en.wikipedia.org/wiki/ACID)

---

## ✅ Checklist for New Migrations

Before committing a new migration:

- [ ] Follows naming convention: `NNN_description.sql`
- [ ] Uses next sequential number
- [ ] Contains `IF NOT EXISTS` or `IF EXISTS` checks (idempotent)
- [ ] Includes descriptive comments
- [ ] Tested locally with `docker-compose up`
- [ ] Verified in `__migrations_history` table
- [ ] No hardcoded environment variables
- [ ] Compatible with SQL Server 2022
- [ ] SQL is readable and well-formatted

---

**Generated**: 2025-12-15  
**Version**: 1.0  
**Maintainer**: Backend Development Team

