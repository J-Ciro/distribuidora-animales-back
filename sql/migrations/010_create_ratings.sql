CREATE TABLE Calificaciones (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    usuario_id INT NOT NULL,
    pedido_id INT NULL,
    puntuacion INT NOT NULL,
    comentario NVARCHAR(1000),
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
    aprobado BIT DEFAULT 1 NOT NULL,
    visible BIT DEFAULT 1 NOT NULL,
    CONSTRAINT fk_calificacion_producto FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE CASCADE,
    CONSTRAINT fk_calificacion_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE
);
CREATE INDEX idx_calificacion_producto ON Calificaciones(producto_id);
CREATE INDEX idx_calificacion_usuario ON Calificaciones(usuario_id);