-- Migration: add missing columns to dbo.Usuarios if they don't exist
SET NOCOUNT ON;

IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'telefono' AND Object_ID = Object_ID(N'dbo.Usuarios'))
BEGIN
    ALTER TABLE dbo.Usuarios ADD telefono NVARCHAR(20) NULL;
END

IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'direccion_envio' AND Object_ID = Object_ID(N'dbo.Usuarios'))
BEGIN
    ALTER TABLE dbo.Usuarios ADD direccion_envio NVARCHAR(500) NULL;
END

IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'preferencia_mascotas' AND Object_ID = Object_ID(N'dbo.Usuarios'))
BEGIN
    ALTER TABLE dbo.Usuarios ADD preferencia_mascotas NVARCHAR(20) NULL;
END

IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'failed_login_attempts' AND Object_ID = Object_ID(N'dbo.Usuarios'))
BEGIN
    ALTER TABLE dbo.Usuarios ADD failed_login_attempts INT NOT NULL CONSTRAINT DF_Usuarios_failed_login_attempts DEFAULT 0;
END

IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'locked_until' AND Object_ID = Object_ID(N'dbo.Usuarios'))
BEGIN
    ALTER TABLE dbo.Usuarios ADD locked_until DATETIME NULL;
END

PRINT 'Migration finished: ensured user columns exist.'
