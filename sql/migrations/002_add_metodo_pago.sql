-- Agregar columna metodo_pago a la tabla Pedidos
-- Fecha: 2025-11-29

-- Verificar si la columna ya existe antes de agregarla
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('Pedidos') 
    AND name = 'metodo_pago'
)
BEGIN
    ALTER TABLE Pedidos
    ADD metodo_pago VARCHAR(50) NULL;
    
    -- Actualizar pedidos existentes con valor por defecto
    UPDATE Pedidos 
    SET metodo_pago = 'Efectivo' 
    WHERE metodo_pago IS NULL;
    
    PRINT 'Columna metodo_pago agregada exitosamente a la tabla Pedidos';
END
ELSE
BEGIN
    PRINT 'La columna metodo_pago ya existe en la tabla Pedidos';
END
GO
