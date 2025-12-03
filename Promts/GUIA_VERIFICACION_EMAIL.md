# Configuración de Email SMTP con Gmail

## ✅ Sistema de Verificación de Email Implementado

Se ha implementado un sistema completo de autenticación por email con las siguientes características:

### 🔒 Características de Seguridad

1. **Códigos de Verificación**:
   - Códigos de 6 dígitos generados aleatoriamente
   - Almacenados como hash (nunca en texto plano)
   - Expiración de 10 minutos
   - Máximo 5 intentos de verificación

2. **Rate Limiting**:
   - Máximo 3 reenvíos de código por hora
   - Prevención de abuso del sistema de emails

3. **Flujo de Registro**:
   - Usuario se registra → Cuenta inactiva (is_active=False)
   - Email con código enviado automáticamente
   - Usuario verifica → Cuenta activada (is_active=True)
   - Login permitido solo para cuentas verificadas

### 📧 Configuración de Gmail SMTP

Para que el sistema de emails funcione, necesitas configurar una **Contraseña de Aplicación** de Gmail:

#### Paso 1: Habilitar 2FA en tu cuenta de Gmail
1. Ve a https://myaccount.google.com/security
2. En "Acceso a Google", selecciona "Verificación en dos pasos"
3. Sigue los pasos para habilitar 2FA

#### Paso 2: Generar Contraseña de Aplicación
1. Ve a https://myaccount.google.com/apppasswords
2. Selecciona "Correo" en la aplicación
3. Selecciona "Otro (nombre personalizado)" en el dispositivo
4. Escribe "Distribuidora Perros Gatos"
5. Haz clic en "Generar"
6. **Copia la contraseña de 16 caracteres** (sin espacios)

#### Paso 3: Actualizar archivo .env
En `backend/api/.env`, actualiza la línea:

```env
SMTP_USER=paulagutierrez0872@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion_aqui
```

Reemplaza `tu_contraseña_de_aplicacion_aqui` con la contraseña que acabas de generar.

### 🚀 Límites Gratuitos de Gmail SMTP

- **500 emails por día** (límite gratuito)
- Perfecto para desarrollo y producción pequeña/mediana
- Sin costos adicionales

### 📝 Endpoints Implementados

#### POST /api/auth/register
- Crea usuario con `is_active=False`
- Genera y envía código de verificación
- Responde con mensaje de éxito

#### POST /api/auth/verify-email
Request body:
```json
{
  "email": "usuario@ejemplo.com",
  "code": "123456"
}
```
- Verifica el código
- Activa la cuenta (is_active=True)
- Invalida el código usado

#### POST /api/auth/resend-code
Request body:
```json
{
  "email": "usuario@ejemplo.com"
}
```
- Genera nuevo código
- Envía nuevo email
- Respeta límite de 3 reenvíos/hora

#### POST /api/auth/login
- Verifica que `is_active=True`
- Retorna error 403 si no está verificado
- Mensaje: "Cuenta no verificada. Revisa tu correo para obtener el código de verificación."

### 🎨 Frontend Implementado

#### Nueva Página: `/verify-email`
- **Componente**: `src/pages/verify-email/index.js`
- **Estilos**: `src/pages/verify-email/styles.css`
- **Características**:
  - Input de 6 dígitos con autofocus
  - Soporte para pegar código completo
  - Botón de reenvío con countdown (60s)
  - Manejo de códigos expirados
  - Validación de intentos máximos
  - Animaciones y diseño moderno

#### Flujo de Usuario
1. Usuario se registra en `/registro`
2. Redirección automática a `/verify-email` con email en state
3. Usuario ingresa código de 6 dígitos
4. Si correcto: redirección a `/login` con mensaje de éxito
5. Si incorrecto: contador de intentos
6. Si expiró: botón de reenvío habilitado

### 🔧 Servicios Actualizados

