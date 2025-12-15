ALTER TABLE Usuarios ADD preferencia_mascotas NVARCHAR(20) NULL;
ALTER TABLE Usuarios ADD failed_login_attempts INT DEFAULT 0 NOT NULL;
ALTER TABLE Usuarios ADD locked_until DATETIME NULL;
