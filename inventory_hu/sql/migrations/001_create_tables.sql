USE distribuidora_db;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Productos')
BEGIN
    CREATE TABLE Productos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        descripcion VARCHAR(1000) NULL,
        precio DECIMAL(10,2) NOT NULL DEFAULT 0,
        stock INT NOT NULL DEFAULT 0
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'InventarioHistorial')
BEGIN
    CREATE TABLE InventarioHistorial (
        id INT IDENTITY(1,1) PRIMARY KEY,
        producto_id INT NOT NULL REFERENCES Productos(id) ON DELETE CASCADE,
        cantidad INT NOT NULL,
        accion VARCHAR(50) NOT NULL,
        request_id VARCHAR(100) NULL,
        created_at DATETIME2 DEFAULT SYSUTCDATETIME()
    );
END
GO
