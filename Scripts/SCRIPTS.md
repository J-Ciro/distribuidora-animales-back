# 📚 Guía de Scripts de Instalación y Gestión

Este documento describe todos los scripts disponibles para facilitar la instalación, configuración y gestión del proyecto.

## 🎯 Scripts Principales

### 1. `SETUP-COMPLETO.ps1` ⭐ (Recomendado para Primera Instalación)

**Descripción:** Instalación completa automática de todo el proyecto desde cero.

**Uso:**
```powershell
.\SETUP-COMPLETO.ps1
```

**Lo que hace:**
- ✅ Instala el backend (Docker, SQL Server, RabbitMQ)
- ✅ Instala el frontend (React, dependencias npm)
- ✅ Configura la base de datos
- ✅ Verifica que todo funcione correctamente

**Tiempo estimado:** 8-12 minutos (primera vez)

**Opciones:**
```powershell
# Solo backend
.\SETUP-COMPLETO.ps1 -SkipFrontend

# Solo frontend
.\SETUP-COMPLETO.ps1 -SkipBackend
```

---

### 2. `INSTALL.ps1` (Backend y Frontend)

**Descripción:** Scripts individuales para instalar cada componente.

**Backend:**
```powershell
cd Distribuidora_Perros_Gatos_back
.\INSTALL.ps1
```

**Frontend:**
```powershell
cd Distribuidora_Perros_Gatos_front
.\INSTALL.ps1
```

**Backend hace:**
- Verifica Docker
- Construye imágenes Docker
- Inicia contenedores (API, Worker, SQL Server, RabbitMQ)
- Aplica schema de base de datos

**Frontend hace:**
- Verifica Node.js y npm
- Crea archivo .env
- Instala dependencias npm
- Verifica conexión con backend

---

### 3. `START.ps1` (Inicio Rápido)

**Descripción:** Inicia todos los servicios del proyecto.

**Uso:**
```powershell
.\START.ps1
```

**Lo que hace:**
- ✅ Inicia servicios Docker (backend)
- ✅ Inicia servidor React (frontend)
- ✅ Verifica que todo esté corriendo
- ✅ Abre el navegador automáticamente

**Opciones:**
```powershell
# Solo backend
.\START.ps1 -BackendOnly

# Solo frontend
.\START.ps1 -FrontendOnly
```

---

### 4. `STOP.ps1` (Detener Servicios)

**Descripción:** Detiene todos los servicios del proyecto.

**Uso:**
```powershell
.\STOP.ps1
```

**Lo que hace:**
- ✅ Detiene contenedores Docker
- ✅ Detiene servidor React
- ✅ Libera recursos del sistema

---

### 5. `HEALTH-CHECK.ps1` (Verificación)

**Descripción:** Verifica que todos los servicios estén funcionando correctamente.

**Uso:**
```powershell
.\HEALTH-CHECK.ps1
```

**Lo que verifica:**
- ✅ Docker instalado y corriendo
- ✅ Contenedores activos
- ✅ SQL Server saludable y conectado
- ✅ RabbitMQ funcionando
- ✅ API Backend accesible
- ✅ Node.js instalado
- ✅ Frontend configurado
- ✅ Dependencias instaladas

---

## 📋 Flujos de Trabajo Recomendados

### 🆕 Primera Instalación (Nuevo Desarrollador)

```powershell
# 1. Clonar repositorios
git clone <url-backend> Distribuidora_Perros_Gatos_back
git clone <url-frontend> Distribuidora_Perros_Gatos_front

# 2. Ejecutar instalación completa
.\SETUP-COMPLETO.ps1

# 3. Iniciar aplicación
.\START.ps1

# La aplicación se abrirá en http://localhost:3000
```

**Tiempo total:** ~10 minutos

---

### 🔄 Uso Diario (Desarrollo)

```powershell
# Al inicio del día
.\START.ps1

# Desarrollar normalmente...

# Al final del día
.\STOP.ps1
```

---

### 🔍 Solución de Problemas

```powershell
# 1. Verificar estado del sistema
.\HEALTH-CHECK.ps1

# 2. Si hay problemas, reinstalar componente específico:

# Backend
cd Distribuidora_Perros_Gatos_back
.\INSTALL.ps1

# Frontend
cd Distribuidora_Perros_Gatos_front
.\INSTALL.ps1

# 3. Reiniciar todo
.\STOP.ps1
.\START.ps1
```

