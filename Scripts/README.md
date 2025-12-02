# Distribuidora Perros y Gatos - E-commerce

Sistema de e-commerce completo para venta de productos para mascotas, desarrollado con FastAPI (Backend) y React (Frontend).

## ⚡ Inicio Rápido (2 Comandos)

```powershell
# 1. Instalar todo automáticamente
.\SETUP-COMPLETO.ps1

# 2. Iniciar aplicación
.\START.ps1
```

**¡Eso es todo!** La aplicación estará en http://localhost:3000

📖 **[Ver Guía de 30 Segundos](QUICKSTART.md)** | 📚 **[Documentación Completa](INSTALACION_RAPIDA.md)**

---

## 🚀 Instalación Rápida (Recomendado)

**¡Solo 3 comandos para tener todo funcionando!**

### Opción 1: Instalación Automática (Recomendada)

```powershell
# 1. Clonar repositorios (ajusta las URLs según tu repositorio)
git clone <url-backend> Distribuidora_Perros_Gatos_back
git clone <url-frontend> Distribuidora_Perros_Gatos_front

# 2. Instalar Backend (Docker - 3-5 minutos)
cd Distribuidora_Perros_Gatos_back
.\INSTALL.ps1

# 3. Instalar Frontend (React - 2-3 minutos)
cd ..\Distribuidora_Perros_Gatos_front
.\INSTALL.ps1

# 4. Iniciar aplicación
npm start
```

### Opción 2: Inicio Rápido con un Solo Comando

```powershell
# Desde la carpeta raíz del proyecto
.\START.ps1
```

**Este script automáticamente:**
- ✅ Inicia todos los servicios Docker (backend, base de datos, etc.)
- ✅ Verifica que todo esté funcionando
- ✅ Inicia el servidor de desarrollo React
- ✅ Abre la aplicación en tu navegador

### Verificar que Todo Funciona

```powershell
# Verificación completa del sistema
.\HEALTH-CHECK.ps1
```

**📖 [Ver Guía de Instalación Completa](INSTALACION_RAPIDA.md)**

## 📋 Requisitos

- **Backend:** Docker Desktop
- **Frontend:** Node.js 16+
- **SO:** Windows 10/11, macOS, Linux

## 🌐 URLs de Acceso

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| API Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| RabbitMQ Admin | http://localhost:15672 |

## ✨ Características

### 👥 Gestión de Usuarios
- Registro con verificación por email
- Login/Logout con JWT
- Recuperación de contraseña
- Perfiles de usuario y administrador

### 🛍️ Catálogo de Productos
- Navegación por categorías y subcategorías
- Búsqueda y filtros avanzados
- Carrusel de productos destacados
- Sistema de calificaciones y reseñas
- Carrito de compras

### 📦 Gestión de Pedidos
- Creación de pedidos
- Seguimiento de estado
- Historial de compras
- Panel de administración de pedidos

### 🏪 Panel de Administración
- Gestión de productos e inventario
- Gestión de categorías
- Gestión de usuarios
- Gestión de pedidos
- Gestión de carrusel
- Estadísticas y reportes

### 📧 Sistema de Notificaciones
- Emails de verificación
- Confirmación de pedidos
- Worker asíncrono con RabbitMQ

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** FastAPI (Python)
- **Base de datos:** SQL Server 2022
- **Message Queue:** RabbitMQ
- **Email Worker:** Node.js + TypeScript
- **Containerización:** Docker + Docker Compose
- **Instalación:** Scripts PowerShell automatizados ⭐

### Frontend
- **Framework:** React 18
- **Estado:** Redux + Redux Thunk
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **UI:** CSS personalizado con diseño moderno
- **Carrusel:** Swiper.js
- **Instalación:** Scripts PowerShell automatizados ⭐

## 🎯 Scripts de Gestión Automatizada

El proyecto incluye scripts que automatizan completamente la instalación y gestión:

| Script | Descripción | Uso |
|--------|-------------|-----|
| `SETUP-COMPLETO.ps1` | ⭐ Instalación completa automática | `.\SETUP-COMPLETO.ps1` |
| `START.ps1` | Inicia todos los servicios | `.\START.ps1` |
| `STOP.ps1` | Detiene todos los servicios | `.\STOP.ps1` |
| `HEALTH-CHECK.ps1` | Verifica estado del sistema | `.\HEALTH-CHECK.ps1` |
| `INSTALL.ps1` (Backend) | Instala solo el backend | `cd backend; .\INSTALL.ps1` |
| `INSTALL.ps1` (Frontend) | Instala solo el frontend | `cd frontend; .\INSTALL.ps1` |

