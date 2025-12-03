# ✅ Checklist de Implementación - Sistema de Verificación de Email

## 📋 Antes de Usar en Producción

### 1. Configuración de Gmail SMTP
- [ ] Cuenta de Gmail tiene 2FA habilitado
- [ ] Contraseña de Aplicación generada en https://myaccount.google.com/apppasswords
- [ ] Archivo `backend/api/.env` actualizado con:
  ```env
  SMTP_USER=paulagutierrez0872@gmail.com
  SMTP_PASSWORD=tu_contraseña_de_aplicacion_aqui  # ⚠️ Cambiar esto
  ```
- [ ] Contraseña **NO** contiene espacios

### 2. Servicios Docker
- [ ] Backend reiniciado después de cambiar .env:
  ```powershell
  cd backend
  docker-compose restart api
  ```
- [ ] Verificar logs no muestran errores de SMTP:
  ```powershell
  docker logs api-container | Select-String "error|smtp" -CaseSensitive:$false
  ```

### 3. Frontend
- [ ] Instalar dependencias si es necesario:
  ```powershell
  cd frontend
  npm install
  ```
- [ ] Frontend corriendo en http://localhost:3000
- [ ] No hay errores en consola del navegador

---

## 🧪 Testing Básico

### Test 1: Registro y Verificación
- [ ] Ir a http://localhost:3000/registro
- [ ] Completar formulario con email real tuyo
- [ ] Click en "Registrarse"
- [ ] Ver mensaje: "¡Registro exitoso! Revisa tu correo..."
- [ ] Redirigido automáticamente a `/verify-email`
- [ ] Email recibido en bandeja (revisar spam también)
- [ ] Email tiene código de 6 dígitos
- [ ] Ingresar código en página de verificación
- [ ] Ver mensaje: "Cuenta verificada exitosamente"
- [ ] Redirigido a `/login`

### Test 2: Login con Cuenta Verificada
- [ ] Usar credenciales del Test 1
- [ ] Login exitoso
- [ ] No hay error de "cuenta no verificada"

### Test 3: Login SIN Verificar (crear nuevo usuario)
- [ ] Registrar nuevo usuario
- [ ] **NO** verificar el código
- [ ] Intentar login con ese usuario
- [ ] Ver error: "Cuenta no verificada. Revisa tu correo..."
- [ ] Redirigido a `/verify-email`

### Test 4: Código Expirado
- [ ] Registrar nuevo usuario
- [ ] Esperar 11 minutos (código expira en 10)
- [ ] Intentar verificar con código antiguo
- [ ] Ver error: "El código ha expirado"
- [ ] Click en "Reenviar código"
- [ ] Recibir nuevo email con nuevo código
- [ ] Verificar con nuevo código exitosamente

### Test 5: Intentos Máximos
- [ ] Registrar nuevo usuario
- [ ] Ingresar código incorrecto 5 veces
- [ ] Ver error: "Has excedido el número máximo de intentos"
- [ ] Solicitar reenvío de código
- [ ] Verificar con nuevo código

### Test 6: Rate Limiting Reenvíos
- [ ] Registrar nuevo usuario
- [ ] Solicitar reenvío 3 veces seguidas
- [ ] En el 4to intento ver error: "Has alcanzado el número máximo de reenvíos"
- [ ] Esperar 60 minutos y probar de nuevo

---

## 🔍 Verificaciones de Seguridad

### Backend
- [ ] Códigos almacenados como hash en DB (no plaintext)
- [ ] Usuario creado con `is_active=False`
- [ ] Endpoint `/auth/login` rechaza usuarios con `is_active=False`
- [ ] Códigos expiran después de 10 minutos
- [ ] Máximo 5 intentos de verificación por código
- [ ] Máximo 3 reenvíos por hora

### Frontend
- [ ] Página de verificación valida solo números (0-9)
- [ ] Inputs limitados a 1 dígito cada uno
- [ ] Botón de verificar deshabilitado si faltan dígitos
- [ ] Countdown visible para reenvío
- [ ] Mensajes de error claros y útiles

