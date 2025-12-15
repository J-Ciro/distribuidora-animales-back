CREATE TABLE Carts (
    id INT PRIMARY KEY IDENTITY(1,1),
    usuario_id INT,
    session_id NVARCHAR(255),
    total DECIMAL(10, 2) DEFAULT 0,
    cantidad_items INT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE()
);
CREATE INDEX idx_cart_usuario ON Carts(usuario_id);
CREATE INDEX idx_cart_session ON Carts(session_id);
CREATE TABLE CartItems (
    id INT PRIMARY KEY IDENTITY(1,1),
    cart_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    fecha_agregado DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_cartitem_cart FOREIGN KEY (cart_id) REFERENCES Carts(id) ON DELETE CASCADE,
    CONSTRAINT fk_cartitem_producto FOREIGN KEY (producto_id) REFERENCES Productos(id)
);
CREATE INDEX idx_cartitem_cart ON CartItems(cart_id);
CREATE INDEX idx_cartitem_producto ON CartItems(producto_id);