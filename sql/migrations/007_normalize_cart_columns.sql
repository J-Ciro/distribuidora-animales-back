/*
  Migration 003: Normalize cart columns
  - Ensure `created_at` and `updated_at` exist on `Carts` and `CartItems` and are NOT NULL with default GETUTCDATE()
  - Ensure `CartItems.precio_unitario` exists as DECIMAL(18,2) NOT NULL and populate existing NULLs

  Run this migration against the `distribuidora_db` database.
  Recommended to run inside the sqlserver container using sqlcmd with -C to avoid TLS issues in dev:
    docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -d distribuidora_db -C -i sql/migrations/003_normalize_cart_columns.sql

*/

BEGIN TRANSACTION;

-- === Carts: created_at / updated_at ===
IF COL_LENGTH('dbo.Carts', 'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.Carts ADD created_at DATETIME2 NULL;
    UPDATE dbo.Carts SET created_at = GETUTCDATE() WHERE created_at IS NULL;
    ALTER TABLE dbo.Carts ALTER COLUMN created_at DATETIME2 NOT NULL;
    IF NOT EXISTS (SELECT 1 FROM sys.default_constraints dc JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id WHERE OBJECT_NAME(c.object_id) = 'Carts' AND c.name = 'created_at')
    BEGIN
        ALTER TABLE dbo.Carts ADD CONSTRAINT DF_Carts_created_at DEFAULT (GETUTCDATE()) FOR created_at;
    END
END

IF COL_LENGTH('dbo.Carts', 'updated_at') IS NULL
BEGIN
    ALTER TABLE dbo.Carts ADD updated_at DATETIME2 NULL;
    UPDATE dbo.Carts SET updated_at = GETUTCDATE() WHERE updated_at IS NULL;
    ALTER TABLE dbo.Carts ALTER COLUMN updated_at DATETIME2 NOT NULL;
    IF NOT EXISTS (SELECT 1 FROM sys.default_constraints dc JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id WHERE OBJECT_NAME(c.object_id) = 'Carts' AND c.name = 'updated_at')
    BEGIN
        ALTER TABLE dbo.Carts ADD CONSTRAINT DF_Carts_updated_at DEFAULT (GETUTCDATE()) FOR updated_at;
    END
END

-- === CartItems: created_at / updated_at ===
IF COL_LENGTH('dbo.CartItems', 'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.CartItems ADD created_at DATETIME2 NULL;
    UPDATE dbo.CartItems SET created_at = GETUTCDATE() WHERE created_at IS NULL;
    ALTER TABLE dbo.CartItems ALTER COLUMN created_at DATETIME2 NOT NULL;
    IF NOT EXISTS (SELECT 1 FROM sys.default_constraints dc JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id WHERE OBJECT_NAME(c.object_id) = 'CartItems' AND c.name = 'created_at')
    BEGIN
        ALTER TABLE dbo.CartItems ADD CONSTRAINT DF_CartItems_created_at DEFAULT (GETUTCDATE()) FOR created_at;
    END
END

IF COL_LENGTH('dbo.CartItems', 'updated_at') IS NULL
BEGIN
    ALTER TABLE dbo.CartItems ADD updated_at DATETIME2 NULL;
    UPDATE dbo.CartItems SET updated_at = GETUTCDATE() WHERE updated_at IS NULL;
    ALTER TABLE dbo.CartItems ALTER COLUMN updated_at DATETIME2 NOT NULL;
    IF NOT EXISTS (SELECT 1 FROM sys.default_constraints dc JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id WHERE OBJECT_NAME(c.object_id) = 'CartItems' AND c.name = 'updated_at')
    BEGIN
        ALTER TABLE dbo.CartItems ADD CONSTRAINT DF_CartItems_updated_at DEFAULT (GETUTCDATE()) FOR updated_at;
    END
END

-- === CartItems: precio_unitario (ensure exists and NOT NULL) ===
IF COL_LENGTH('dbo.CartItems', 'precio_unitario') IS NULL
BEGIN
    ALTER TABLE dbo.CartItems ADD precio_unitario DECIMAL(18,2) NULL;
END

-- Populate precio_unitario from Productos where possible
UPDATE ci
SET ci.precio_unitario = p.precio
FROM dbo.CartItems ci
JOIN dbo.Productos p ON p.id = ci.producto_id
WHERE ci.precio_unitario IS NULL;

-- Set remaining NULLs to 0.00
UPDATE dbo.CartItems SET precio_unitario = 0.00 WHERE precio_unitario IS NULL;

-- Alter column to NOT NULL
ALTER TABLE dbo.CartItems ALTER COLUMN precio_unitario DECIMAL(18,2) NOT NULL;

-- Add default constraint if missing
IF NOT EXISTS (
    SELECT 1 FROM sys.default_constraints dc
    JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
    WHERE OBJECT_NAME(c.object_id) = 'CartItems' AND c.name = 'precio_unitario'
)
BEGIN
    ALTER TABLE dbo.CartItems ADD CONSTRAINT DF_CartItems_precio_unitario DEFAULT (0.00) FOR precio_unitario;
END

COMMIT TRANSACTION;
