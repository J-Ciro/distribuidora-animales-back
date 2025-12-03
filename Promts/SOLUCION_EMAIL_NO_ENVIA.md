# 🚨 SOLUCIÓN: Email No Se Envía

## Problema Identificado

El sistema de verificación de email **NO está enviando emails** porque:

❌ La contraseña SMTP en `.env` es un placeholder: `TU_CONTRASEÑA_DE_APLICACION_AQUI`
❌ No has generado una **Contraseña de Aplicación** de Gmail

---

## ✅ SOLUCIÓN PASO A PASO (5 minutos)

### Paso 1: Habilitar Verificación en 2 Pasos (2FA)

1. Ve a: https://myaccount.google.com/security
2. Busca **"Verificación en dos pasos"**
3. Haz clic en **"Comenzar"**
4. Sigue los pasos (agregar número de teléfono, confirmar código)
5. ✅ Activa la verificación en 2 pasos

### Paso 2: Generar Contraseña de Aplicación

1. Ve a: https://myaccount.google.com/apppasswords
   - Si no aparece, asegúrate de tener 2FA activado primero
   
2. En **"Selecciona la app"**: Elige **"Correo"**

3. En **"Selecciona el dispositivo"**: Elige **"Otro (nombre personalizado)"**
   - Escribe: `Distribuidora Perros Gatos`

4. Haz clic en **"Generar"**

5. **Copia la contraseña de 16 caracteres** que aparece
   - Ejemplo: `abcd efgh ijkl mnop`
   - **IMPORTANTE:** Quita los espacios: `abcdefghijklmnop`

### Paso 3: Actualizar archivo .env

1. Abre el archivo:
   ```
   backend/api/.env
   ```

2. Encuentra esta línea:
   ```env
   SMTP_PASSWORD=TU_CONTRASEÑA_DE_APLICACION_AQUI
   ```

3. Reemplázala con tu contraseña (SIN espacios):
   ```env
   SMTP_PASSWORD=abcdefghijklmnop
   ```
   ⚠️ Usa TU contraseña, no este ejemplo

4. Guarda el archivo (Ctrl+S)

### Paso 4: Reiniciar el Contenedor API

Abre PowerShell y ejecuta:

```powershell
cd C:\Users\maria.gutierrezn\Distribuidora_Perros_Gatos_back\Distribuidora_Perros_Gatos_back
docker-compose restart api
```

Espera que diga:
```
[+] Restarting 1/1
 ✔ Container distribuidora-api  Started
```

### Paso 5: Probar el Envío de Email

#### Opción A: Test Manual con Script Python

```powershell
# Ejecutar test SMTP
docker exec distribuidora-api python /app/test_smtp.py
```

Si está bien configurado, verás:
```
✅ Connected successfully
✅ TLS activated
✅ Login successful!
✅ Test email sent successfully!
🎉 All tests passed!
```

#### Opción B: Test con Registro Real

1. Ve a: http://localhost:3000/registro
2. Completa el formulario con **tu email real**
3. Haz clic en "Registrarse"
4. Deberías ver el mensaje: "¡Registro exitoso! Revisa tu correo..."
5. **Revisa tu bandeja de entrada** (y también spam/promociones)
6. Deberías recibir un email con un código de 6 dígitos

---

## 🔍 Verificar que el Email se Envió

### Ver logs del backend:

```powershell
docker logs distribuidora-api --tail 50 | Select-String "email|smtp"
```

**Logs esperados (éxito):**
```
INFO: Email enviado exitosamente a usuario@ejemplo.com
```

**Logs de error (si algo falla):**
```
ERROR: Error enviando email a usuario@ejemplo.com: [detalle del error]
```

---

## 🚨 Errores Comunes

### Error: "SMTPAuthenticationError: (535, ...)"

**Causa:** Contraseña incorrecta o no es contraseña de aplicación

**Solución:**
1. Verifica que copiaste la contraseña sin espacios
2. Asegúrate de usar la contraseña de aplicación, no tu contraseña normal de Gmail
3. Regenera la contraseña en https://myaccount.google.com/apppasswords
4. Actualiza `.env` y reinicia: `docker-compose restart api`

### Error: "UnicodeEncodeError"

**Causa:** Hay caracteres especiales (Ñ, á, é, etc.) en la contraseña

**Solución:**
- Las contraseñas de aplicación de Gmail solo tienen letras y números (sin caracteres especiales)
- Si ves este error, significa que aún tienes el placeholder `TU_CONTRASEÑA_DE_APLICACION_AQUI`

### Email no llega

**Posibles soluciones:**
1. **Revisa la carpeta de SPAM/Promociones** en Gmail
2. Espera 1-2 minutos (a veces hay delay)
3. Verifica que usaste tu email real en el registro
4. Revisa logs del backend para confirmar que se envió

### No aparece opción "Contraseñas de aplicación"

**Causa:** No tienes 2FA activado

**Solución:**
1. Primero activa 2FA en: https://myaccount.google.com/security
2. Espera 5-10 minutos
3. Luego ve a: https://myaccount.google.com/apppasswords

---

## ✅ Checklist de Configuración

Marca cada paso cuando lo completes:

- [ ] 2FA activado en Gmail
- [ ] Contraseña de aplicación generada
- [ ] Archivo `.env` actualizado con la contraseña real
- [ ] Contraseña NO tiene espacios
- [ ] Contenedor API reiniciado: `docker-compose restart api`
- [ ] Test SMTP ejecutado exitosamente
- [ ] Email de prueba recibido

---

## 📧 Resultado Esperado

Una vez configurado correctamente, el email que recibirás se verá así:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
De: paulagutierrez0872@gmail.com
Para: tu_email@ejemplo.com
Asunto: Código de Verificación - Distribuidora Perros y Gatos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐕 Distribuidora Perros y Gatos 🐈

¡Bienvenido!

Gracias por registrarte en nuestra tienda. Para completar
tu registro, por favor verifica tu correo electrónico 
usando el siguiente código:

┌─────────────────┐
│   1 2 3 4 5 6   │  ← Tu código de 6 dígitos
└─────────────────┘

Este código es válido por 10 minutos.

⚠️ Importante:
• No compartas este código con nadie
• Si no solicitaste este código, ignora este mensaje
• El código solo funciona una vez

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 Siguiente Paso

Una vez que hayas completado estos pasos:

1. Haz clic en "Registrarse" en la aplicación
2. Ingresa el código de 6 dígitos que recibas
3. ¡Tu cuenta estará verificada! ✅

---

## 💡 Información Útil

### Límites de Gmail SMTP (Gratis)
- **500 emails por día**
- Perfecto para desarrollo y producción pequeña
- Sin costo adicional

### URLs Importantes
- 2FA: https://myaccount.google.com/security
- Contraseñas de app: https://myaccount.google.com/apppasswords
- Gmail: https://mail.google.com

---

**¿Necesitas ayuda?** Ejecuta estos comandos para debug:

```powershell
# Ver configuración actual (oculta la contraseña)
cd backend/api
cat .env | Select-String "SMTP"

# Ver logs recientes
docker logs distribuidora-api --tail 100

# Reiniciar todo
docker-compose restart
```