### Email
- [ ] Email se envía con TLS (conexión segura)
- [ ] Email contiene advertencia de seguridad
- [ ] Email menciona expiración de 10 minutos
- [ ] Email tiene diseño profesional (no spam-like)

---

## 🗄️ Verificaciones en Base de Datos

### SQL Queries de Validación

#### Ver usuarios no verificados
```sql
SELECT email, nombre_completo, is_active, fecha_registro
FROM Usuarios
WHERE is_active = 0
ORDER BY fecha_registro DESC;
```

#### Ver códigos de verificación activos
```sql
SELECT 
    u.email,
    vc.code_hash,
    vc.expires_at,
    vc.attempts,
    vc.sent_count,
    vc.is_used,
    vc.created_at,
    CASE 
        WHEN vc.expires_at > GETUTCDATE() THEN 'Válido'
        ELSE 'Expirado'
    END AS estado
FROM VerificationCode vc
JOIN Usuarios u ON vc.usuario_id = u.id
WHERE vc.is_used = 0
ORDER BY vc.created_at DESC;
```

#### Ver estadísticas de verificación
```sql
SELECT 
    COUNT(*) AS total_usuarios,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS verificados,
    SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) AS pendientes,
    CAST(SUM(CASE WHEN is_active = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100 AS DECIMAL(5,2)) AS porcentaje_verificacion
FROM Usuarios;
```

Resultados esperados:
- [ ] Usuarios nuevos aparecen con `is_active=0`
- [ ] Códigos tienen `code_hash` (no texto plano)
- [ ] Después de verificar: `is_active=1` y `is_used=1`

---

## 📊 Monitoreo de Logs

### Logs a Revisar

#### Registro exitoso
```
INFO: User X registered successfully
INFO: Email enviado exitosamente a usuario@ejemplo.com
```

#### Verificación exitosa
```
INFO: User X (usuario@ejemplo.com) verified successfully
```

#### Email fallido (pero registro OK)
```
ERROR: Error enviando email a usuario@ejemplo.com: [detalle]
```
*Nota: El registro debe completarse aunque el email falle*

#### Login de usuario no verificado
```
INFO: Login attempt for unverified account: usuario@ejemplo.com
```

### Comandos de Monitoreo

```powershell
# Ver todos los logs del backend
docker logs -f api-container

# Filtrar solo logs de email
docker logs -f api-container | Select-String "email" -CaseSensitive:$false

# Filtrar errores
docker logs -f api-container | Select-String "error" -CaseSensitive:$false

# Ver últimas 100 líneas
docker logs --tail 100 api-container
```

---

## 🚨 Errores Comunes y Soluciones

### ❌ "SMTPAuthenticationError: (535, ...)"
**Causa:** Contraseña incorrecta o no es contraseña de aplicación  
**Solución:**
1. Ir a https://myaccount.google.com/apppasswords
2. Generar nueva contraseña
3. Actualizar `.env`
4. Reiniciar: `docker-compose restart api`

### ❌ Email no llega
**Posibles causas:**
- [ ] Verificar carpeta de spam/promociones
- [ ] Confirmar SMTP_USER es el email correcto
- [ ] Ver logs: `docker logs api-container | Select-String "email"`
- [ ] Probar con otro email (Gmail, Outlook, etc.)

### ❌ "Cannot read property 'email' of undefined"
**Causa:** state no se pasó en navegación  
**Solución:** Asegurar que navigate incluye `state: { email }`

### ❌ "Network Error" en frontend
**Causa:** Backend no está corriendo o CORS  
**Solución:**
1. Verificar backend: `docker ps | Select-String api`
2. Confirmar CORS_ORIGINS en .env incluye `http://localhost:3000`

### ❌ Usuario sigue inactivo después de verificar
**Causa:** Código no marcado como usado o error en DB  
**Solución:**
1. Ver logs del backend
2. Query DB: `SELECT * FROM Usuarios WHERE email='...'`
3. Verificar transaction commits

