CREATE TABLE Usuarios (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre_completo NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) NOT NULL UNIQUE,
    cedula NVARCHAR(20) NOT NULL UNIQUE,
    password_hash NVARCHAR(MAX) NOT NULL,
    es_admin BIT DEFAULT 0,
    is_active BIT DEFAULT 0,
    fecha_registro DATETIME DEFAULT GETUTCDATE(),
    ultimo_login DATETIME NULL,
    created_at DATETIME DEFAULT GETUTCDATE(),
    updated_at DATETIME DEFAULT GETUTCDATE()
);
CREATE INDEX idx_email ON Usuarios(email);
CREATE INDEX idx_cedula ON Usuarios(cedula);
CREATE INDEX idx_nombre ON Usuarios(nombre_completo);
CREATE TABLE Categorias (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre NVARCHAR(100) NOT NULL UNIQUE,
    descripcion NVARCHAR(500) NULL,
    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE()
);
CREATE INDEX idx_categoria_nombre ON Categorias(nombre);
CREATE TABLE Subcategorias (
    id INT PRIMARY KEY IDENTITY(1,1),
    categoria_id INT NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_subcategoria_categoria FOREIGN KEY (categoria_id) REFERENCES Categorias(id) ON DELETE CASCADE
);
CREATE INDEX idx_subcategoria_categoria ON Subcategorias(categoria_id);
CREATE UNIQUE INDEX idx_subcategoria_nombre_categoria ON Subcategorias(categoria_id, nombre);
CREATE TABLE Productos (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    precio DECIMAL(10, 2) NOT NULL,
    peso_gramos INT NOT NULL,
    cantidad_disponible INT DEFAULT 0,
    categoria_id INT NOT NULL,
    subcategoria_id INT NOT NULL,
    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_producto_categoria FOREIGN KEY (categoria_id) REFERENCES Categorias(id),
    CONSTRAINT fk_producto_subcategoria FOREIGN KEY (subcategoria_id) REFERENCES Subcategorias(id) ON DELETE CASCADE
);
CREATE INDEX idx_producto_categoria ON Productos(categoria_id);
CREATE INDEX idx_producto_subcategoria ON Productos(subcategoria_id);
CREATE INDEX idx_producto_nombre ON Productos(nombre);
CREATE TABLE ProductoImagenes (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    ruta_imagen NVARCHAR(MAX) NOT NULL,
    es_principal BIT DEFAULT 0,
    orden INT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_imagen_producto FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE CASCADE
);
CREATE INDEX idx_imagen_producto ON ProductoImagenes(producto_id);
CREATE TABLE CarruselImagenes (
    id INT PRIMARY KEY IDENTITY(1,1),
    orden INT NOT NULL UNIQUE,
    ruta_imagen NVARCHAR(MAX) NOT NULL,
    link_url NVARCHAR(500) NULL,
    activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE()
);
CREATE INDEX idx_carrusel_orden ON CarruselImagenes(orden);
CREATE TABLE Pedidos (
    id INT PRIMARY KEY IDENTITY(1,1),
    usuario_id INT NOT NULL,
    estado NVARCHAR(50) DEFAULT 'Pendiente',
    total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    direccion_entrega NVARCHAR(500) NOT NULL,
    telefono_contacto NVARCHAR(20) NOT NULL,
    nota_especial NVARCHAR(500) NULL,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_pedido_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
);
CREATE INDEX idx_pedido_usuario ON Pedidos(usuario_id);
CREATE INDEX idx_pedido_estado ON Pedidos(estado);
CREATE INDEX idx_pedido_fecha ON Pedidos(fecha_creacion);
CREATE TABLE PedidoItems (
    id INT PRIMARY KEY IDENTITY(1,1),
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_pedidoitem_pedido FOREIGN KEY (pedido_id) REFERENCES Pedidos(id) ON DELETE CASCADE,
    CONSTRAINT fk_pedidoitem_producto FOREIGN KEY (producto_id) REFERENCES Productos(id)
);
CREATE INDEX idx_pedidoitem_pedido ON PedidoItems(pedido_id);
CREATE TABLE PedidosHistorialEstado (
    id INT PRIMARY KEY IDENTITY(1,1),
    pedido_id INT NOT NULL,
    estado_anterior NVARCHAR(50) NULL,
    estado_nuevo NVARCHAR(50) NOT NULL,
    usuario_id INT NULL,
    nota NVARCHAR(300) NULL,
    fecha DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_historial_pedido FOREIGN KEY (pedido_id) REFERENCES Pedidos(id) ON DELETE CASCADE,
    CONSTRAINT fk_historial_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
);
CREATE INDEX idx_historial_pedido ON PedidosHistorialEstado(pedido_id);
CREATE INDEX idx_historial_fecha ON PedidosHistorialEstado(fecha);
CREATE TABLE InventarioHistorial (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    cantidad_anterior INT NOT NULL,
    cantidad_nueva INT NOT NULL,
    tipo_movimiento NVARCHAR(50) NOT NULL,
    referencia NVARCHAR(200) NULL,
    usuario_id INT NULL,
    fecha DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_inventario_producto FOREIGN KEY (producto_id) REFERENCES Productos(id),
    CONSTRAINT fk_inventario_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
);
CREATE INDEX idx_inventario_producto ON InventarioHistorial(producto_id);
CREATE INDEX idx_inventario_fecha ON InventarioHistorial(fecha);
CREATE TABLE VerificationCodes (
    id INT PRIMARY KEY IDENTITY(1,1),
    usuario_id INT NOT NULL,
    code_hash NVARCHAR(MAX) NOT NULL,
    expira_en DATETIME NOT NULL,
    intentos_fallidos INT DEFAULT 0,
    usado BIT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_verif_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE
);
CREATE INDEX idx_verif_usuario ON VerificationCodes(usuario_id);
CREATE TABLE RefreshTokens (
    id INT PRIMARY KEY IDENTITY(1,1),
    usuario_id INT NOT NULL,
    token_hash NVARCHAR(MAX) NOT NULL,
    expira_en DATETIME NOT NULL,
    revocado BIT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETUTCDATE(),
    CONSTRAINT fk_refresh_usuario FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE
);
CREATE INDEX idx_refresh_usuario ON RefreshTokens(usuario_id);
CREATE INDEX idx_refresh_expira ON RefreshTokens(expira_en);