ALTER TABLE Calificaciones ADD pedido_id INT NULL;
ALTER TABLE Calificaciones ADD fecha_actualizacion DATETIME DEFAULT GETUTCDATE();
ALTER TABLE Calificaciones ADD aprobado BIT DEFAULT 1 NOT NULL;
ALTER TABLE Calificaciones ADD visible BIT DEFAULT 1 NOT NULL;