---

## 📈 Métricas de Éxito

### KPIs a Monitorear

- [ ] **Tasa de Verificación**: % usuarios que verifican su email
  - Meta: >80% en primeras 24 horas
  
- [ ] **Tiempo de Verificación**: Promedio desde registro hasta verificación
  - Meta: <5 minutos
  
- [ ] **Tasa de Reenvíos**: % usuarios que solicitan reenvío
  - Esperado: 10-20%
  - Si >30%: revisar entrega de emails
  
- [ ] **Emails Entregados**: % emails que llegan exitosamente
  - Meta: >95%
  
- [ ] **Códigos Expirados**: % códigos que expiran sin usar
  - Si >40%: considerar aumentar tiempo de expiración

### Queries para Métricas

```sql
-- Tasa de verificación (últimos 7 días)
SELECT 
    COUNT(*) AS registros,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS verificados,
    CAST(SUM(CASE WHEN is_active = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100 AS DECIMAL(5,2)) AS tasa_verificacion
FROM Usuarios
WHERE fecha_registro >= DATEADD(day, -7, GETDATE());

-- Tiempo promedio de verificación
SELECT AVG(DATEDIFF(minute, u.fecha_registro, vc.updated_at)) AS minutos_promedio
FROM Usuarios u
JOIN VerificationCode vc ON u.id = vc.usuario_id
WHERE vc.is_used = 1 AND u.is_active = 1;

-- Reenvíos por usuario
SELECT AVG(sent_count) AS promedio_reenvios
FROM VerificationCode
WHERE is_used = 1;
```

---

## 🎯 Checklist Final

### Antes de Marcar como Completo

- [ ] Gmail SMTP configurado correctamente
- [ ] Backend reiniciado y sin errores
- [ ] Frontend sin errores de compilación
- [ ] Test 1 (Registro y Verificación) ✅
- [ ] Test 2 (Login Verificado) ✅
- [ ] Test 3 (Login Sin Verificar) ✅
- [ ] Test 4 (Código Expirado) ✅
- [ ] Test 5 (Intentos Máximos) ✅
- [ ] Códigos almacenados como hash en DB ✅
- [ ] Emails llegando correctamente ✅
- [ ] Documentación leída y entendida ✅

### Documentos de Referencia Revisados

- [ ] [IMPLEMENTACION_VERIFICACION_EMAIL.md](./IMPLEMENTACION_VERIFICACION_EMAIL.md)
- [ ] [GUIA_VERIFICACION_EMAIL.md](./GUIA_VERIFICACION_EMAIL.md)
- [ ] Este checklist

---

## 📞 Soporte

### En caso de problemas persistentes:

1. **Revisar logs completos:**
   ```powershell
   docker logs api-container > logs.txt
   notepad logs.txt
   ```

2. **Verificar configuración:**
   ```powershell
   # Backend
   cat backend/api/.env | Select-String "SMTP"
   
   # Frontend
   cat frontend/.env
   ```

3. **Estado de servicios:**
   ```powershell
   docker ps
   docker-compose logs api
   ```

4. **Test SMTP directo (Python):**
   ```python
   import smtplib
   from email.mime.text import MIMEText
   
   smtp = smtplib.SMTP('smtp.gmail.com', 587)
   smtp.starttls()
   smtp.login('tu_email@gmail.com', 'tu_contraseña_app')
   
   msg = MIMEText('Test')
   msg['Subject'] = 'Test'
   msg['From'] = 'tu_email@gmail.com'
   msg['To'] = 'destino@ejemplo.com'
   
   smtp.send_message(msg)
   smtp.quit()
   print("✅ Email enviado!")
   ```

---

## 🎉 Estado Final

Una vez completado este checklist, tu sistema de verificación de email estará **100% funcional y listo para producción**.

**Última actualización:** Enero 2025  
**Versión:** 1.0  
**Desarrollado por:** GitHub Copilot (Claude Sonnet 4.5)
