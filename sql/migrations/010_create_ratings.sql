-- ============================================================
-- MIGRATION: Create Ratings System
-- Description: Tabla para sistema de calificaciones de productos
-- Date: 2025-12-02
-- ============================================================

USE distribuidora_db;
GO

-- ============================================================
-- CALIFICACIONES Table (Product Ratings)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Calificaciones')
BEGIN
    CREATE TABLE Calificaciones (
        id INT PRIMARY KEY IDENTITY(1,1),
        producto_id INT NOT NULL,
        usuario_id INT NOT NULL,
        pedido_id INT NOT NULL,
        calificacion INT NOT NULL CHECK (calificacion >= 1 AND calificacion <= 5),
        comentario NVARCHAR(500) NULL,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
        aprobado BIT DEFAULT 1,
        visible BIT DEFAULT 1,
        CONSTRAINT fk_calificacion_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id),
        CONSTRAINT fk_calificacion_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id),
        CONSTRAINT fk_calificacion_pedido FOREIGN KEY (pedido_id) 
            REFERENCES Pedidos(id),
        -- Un usuario solo puede calificar un producto una vez por pedido
        CONSTRAINT uk_calificacion_usuario_producto_pedido UNIQUE (usuario_id, producto_id, pedido_id)
    );
    
    CREATE INDEX idx_calificacion_producto ON Calificaciones(producto_id);
    CREATE INDEX idx_calificacion_usuario ON Calificaciones(usuario_id);
    CREATE INDEX idx_calificacion_pedido ON Calificaciones(pedido_id);
    CREATE INDEX idx_calificacion_fecha ON Calificaciones(fecha_creacion);
    CREATE INDEX idx_calificacion_visible ON Calificaciones(visible);
    
    PRINT 'Table Calificaciones created successfully';
END
ELSE
BEGIN
    PRINT 'Table Calificaciones already exists';
END
GO

-- ============================================================
-- PRODUCTO_STATS Table (Product Rating Statistics)
-- Tabla para cachear estadísticas de calificaciones
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'ProductoStats')
BEGIN
    CREATE TABLE ProductoStats (
        producto_id INT PRIMARY KEY,
        promedio_calificacion DECIMAL(3, 2) DEFAULT 0 CHECK (promedio_calificacion >= 0 AND promedio_calificacion <= 5),
        total_calificaciones INT DEFAULT 0,
        total_5_estrellas INT DEFAULT 0,
        total_4_estrellas INT DEFAULT 0,
        total_3_estrellas INT DEFAULT 0,
        total_2_estrellas INT DEFAULT 0,
        total_1_estrella INT DEFAULT 0,
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_producto_stats_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_producto_stats_promedio ON ProductoStats(promedio_calificacion);
    
    PRINT 'Table ProductoStats created successfully';
END
ELSE
BEGIN
    PRINT 'Table ProductoStats already exists';
END
GO

-- ============================================================
-- TRIGGER: Update Product Stats on Rating Insert/Update/Delete
-- ============================================================

-- Trigger para INSERT
IF OBJECT_ID('trg_calificaciones_after_insert', 'TR') IS NOT NULL
    DROP TRIGGER trg_calificaciones_after_insert;
GO

CREATE TRIGGER trg_calificaciones_after_insert
ON Calificaciones
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @producto_id INT;
    
    SELECT @producto_id = producto_id FROM inserted;
    
    -- Actualizar o insertar estadísticas
    MERGE INTO ProductoStats AS target
    USING (
        SELECT 
            @producto_id AS producto_id,
            AVG(CAST(calificacion AS DECIMAL(3,2))) AS promedio,
            COUNT(*) AS total,
            SUM(CASE WHEN calificacion = 5 THEN 1 ELSE 0 END) AS total_5,
            SUM(CASE WHEN calificacion = 4 THEN 1 ELSE 0 END) AS total_4,
            SUM(CASE WHEN calificacion = 3 THEN 1 ELSE 0 END) AS total_3,
            SUM(CASE WHEN calificacion = 2 THEN 1 ELSE 0 END) AS total_2,
            SUM(CASE WHEN calificacion = 1 THEN 1 ELSE 0 END) AS total_1
        FROM Calificaciones
        WHERE producto_id = @producto_id AND visible = 1
    ) AS source
    ON target.producto_id = source.producto_id
    WHEN MATCHED THEN
        UPDATE SET
            promedio_calificacion = source.promedio,
            total_calificaciones = source.total,
            total_5_estrellas = source.total_5,
            total_4_estrellas = source.total_4,
            total_3_estrellas = source.total_3,
            total_2_estrellas = source.total_2,
            total_1_estrella = source.total_1,
            fecha_actualizacion = GETUTCDATE()
    WHEN NOT MATCHED THEN
        INSERT (producto_id, promedio_calificacion, total_calificaciones, total_5_estrellas, total_4_estrellas, total_3_estrellas, total_2_estrellas, total_1_estrella)
        VALUES (source.producto_id, source.promedio, source.total, source.total_5, source.total_4, source.total_3, source.total_2, source.total_1);
END
GO

-- Trigger para UPDATE
IF OBJECT_ID('trg_calificaciones_after_update', 'TR') IS NOT NULL
    DROP TRIGGER trg_calificaciones_after_update;
GO

CREATE TRIGGER trg_calificaciones_after_update
ON Calificaciones
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @producto_id INT;
    
    SELECT @producto_id = producto_id FROM inserted;
    
    -- Actualizar estadísticas
    UPDATE ProductoStats
    SET 
        promedio_calificacion = (
            SELECT AVG(CAST(calificacion AS DECIMAL(3,2))) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1
        ),
        total_calificaciones = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1
        ),
        total_5_estrellas = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 5
        ),
        total_4_estrellas = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 4
        ),
        total_3_estrellas = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 3
        ),
        total_2_estrellas = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 2
        ),
        total_1_estrella = (
            SELECT COUNT(*) 
            FROM Calificaciones 
            WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 1
        ),
        fecha_actualizacion = GETUTCDATE()
    WHERE producto_id = @producto_id;
END
GO

-- Trigger para DELETE
IF OBJECT_ID('trg_calificaciones_after_delete', 'TR') IS NOT NULL
    DROP TRIGGER trg_calificaciones_after_delete;
GO

CREATE TRIGGER trg_calificaciones_after_delete
ON Calificaciones
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @producto_id INT;
    
    SELECT @producto_id = producto_id FROM deleted;
    
    -- Actualizar estadísticas
    IF EXISTS (SELECT 1 FROM Calificaciones WHERE producto_id = @producto_id)
    BEGIN
        UPDATE ProductoStats
        SET 
            promedio_calificacion = (
                SELECT AVG(CAST(calificacion AS DECIMAL(3,2))) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1
            ),
            total_calificaciones = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1
            ),
            total_5_estrellas = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 5
            ),
            total_4_estrellas = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 4
            ),
            total_3_estrellas = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 3
            ),
            total_2_estrellas = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 2
            ),
            total_1_estrella = (
                SELECT COUNT(*) 
                FROM Calificaciones 
                WHERE producto_id = @producto_id AND visible = 1 AND calificacion = 1
            ),
            fecha_actualizacion = GETUTCDATE()
        WHERE producto_id = @producto_id;
    END
    ELSE
    BEGIN
        -- Si no quedan calificaciones, eliminar el registro de stats
        DELETE FROM ProductoStats WHERE producto_id = @producto_id;
    END
END
GO

PRINT 'Ratings migration completed successfully!';
