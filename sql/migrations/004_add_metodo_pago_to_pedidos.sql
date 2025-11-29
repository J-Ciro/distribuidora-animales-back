-- Agregar columna metodo_pago a la tabla Pedidos
-- Fecha: 2025-11-29
-- Descripción: Permite guardar el método de pago seleccionado por el cliente

USE distribuidora_db;
GO

-- Verificar si la columna ya existe
IF NOT EXISTS (
    SELECT * 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Pedidos' 
    AND COLUMN_NAME = 'metodo_pago'
)
BEGIN
    ALTER TABLE Pedidos
    ADD metodo_pago VARCHAR(50) NULL DEFAULT 'Efectivo';
    
    PRINT 'Columna metodo_pago agregada exitosamente a la tabla Pedidos';
END
ELSE
BEGIN
    PRINT 'La columna metodo_pago ya existe en la tabla Pedidos';
END
GO
