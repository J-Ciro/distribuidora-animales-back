-- ============================================================
-- Migration History Tracking Table
-- ============================================================
-- This table tracks which migrations have been applied to the database
-- Must be executed FIRST before any other migrations
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = '__migrations_history')
BEGIN
    CREATE TABLE __migrations_history (
        id INT PRIMARY KEY IDENTITY(1,1),
        migration_name NVARCHAR(255) NOT NULL UNIQUE,
        applied_at DATETIME DEFAULT GETUTCDATE(),
        status NVARCHAR(50) DEFAULT 'success',
        error_message NVARCHAR(MAX) NULL,
        execution_time_ms INT NULL
    );
    
    -- Create index for fast lookups
    CREATE INDEX idx_migration_name ON __migrations_history(migration_name);
    CREATE INDEX idx_applied_at ON __migrations_history(applied_at DESC);
    
    PRINT '[✓] Table __migrations_history created successfully';
END
ELSE
BEGIN
    PRINT '[✓] Table __migrations_history already exists, skipping creation';
END
GO
