ALTER TABLE Pedidos ADD monto_envio DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE Pedidos ADD estado_pago NVARCHAR(50) DEFAULT 'Pendiente';