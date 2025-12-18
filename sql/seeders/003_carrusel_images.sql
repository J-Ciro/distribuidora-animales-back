-- ============================================================
-- Seeder: Imágenes predeterminadas del carrusel
-- ============================================================
-- Este script inserta las imágenes predeterminadas del carrusel
-- que se muestran en la página principal
-- ============================================================

USE distribuidora_db;
GO

-- Limpiar tabla de carrusel si existe datos previos (solo para desarrollo)
-- DELETE FROM CarruselImagenes;
-- GO

-- Insertar imágenes del carrusel si no existen
IF NOT EXISTS (SELECT 1 FROM CarruselImagenes WHERE orden = 1)
BEGIN
    INSERT INTO CarruselImagenes (orden, ruta_imagen, link_url, activo)
    VALUES (
        1,
        'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=1200&q=80',
        NULL,
        1
    );
    PRINT 'Imagen de carrusel 1 insertada';
END

IF NOT EXISTS (SELECT 1 FROM CarruselImagenes WHERE orden = 2)
BEGIN
    INSERT INTO CarruselImagenes (orden, ruta_imagen, link_url, activo)
    VALUES (
        2,
        'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=1200&q=80',
        NULL,
        1
    );
    PRINT 'Imagen de carrusel 2 insertada';
END

IF NOT EXISTS (SELECT 1 FROM CarruselImagenes WHERE orden = 3)
BEGIN
    INSERT INTO CarruselImagenes (orden, ruta_imagen, link_url, activo)
    VALUES (
        3,
        'https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=1200&q=80',
        NULL,
        1
    );
    PRINT 'Imagen de carrusel 3 insertada';
END

IF NOT EXISTS (SELECT 1 FROM CarruselImagenes WHERE orden = 4)
BEGIN
    INSERT INTO CarruselImagenes (orden, ruta_imagen, link_url, activo)
    VALUES (
        4,
        'https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=1200&q=80',
        NULL,
        1
    );
    PRINT 'Imagen de carrusel 4 insertada';
END

PRINT 'Seeder de imágenes del carrusel completado';
GO