#### `src/services/auth-service.js`
```javascript
export const verificarEmail = authService.verifyEmail.bind(authService);
export const reenviarCodigo = authService.resendVerificationCode.bind(authService);
```

#### `backend/api/app/utils/email_service.py`
- Clase `EmailService` con métodos:
  - `send_verification_code(email, code)` - Email HTML con diseño profesional
  - `send_welcome_email(email, nombre)` - Email de bienvenida post-verificación
- Conexión SMTP con TLS
- Manejo de errores robusto

### 🗄️ Base de Datos

La tabla `VerificationCode` ya existe con:
- `code_hash` - Hash del código (seguridad)
- `expires_at` - Timestamp de expiración
- `attempts` - Contador de intentos
- `sent_count` - Contador de envíos
- `is_used` - Marca si fue usado

### ✅ Testing del Sistema

#### 1. Probar Registro con Verificación
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ejemplo.com",
    "password": "TestPass123!",
    "nombre": "Test User",
    "cedula": "12345678",
    "telefono": "555-1234",
    "direccion_envio": "Test 123"
  }'
```

Respuesta esperada:
```json
{
  "status": "success",
  "message": "¡Registro exitoso! Revisa tu correo para verificar tu cuenta. El código expira en 10 minutos."
}
```

#### 2. Revisar Email
Busca en tu bandeja de entrada (o spam) un email con:
- Asunto: "Código de Verificación - Distribuidora Perros y Gatos"
- Código de 6 dígitos en formato grande

#### 3. Verificar Email
```bash
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ejemplo.com",
    "code": "123456"
  }'
```

Respuesta esperada:
```json
{
  "status": "success",
  "message": "Cuenta verificada exitosamente. Ya puedes iniciar sesión."
}
```

#### 4. Login (debe funcionar)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ejemplo.com",
    "password": "TestPass123!"
  }'
```

#### 5. Test de Cuenta No Verificada
Si intentas login sin verificar:
```json
{
  "detail": {
    "status": "error",
    "message": "Cuenta no verificada. Revisa tu correo para obtener el código de verificación."
  }
}
```

### 🚨 Troubleshooting

#### "Error enviando email"
1. Verifica que 2FA esté habilitado en Gmail
2. Confirma que generaste una Contraseña de Aplicación (no tu contraseña normal)
3. Revisa que no tenga espacios: `abcd efgh ijkl mnop` → `abcdefghijklmnop`

#### "SMTPAuthenticationError"
- La contraseña en `.env` es incorrecta
- Regenera la contraseña de aplicación

#### "Email no llega"
1. Revisa spam/promociones en Gmail
2. Verifica logs del backend: `docker logs api-container`
3. Confirma que SMTP_USER sea el email correcto

#### "Código expirado"
- Los códigos duran 10 minutos
- Usa el botón "Reenviar código" en el frontend
- Límite: 3 reenvíos por hora

### 📊 Monitoreo

Ver logs del servicio de email:
```bash
docker logs -f api-container | grep -i email
```

Ver registros de verificación en DB:
```sql
SELECT TOP 10 * FROM VerificationCode 
ORDER BY created_at DESC;
```

### 🎯 Próximos Pasos Opcionales

1. **Email de bienvenida**: Ya implementado en `send_welcome_email()`, solo falta llamarlo después de verificación
2. **Recordatorios**: Email si el usuario no verificó en 24h
3. **Cambio de contraseña**: Usar mismo sistema de códigos
4. **Notificaciones de pedidos**: Reutilizar infraestructura de emails

### 🔐 Seguridad Implementada

✅ Códigos hasheados (bcrypt)  
✅ Expiración temporal (10 min)  
✅ Rate limiting (5 intentos, 3 reenvíos/hora)  
✅ Constant-time comparison  
✅ is_active flag para control de acceso  
✅ Invalidación de códigos antiguos  
✅ No exposición de información en errores  

---

**¡Sistema completo y listo para producción!** 🎉