---

### 🧹 Limpieza y Reinstalación

```powershell
# Detener todo
.\STOP.ps1

# Limpiar Docker
cd Distribuidora_Perros_Gatos_back
docker-compose down -v  # -v elimina volúmenes (¡CUIDADO! borra datos)

# Reinstalar
.\SETUP-COMPLETO.ps1
```

---

## 🛠️ Comandos Docker Útiles

### Ver Estado de Contenedores
```powershell
docker ps
docker-compose ps
```

### Ver Logs
```powershell
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f sqlserver
```

### Reiniciar Servicios
```powershell
# Todos
docker-compose restart

# Específico
docker-compose restart api
```

### Reconstruir Imágenes
```powershell
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🎨 Comandos Frontend Útiles

### Desarrollo
```powershell
cd Distribuidora_Perros_Gatos_front
npm start
```

### Build de Producción
```powershell
npm run build
```

### Limpiar y Reinstalar Dependencias
```powershell
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install
```

---

## 📊 Estructura de Scripts

```
MariaPaulaRama/
├── SETUP-COMPLETO.ps1      # ⭐ Instalación completa automática
├── START.ps1               # Inicia todo el proyecto
├── STOP.ps1                # Detiene todo el proyecto
├── HEALTH-CHECK.ps1        # Verifica estado del sistema
├── README.md               # Documentación principal
├── INSTALACION_RAPIDA.md   # Guía de instalación detallada
├── CONFIGURACION.md        # Configuraciones del proyecto
├── SCRIPTS.md              # Este archivo
│
├── Distribuidora_Perros_Gatos_back/
│   └── INSTALL.ps1         # Instalación del backend
│
└── Distribuidora_Perros_Gatos_front/
    └── INSTALL.ps1         # Instalación del frontend
```

---

## ⚠️ Notas Importantes

### Requisitos del Sistema
- **Windows 10/11** con PowerShell 5.1+
- **Docker Desktop** instalado y corriendo
- **Node.js 16+** instalado
- **8GB RAM** mínimo (16GB recomendado)
- **10GB espacio** en disco

### Puertos Utilizados
- `3000` - Frontend React
- `8000` - Backend API
- `1433` - SQL Server
- `5672` - RabbitMQ
- `15672` - RabbitMQ Admin UI

**Si algún puerto está en uso**, verás un error. Soluciones:
1. Detener el proceso que usa el puerto
2. Cambiar el puerto en `docker-compose.yml` (backend) o React te preguntará automáticamente (frontend)

### Primera Ejecución
- La primera vez que ejecutes `SETUP-COMPLETO.ps1` o `INSTALL.ps1`, puede tardar más debido a:
  - Descarga de imágenes Docker (~2GB)
  - Instalación de dependencias npm (~500MB)
  - Inicialización de SQL Server

### Datos Persistentes
- SQL Server usa volúmenes de Docker
- Los datos **persisten** entre reinicios
- Para eliminar datos: `docker-compose down -v` (⚠️ elimina TODO)

---

## 🆘 Soporte y Ayuda

### Problemas Comunes

**❌ "Docker no está corriendo"**
- Solución: Inicia Docker Desktop

**❌ "Puerto ya en uso"**
- Solución: `Get-NetTCPConnection -LocalPort 8000` para ver qué usa el puerto

**❌ "npm install falla"**
- Solución: `npm install --legacy-peer-deps`

**❌ "SQL Server no inicia"**
- Solución: Espera 2-3 minutos, SQL Server es lento en iniciar

### Ver Logs Detallados

**Backend:**
```powershell
docker-compose logs -f api
```

**Frontend:**
Los logs aparecen en la terminal donde ejecutaste `npm start`

**SQL Server:**
```powershell
docker-compose logs -f sqlserver
```

---

## 📖 Documentación Adicional

- **Arquitectura Backend:** `Distribuidora_Perros_Gatos_back/ARCHITECTURE.md`
- **Arquitectura Frontend:** `Distribuidora_Perros_Gatos_front/ARCHITECTURE.md`
- **API Docs:** http://localhost:8000/docs (cuando esté corriendo)

---

**¡Todo listo para comenzar a desarrollar! 🚀**
