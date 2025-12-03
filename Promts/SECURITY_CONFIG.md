# 🔒 Configuración de Seguridad - Variables de Entorno Requeridas

## ⚠️ IMPORTANTE: Cambios de Seguridad

A partir de esta versión, las siguientes variables de entorno **son obligatorias** y **no tienen valores por defecto** por razones de seguridad:

### Variables Requeridas

1. **`SECRET_KEY`** - Clave secreta para JWT
   - **Debe ser única y aleatoria**
   - Mínimo 32 caracteres recomendado
   - Genera una con: `openssl rand -hex 32`
   
2. **`DB_PASSWORD`** - Contraseña de la base de datos
   - **No usar contraseñas por defecto en producción**
   - Debe ser fuerte y única

## 🚀 Configuración Rápida

### 1. Copiar el archivo de ejemplo

```bash
cd backend/api
cp .env.example .env
```

### 2. Generar SECRET_KEY segura

**En Linux/Mac:**
```bash
openssl rand -hex 32
```

**En PowerShell (Windows):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

**En Python:**
```python
import secrets
print(secrets.token_hex(32))
```

### 3. Editar .env con tus valores

```env
# REQUERIDO: Pega la clave generada aquí
SECRET_KEY=tu_clave_secreta_generada_aqui_min_32_chars

# REQUERIDO: Tu contraseña de SQL Server
DB_PASSWORD=TuPasswordSegura123!
```

### 4. Verificar configuración

```bash
# El API debe iniciar sin errores
python -m uvicorn main:app --reload
```

## 🐳 Configuración con Docker

### docker-compose.yml

```yaml
services:
  api:
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
```

### .env en la raíz del proyecto

```env
SECRET_KEY=tu_clave_secreta_aqui
DB_PASSWORD=tu_password_db_aqui
```

## ❌ Errores Comunes

### Error: "field required" en SECRET_KEY o DB_PASSWORD

**Causa:** No has creado el archivo `.env` o faltan las variables.

**Solución:**
1. Copia `.env.example` a `.env`
2. Genera y configura `SECRET_KEY`
3. Configura `DB_PASSWORD`

### Error: Pydantic ValidationError

**Causa:** Las variables de entorno no están siendo cargadas.

**Solución:**
1. Verifica que el archivo `.env` esté en `backend/api/.env`
2. Reinicia el servidor después de editar `.env`

## 🔐 Mejores Prácticas de Seguridad

1. ✅ **NUNCA** commitear el archivo `.env` al repositorio
2. ✅ **SIEMPRE** usar diferentes SECRET_KEY para desarrollo y producción
3. ✅ Rotar SECRET_KEY periódicamente en producción
4. ✅ Usar gestores de secretos en producción (AWS Secrets Manager, Azure Key Vault, etc.)
5. ✅ Validar que las variables estén configuradas antes de deploy

## 📝 Checklist de Deployment

- [ ] Generar SECRET_KEY única para el ambiente
- [ ] Configurar DB_PASSWORD segura
- [ ] Verificar que `.env` NO esté en git (usar `.gitignore`)
- [ ] Configurar variables en el servidor/contenedor
- [ ] Validar que la aplicación inicie correctamente
- [ ] Documentar dónde están almacenadas las credenciales

## 🆘 Soporte

Si encuentras problemas con la configuración:

1. Revisa los logs del servidor: `docker logs distribuidora-api`
2. Verifica que las variables estén en `.env`
3. Confirma que `.env` esté en la ubicación correcta: `backend/api/.env`

---

**Nota:** Estos cambios fueron implementados para cumplir con mejores prácticas de seguridad identificadas en la auditoría de código.