**📖 [Ver Guía Completa de Scripts](SCRIPTS.md)**

## 📁 Estructura del Proyecto

```
Distribuidora_Perros_Gatos_back/
├── INSTALL.ps1              # ⭐ Script de instalación automática
├── docker-compose.yml       # Orquestación de servicios
├── backend/
│   ├── api/                 # FastAPI Backend
│   └── worker/              # Email Worker (Node.js)
└── sql/
    ├── schema.sql           # Schema de base de datos
    └── migrations/          # Migraciones

Distribuidora_Perros_Gatos_front/
├── INSTALL.ps1              # ⭐ Script de instalación automática
├── src/
│   ├── components/          # Componentes React
│   ├── pages/              # Páginas
│   ├── redux/              # Estado global
│   ├── services/           # Servicios API
│   └── modules/            # Módulos (carrito, etc.)
└── public/                 # Assets estáticos
```

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | ⚡ Inicio en 30 segundos |
| **[INSTALACION_RAPIDA.md](INSTALACION_RAPIDA.md)** | 📖 Guía completa de instalación |
| **[SCRIPTS.md](SCRIPTS.md)** | 🛠️ Todos los scripts disponibles |
| **[CONFIGURACION.md](CONFIGURACION.md)** | ⚙️ Configuraciones del proyecto |
| **[POST-INSTALACION.md](POST-INSTALACION.md)** | ✅ Checklist de verificación |
| **[INDICE.md](INDICE.md)** | 📚 Índice completo de documentación |

---

### Backend (Docker)
```powershell
# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

### Frontend (React)
```powershell
# Desarrollo
npm start

# Producción
npm run build

# Tests
npm test
```

## 📊 Base de Datos

**Tablas principales:**
- Usuarios
- Productos
- Categorias
- Subcategorias
- Pedidos
- DetallesPedido
- Inventario
- Calificaciones
- CarruselImagenes

## 🔐 Credenciales por Defecto

### SQL Server
- Host: localhost:1433
- User: SA
- Password: yourStrongPassword123#
- Database: distribuidora_db

### RabbitMQ
- Admin UI: http://localhost:15672
- User: guest
- Password: guest

## 🎯 Funcionalidades Principales

### Para Clientes
✅ Registro y autenticación
✅ Navegación de productos por categorías
✅ Búsqueda y filtros
✅ Carrito de compras
✅ Realizar pedidos
✅ Historial de pedidos
✅ Calificar productos

### Para Administradores
✅ Gestión completa de productos
✅ Control de inventario
✅ Gestión de categorías
✅ Administración de usuarios
✅ Gestión de pedidos
✅ Configuración de carrusel
✅ Panel de estadísticas

## 📖 Documentación Adicional

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Guía de Instalación:** [INSTALACION_RAPIDA.md](../INSTALACION_RAPIDA.md)
- **Arquitectura Backend:** [ARCHITECTURE.md](Distribuidora_Perros_Gatos_back/ARCHITECTURE.md)
- **Arquitectura Frontend:** [ARCHITECTURE.md](Distribuidora_Perros_Gatos_front/ARCHITECTURE.md)

## 🐛 Solución de Problemas

### Backend no inicia
```powershell
# Verificar Docker
docker ps

# Ver logs
docker-compose logs -f api

# Reiniciar
docker-compose restart
```

### Frontend no conecta con API
```powershell
# Verificar .env
cat .env

# Debería contener:
# REACT_APP_API_URL=http://localhost:8000/api

# Reiniciar servidor
npm start
```

### Base de datos no se crea
```powershell
# Aplicar schema manualmente
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C < sql/schema.sql
```

## 🚀 Despliegue en Producción

### Backend
```powershell
# Construir imagen optimizada
docker-compose -f docker-compose.prod.yml build

# Configurar variables de entorno
# Editar docker-compose.prod.yml con credenciales seguras

# Iniciar en producción
docker-compose -f docker-compose.prod.yml up -d
```

### Frontend
```powershell
# Crear build de producción
npm run build

# Servir con servidor web (nginx, apache, etc.)
# Los archivos estarán en ./build/
```

## 👥 Contribuir

1. Fork el proyecto
2. Crear una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT.

## 🆘 Soporte

Para problemas o preguntas:
- Revisa la [Guía de Instalación](../INSTALACION_RAPIDA.md)
- Consulta la documentación de API
- Revisa los logs de Docker

---

**Desarrollado con ❤️ para la gestión de productos para mascotas**

**¡Listo para usar! 🚀**
