-- Agregar campos de ubicación a la tabla Pedidos
-- Fecha: 2025-11-29

USE distribuidora_db;
GO

-- Verificar y agregar columna municipio
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('Pedidos') 
    AND name = 'municipio'
)
BEGIN
    ALTER TABLE Pedidos
    ADD municipio VARCHAR(100) NULL;
    PRINT 'Columna municipio agregada exitosamente a la tabla Pedidos';
END
ELSE
BEGIN
    PRINT 'La columna municipio ya existe en la tabla Pedidos';
END
GO

-- Verificar y agregar columna departamento
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('Pedidos') 
    AND name = 'departamento'
)
BEGIN
    ALTER TABLE Pedidos
    ADD departamento VARCHAR(100) NULL;
    PRINT 'Columna departamento agregada exitosamente a la tabla Pedidos';
END
ELSE
BEGIN
    PRINT 'La columna departamento ya existe en la tabla Pedidos';
END
GO

-- Verificar y agregar columna pais
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('Pedidos') 
    AND name = 'pais'
)
BEGIN
    ALTER TABLE Pedidos
    ADD pais VARCHAR(100) NULL;
    
    ALTER TABLE Pedidos
    ADD CONSTRAINT DF_Pedidos_pais DEFAULT 'Colombia' FOR pais;
    
    PRINT 'Columna pais agregada exitosamente a la tabla Pedidos';
END
ELSE
BEGIN
    PRINT 'La columna pais ya existe en la tabla Pedidos';
END
GO

PRINT 'Migración 005 completada exitosamente';
GO
