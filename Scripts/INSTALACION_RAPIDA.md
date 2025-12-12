# 🚀 Guía de Instalación Rápida - Distribuidora Perros y Gatos

Este proyecto incluye scripts automatizados para facilitar la instalación y configuración inicial.

## 📋 Requisitos Previos

### Backend
- **Docker Desktop** (versión 20.10 o superior)
- **Docker Compose** (incluido en Docker Desktop)
- Windows 10/11, macOS, o Linux

### Frontend
- **Node.js** (versión 16 o superior)
- **npm** (incluido con Node.js)

## 🔧 Instalación Automatizada

### 1️⃣ Clonar el Repositorio

```powershell
# Clonar el repositorio backend
git clone <url-del-repositorio-backend>
cd distribuidora-animales-back

# Clonar el repositorio frontend (en otra carpeta)
git clone <url-del-repositorio-frontend>
cd distribuidora-animales-front
```

### 2️⃣ Instalar Backend (Docker)

```powershell
cd distribuidora-animales-back
.\INSTALL.ps1
```

**Este script automáticamente:**
- ✅ Verifica que Docker esté instalado y corriendo
- ✅ Construye las imágenes Docker (API, Worker)
- ✅ Inicia los contenedores (API, Worker, SQL Server, RabbitMQ)
- ✅ Aplica el schema de base de datos
- ✅ Configura todos los servicios necesarios

**Tiempo estimado:** 3-5 minutos (primera vez)

### 3️⃣ Instalar Frontend (React)

```powershell
cd distribuidora-animales-front
.\INSTALL.ps1
```

**Este script automáticamente:**
- ✅ Verifica Node.js y npm
- ✅ Crea el archivo `.env` con la configuración correcta
- ✅ Instala todas las dependencias npm
- ✅ Verifica la conexión con el backend

**Tiempo estimado:** 2-3 minutos

### 4️⃣ Iniciar la Aplicación

```powershell
# En distribuidora-animales-front
npm start
```

La aplicación se abrirá automáticamente en `http://localhost:3000`

## 🌐 URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs (Swagger)** | http://localhost:8000/docs | - |
| **RabbitMQ Admin** | http://localhost:15672 | user: `guest`, pass: `guest` |

## 🛠️ Comandos Útiles

### Backend (Docker)
```powershell
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f worker

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ver estado de contenedores
docker-compose ps

# Reconstruir y reiniciar
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Frontend (React)
```powershell
# Iniciar servidor de desarrollo
npm start

# Crear build de producción
npm run build

# Ejecutar tests
npm test

# Limpiar y reinstalar dependencias
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install
```

## 🔍 Verificación de Instalación

### Verificar Backend
```powershell
# Verificar que todos los contenedores estén corriendo
docker ps

# Deberías ver:
# - distribuidora-api
# - distribuidora-worker
# - sqlserver
# - rabbitmq

# Probar la API
curl http://localhost:8000/docs
```

### Verificar Frontend
```powershell
# Verificar que el servidor esté corriendo
# Abre http://localhost:3000 en tu navegador

# Verificar conexión con API
curl http://localhost:3000
```

## ⚠️ Solución de Problemas

### Backend

**❌ Error: "Docker no está corriendo"**
- Inicia Docker Desktop
- Espera a que el ícono de Docker muestre "running"
- Ejecuta `.\INSTALL.ps1` nuevamente

**❌ Error: "Puerto 8000 ya en uso"**
```powershell
# Detener el proceso que usa el puerto
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force

# O cambiar el puerto en docker-compose.yml
# Cambiar "8000:8000" a "8001:8000"
```

**❌ Error: "SQL Server no está listo"**
```powershell
# Esperar más tiempo y verificar logs
docker-compose logs sqlserver

# Reiniciar SQL Server
docker-compose restart sqlserver
```

**❌ Error: "Cannot connect to database"**
```powershell
# Verificar que SQL Server esté saludable
docker inspect sqlserver --format='{{.State.Health.Status}}'

# Debería mostrar: healthy

# Si no, reiniciar servicios
docker-compose down
docker-compose up -d
```

**❌ Error en migraciones de base de datos**
```powershell
# Aplicar migraciones manualmente
.\apply-migrations.ps1

# Ver estado de las tablas
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
```

### Frontend

**❌ Error: "npm install falla"**
```powershell
# Limpiar caché de npm
npm cache clean --force

# Intentar con legacy peer deps
npm install --legacy-peer-deps
```

**❌ Error: "Cannot connect to backend"**
- Verifica que el backend esté corriendo: `docker ps`
- Verifica la URL en `.env`: `REACT_APP_API_URL=http://localhost:8000/api`
- Reinicia el servidor React: `Ctrl+C` y luego `npm start`

**❌ Error: "Puerto 3000 ya en uso"**
```powershell
# El sistema te preguntará si quieres usar otro puerto
# O puedes detener el proceso manualmente
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

## 🔐 Credenciales por Defecto

### Base de Datos SQL Server
- **Server:** localhost:1433
- **Usuario:** SA
- **Password:** yourStrongPassword123#
- **Database:** distribuidora_db

### RabbitMQ
- **Host:** localhost:5672
- **Admin UI:** localhost:15672
- **Usuario:** guest
- **Password:** guest

### Email (Worker)
- Configurado en `docker-compose.yml`
- SMTP: Gmail
- Usuario: distribuidoraperrosgatos@gmail.com

## 📊 Estructura del Proyecto

```
distribuidora-animales-back/
├── INSTALL.ps1                 # Script de instalación automática ⭐
├── docker-compose.yml          # Configuración de servicios
├── Dockerfile.api              # Imagen del API
├── Dockerfile.worker           # Imagen del Worker
├── sql/
│   └── schema.sql              # Schema de base de datos
└── backend/
    ├── api/                    # FastAPI Backend
    └── worker/                 # Worker de emails

distribuidora-animales-front/
├── INSTALL.ps1                 # Script de instalación automática ⭐
├── package.json                # Dependencias npm
├── .env                        # Configuración (auto-generado)
├── public/                     # Archivos estáticos
└── src/                        # Código fuente React
```

## 🎯 Próximos Pasos

1. ✅ Ejecutar `.\INSTALL.ps1` en el backend
2. ✅ Ejecutar `.\INSTALL.ps1` en el frontend
3. ✅ Ejecutar `npm start` en el frontend
4. 🎉 ¡Comenzar a desarrollar!

## 📝 Notas Importantes

- **Primera instalación:** Puede tardar 5-8 minutos debido a la descarga de imágenes Docker
- **Instalaciones posteriores:** Serán mucho más rápidas (1-2 minutos)
- **Datos persistentes:** SQL Server usa volúmenes de Docker, los datos persisten entre reinicios
- **Hot reload:** Tanto el frontend como el backend soportan recarga en caliente durante desarrollo

## 🆘 Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica el estado de servicios: `docker-compose ps`
3. Consulta la documentación de API: http://localhost:8000/docs

---

**¡Listo para comenzar! 🚀**
