-- Seeder: Sample Products (5 ejemplo)
-- Inserta 5 productos de ejemplo usando las categorías y subcategorías existentes

USE distribuidora_db;
GO

BEGIN TRANSACTION;

-- Obtener ids de categorías
DECLARE @perros_id INT = (SELECT id FROM Categorias WHERE nombre = 'Perros');
DECLARE @gatos_id INT = (SELECT id FROM Categorias WHERE nombre = 'Gatos');

-- Obtener ids de subcategorías (por nombre dentro de su categoría)
DECLARE @perros_alimento_id INT = (SELECT TOP 1 id FROM Subcategorias WHERE categoria_id = @perros_id AND nombre = 'Alimento');
DECLARE @perros_accesorios_id INT = (SELECT TOP 1 id FROM Subcategorias WHERE categoria_id = @perros_id AND nombre = 'Accesorios');
DECLARE @perros_aseo_id INT = (SELECT TOP 1 id FROM Subcategorias WHERE categoria_id = @perros_id AND nombre = 'Productos de aseo');

DECLARE @gatos_alimento_id INT = (SELECT TOP 1 id FROM Subcategorias WHERE categoria_id = @gatos_id AND nombre = 'Alimento');
DECLARE @gatos_accesorios_id INT = (SELECT TOP 1 id FROM Subcategorias WHERE categoria_id = @gatos_id AND nombre = 'Accesorios');

-- Inserción de 5 productos de ejemplo
INSERT INTO Productos (nombre, descripcion, precio, peso_gramos, categoria_id, subcategoria_id, cantidad_disponible, activo, fecha_creacion)
VALUES
    ('Croquetas Premium Adultos Perro', 'Alimento balanceado premium para perros adultos, con proteína de pollo y omega-3 para piel sana y pelo brillante.', 34900.00, 1500, @perros_id, @perros_alimento_id, 100, 1, GETUTCDATE()),
    ('Correa Nylon Resistente 2m', 'Correa de nylon resistente con mosquetón metálico y agarre acolchado. Ideal para paseos diarios.', 45000.00, 200, @perros_id, @perros_accesorios_id, 50, 1, GETUTCDATE()),
    ('Shampoo Antipulgas Perro 500ml', 'Shampoo antipulgas y garrapatas, fórmula gentil para uso frecuente. Perfume agradable y pH balanceado.', 22000.00, 500, @perros_id, @perros_aseo_id, 75, 1, GETUTCDATE()),
    ('Croquetas Gatos Adultos Salmón', 'Alimento completo para gatos adultos con salmón real. Proteína de alta calidad y taurina.', 27900.00, 2000, @gatos_id, @gatos_alimento_id, 120, 1, GETUTCDATE()),
    ('Cama Donut Gato Talla M', 'Cama tipo donut acolchada para gatos, material suave y lavable. Proporciona confort y calidez.', 52000.00, 800, @gatos_id, @gatos_accesorios_id, 30, 1, GETUTCDATE();

COMMIT TRANSACTION;

PRINT 'Seed: 5 sample products inserted successfully.';
