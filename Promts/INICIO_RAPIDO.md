# 🚀 Guía Rápida de Configuración

## ⚡ Configuración Automática (Recomendado)

### Windows:

1. **Clonar los repositorios:**
   ```powershell
   git clone <url-backend> -b Refactor
   git clone <url-frontend> -b Front_Refactor
   ```

2. **Backend (ejecutar primero):**
   ```powershell
   cd Distribuidora_Perros_Gatos_back\Distribuidora_Perros_Gatos_back
   .\setup.ps1
   ```
   - El script configurará todo automáticamente
   - Te preguntará si quieres configurar email (opcional)
   - Iniciará Docker y todos los contenedores

3. **Frontend:**
   ```powershell
   cd Distribuidora_Perros_Gatos_front\Distribuidora_Perros_Gatos_front
   .\setup.ps1
   ```
   - El script instalará dependencias
   - Configurará variables de entorno
   - Te preguntará si quieres iniciar la app

### Linux/Mac:

1. **Clonar los repositorios:**
   ```bash
   git clone <url-backend> -b Refactor
   git clone <url-frontend> -b Front_Refactor
   ```

2. **Backend:**
   ```bash
   cd Distribuidora_Perros_Gatos_back/Distribuidora_Perros_Gatos_back
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Frontend:**
   ```bash
   cd Distribuidora_Perros_Gatos_front/Distribuidora_Perros_Gatos_front
   chmod +x setup.sh
   ./setup.sh
   ```

---

## 🎯 URLs de Acceso

Una vez configurado:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend | http://localhost:3000 | - |
| API Docs | http://localhost:8000/docs | - |
| RabbitMQ UI | http://localhost:15672 | guest / guest |

---

## 👤 Usuarios de Prueba

Estos usuarios se crean automáticamente al iniciar la base de datos:

**Administrador:**
- Email: `admin@distribuidora.com`
- Password: `Admin123!`

**Cliente:**
- Registrarse en el frontend (email opcional si no configuras SMTP)

---

## ⚙️ Configuración Manual (Solo si falla la automática)

### Backend:

```powershell
# 1. Copiar archivos de ejemplo
cp backend/api/.env.example backend/api/.env
cp backend/worker/.env.example backend/worker/.env

# 2. Editar backend/api/.env y configurar:
#    SMTP_USER=tu-email@gmail.com
#    SMTP_PASSWORD=tu-contraseña-app

# 3. Iniciar contenedores
docker-compose up -d
```

### Frontend:

```powershell
# 1. Copiar archivo de ejemplo
cp .env.example .env

# 2. Instalar dependencias
npm install

# 3. Iniciar
npm start
```

---

## 🐛 Solución de Problemas

### "No llega el código de verificación"
- **Solución:** Configura SMTP en `backend/api/.env`
- El email es opcional para desarrollo
- Puedes registrar usuarios sin verificar email

### "Error 404 al hacer compra"
- **Solución:** Verifica que el backend esté corriendo
- Ejecuta: `docker-compose ps` en el backend
- Verifica en `.env` del frontend: `REACT_APP_API_URL=http://localhost:8000`

### "Error de conexión a la base de datos"
- **Solución:** Reinicia los contenedores
- Ejecuta: `docker-compose restart`
- Espera 10 segundos y prueba de nuevo

### "Puerto 8000 ya en uso"
- **Solución:** Detén otros servicios o cambia el puerto
- Ejecuta: `docker-compose down`
- Verifica: `netstat -ano | findstr :8000`

### "node_modules corrupto"
- **Solución:** Elimina y reinstala
```powershell
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 Requisitos Previos

- ✅ Docker Desktop instalado y corriendo
- ✅ Node.js 16+ (frontend)
- ✅ Git
- ✅ PowerShell (Windows) o Bash (Linux/Mac)

---

## 🔐 Configuración de Email Gmail (Opcional)

Para que funcione el envío de códigos de verificación:

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Seguridad → Verificación en 2 pasos (actívala si no la tienes)
3. Contraseñas de aplicaciones
4. Genera una contraseña para "Correo"
5. Usa esa contraseña en `SMTP_PASSWORD` (no tu contraseña normal)

---

## ✅ Verificación de Instalación

### Backend:
```powershell
# Ver logs
docker-compose logs -f api

# Verificar que responda
curl http://localhost:8000/

# Ver documentación
# Abrir: http://localhost:8000/docs
```

### Frontend:
```powershell
# Verificar que compile sin errores
npm start

# Abrir: http://localhost:3000
```

---

## 🚀 Comandos Rápidos

```powershell
# Backend
cd Distribuidora_Perros_Gatos_back\Distribuidora_Perros_Gatos_back
docker-compose up -d        # Iniciar
docker-compose logs -f      # Ver logs
docker-compose restart      # Reiniciar
docker-compose down         # Detener

# Frontend
cd Distribuidora_Perros_Gatos_front\Distribuidora_Perros_Gatos_front
npm start                   # Iniciar
npm run build               # Build producción
```

---

## 📞 Soporte

Si después de seguir esta guía sigues teniendo problemas:

1. Verifica que Docker esté corriendo
2. Ejecuta los scripts de setup de nuevo
3. Revisa los logs: `docker-compose logs -f`
4. Verifica las variables de entorno en `.env`

---

**¡Listo para desarrollar! 🎉**
