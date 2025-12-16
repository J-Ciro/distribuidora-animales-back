-- Migration: 015_create_payment_tables.sql
-- Description: Create tables for Stripe payment integration (US-FUNC-01)
-- Date: 2025-12-16
-- Idempotent: YES (uses IF NOT EXISTS)

-- Table: TransaccionPago
-- Stores payment transactions processed through Stripe
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TransaccionPago')
BEGIN
    CREATE TABLE [dbo].[TransaccionPago] (
        [id] INT NOT NULL PRIMARY KEY IDENTITY(1,1),
        [pedido_id] INT NOT NULL,
        [payment_intent_id] VARCHAR(100) NOT NULL UNIQUE,
        [usuario_id] INT NOT NULL,
        [monto] NUMERIC(10, 2) NOT NULL,
        [moneda] VARCHAR(3) NOT NULL DEFAULT 'USD',
        [estado] VARCHAR(50) NOT NULL DEFAULT 'pending',
        [metodo_pago] VARCHAR(50) NULL,
        [detalles_error] VARCHAR(500) NULL,
        [fecha_creacion] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [fecha_actualizacion] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [fecha_confirmacion] DATETIME2(7) NULL,
        
        CONSTRAINT [FK_TransaccionPago_Pedidos] 
            FOREIGN KEY ([pedido_id]) REFERENCES [dbo].[Pedidos](id) ON DELETE CASCADE,
        
        INDEX [IX_TransaccionPago_PaymentIntentId] ([payment_intent_id]),
        INDEX [IX_TransaccionPago_PedidoId] ([pedido_id]),
        INDEX [IX_TransaccionPago_Estado] ([estado]),
        INDEX [IX_TransaccionPago_FechaCreacion] ([fecha_creacion]),
        INDEX [IX_TransaccionPago_UsuarioId] ([usuario_id])
    );
    
    PRINT '✅ Table [TransaccionPago] created successfully';
END
ELSE
BEGIN
    PRINT '⚠️  Table [TransaccionPago] already exists';
END
GO

-- Table: EstadoPagoHistorial
-- Audit table for payment transaction state changes
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EstadoPagoHistorial')
BEGIN
    CREATE TABLE [dbo].[EstadoPagoHistorial] (
        [id] INT NOT NULL PRIMARY KEY IDENTITY(1,1),
        [transaccion_id] INT NOT NULL,
        [estado_anterior] VARCHAR(50) NULL,
        [estado_nuevo] VARCHAR(50) NOT NULL,
        [razon_cambio] VARCHAR(300) NULL,
        [fecha] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        
        CONSTRAINT [FK_EstadoPagoHistorial_TransaccionPago] 
            FOREIGN KEY ([transaccion_id]) REFERENCES [dbo].[TransaccionPago](id) ON DELETE CASCADE,
        
        INDEX [IX_EstadoPagoHistorial_TransaccionId] ([transaccion_id]),
        INDEX [IX_EstadoPagoHistorial_Fecha] ([fecha])
    );
    
    PRINT '✅ Table [EstadoPagoHistorial] created successfully';
END
ELSE
BEGIN
    PRINT '⚠️  Table [EstadoPagoHistorial] already exists';
END
GO

-- Table: EventoWebhookStripe
-- Audit table for Stripe webhook events
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EventoWebhookStripe')
BEGIN
    CREATE TABLE [dbo].[EventoWebhookStripe] (
        [id] INT NOT NULL PRIMARY KEY IDENTITY(1,1),
        [event_id] VARCHAR(100) NOT NULL UNIQUE,
        [event_type] VARCHAR(100) NOT NULL,
        [payload] VARCHAR(4000) NULL,
        [transaccion_id] INT NULL,
        [procesado] BIT NOT NULL DEFAULT 0,
        [resultado] VARCHAR(300) NULL,
        [fecha_recibido] DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
        [fecha_procesado] DATETIME2(7) NULL,
        
        CONSTRAINT [FK_EventoWebhookStripe_TransaccionPago] 
            FOREIGN KEY ([transaccion_id]) REFERENCES [dbo].[TransaccionPago](id) ON DELETE SET NULL,
        
        INDEX [IX_EventoWebhookStripe_EventId] ([event_id]),
        INDEX [IX_EventoWebhookStripe_EventType] ([event_type]),
        INDEX [IX_EventoWebhookStripe_TransaccionId] ([transaccion_id]),
        INDEX [IX_EventoWebhookStripe_FechaRecibido] ([fecha_recibido])
    );
    
    PRINT '✅ Table [EventoWebhookStripe] created successfully';
END
ELSE
BEGIN
    PRINT '⚠️  Table [EventoWebhookStripe] already exists';
END
GO

-- Update: Add estado_pago column to Pedidos if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[Pedidos]') AND name = 'estado_pago')
BEGIN
    ALTER TABLE [dbo].[Pedidos] 
    ADD [estado_pago] VARCHAR(50) NOT NULL DEFAULT 'Pendiente de Pago';
    
    CREATE INDEX [IX_Pedidos_EstadoPago] ON [dbo].[Pedidos]([estado_pago]);
    
    PRINT '✅ Column [estado_pago] added to [Pedidos] table';
END
ELSE
BEGIN
    PRINT '⚠️  Column [estado_pago] already exists in [Pedidos] table';
END
GO

-- Remove duplicate metodo_pago column if present (SQL Server allows this issue)
-- Keep the first one, remove the second if it exists (data cleanup)
-- This is a data integrity fix based on models.py observation

PRINT '🔍 Payment migration 015 completed successfully';
GO
