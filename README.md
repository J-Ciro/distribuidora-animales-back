# Quick Links

- [Copilot Instructions](../copilot-instructions.md)
- [Architecture](../ARCHITECTURE.md)
- [Product](../PRODUCT.md)
- [Contributing](../CONTRIBUTING.md)

# Distribuidora Perros y Gatos - Backend

Backend API for Distribuidora Perros y Gatos e-commerce platform - a multi-vendor platform for pet supplies (dogs and cats).

## Project Structure

```
├── backend/
│   ├── api/                    # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Pydantic settings
│   │   │   ├── database.py     # SQLAlchemy setup
│   │   │   ├── schemas.py      # Pydantic models
│   │   │   ├── routers/        # API endpoints
│   │   │   │   ├── auth.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── products.py
│   │   │   │   ├── inventory.py
│   │   │   │   ├── carousel.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── admin_users.py
│   │   │   │   └── home_products.py
│   │   │   ├── services/       # Business logic
│   │   │   ├── middleware/     # Custom middleware
│   │   │   └── utils/          # Utilities
│   │   │       ├── security.py
│   │   │       ├── validators.py
│   │   │       ├── rabbitmq.py
│   │   │       └── logger.py
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   └── worker/                 # Node.js Consumer Service
│       ├── src/
│       │   ├── index.ts
│       │   ├── config.ts
│       │   ├── database.ts
│       │   ├── rabbitmq/
│       │   ├── services/
│       │   ├── jobs/
│       │   └── utils/
│       ├── package.json
│       ├── tsconfig.json
│       └── .env.example
│
├── sql/
│   ├── schema.sql              # Main database schema
│   ├── migrations/
│   │   └── 001_add_indexes.sql
│   └── seeders/
│       └── 001_initial_categories.sql
│
├── uploads/
│   ├── productos/
│   ├── carrusel/
│   └── temp/
│
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
├── .gitignore
├── .env.example
└── README.md
```

## Technology Stack

### Backend (FastAPI - Python)
- **Framework**: FastAPI with async/await
- **ORM**: SQLAlchemy 2.0
- **Database**: SQL Server
- **Message Queue**: RabbitMQ
- **Authentication**: JWT + Refresh Tokens with HttpOnly cookies
- **Password**: bcrypt hashing
- **File Upload**: Multer-like functionality (max 10MB)
- **Validation**: Pydantic v2

### Worker (Node.js - TypeScript)
- **Runtime**: Node.js 18+
- **Language**: TypeScript
- **Database**: mssql package with Tedious driver
- **Message Queue**: amqplib (RabbitMQ client)
- **Email**: Nodemailer
- **API**: Express.js (health checks only)

 🚀 Funcionalidades Implementadas

## HU_REGISTER_USER ✓
- Registro de usuarios con verificación por correo  
- Código de verificación de 6 dígitos (expira en 10 minutos)  
- Validación de contraseña fuerte (10+ caracteres, mayúscula, dígito, caracter especial)  
- Envío de correo por RabbitMQ  

## HU_LOGIN_USER ✓
- Autenticación email/contraseña con bcrypt  
- JWT (acceso 15 min, refresh 7 días)  
- Unificación del carrito entre dispositivos  
- Limitación de intentos fallidos (5 intentos → bloqueo 15 min)  

## HU_CREATE_PRODUCT ✓
- Creación de productos por administrador  
- Validación completa  
- Subida de imágenes (10MB máx, jpg/png/svg/webp)  
- Categoría / Subcategoría  
- Inventario + SKU  

## HU_MANAGE_CATEGORIES ✓
- CRUD de categorías y subcategorías  
- Unicidad sin distinguir mayúsculas  
- No permite eliminar categorías con productos  
- Procesamiento asíncrono con RabbitMQ  

## HU_MANAGE_INVENTORY ✓
- Reabastecimiento con auditoría  
- Historial de movimientos  
- Rate limiting  
- Tipos: reabastecimiento, venta, ajuste, devolución  

## HU_MANAGE_CAROUSEL ✓
- Gestión de imágenes del carrusel  
- Máx. 5 imágenes  
- Reordenamiento  
- URL opcional  

## HU_MANAGE_ORDERS ✓
- Vista admin de pedidos  
- Flujo de estados: Pendiente → Enviado → Entregado/Cancelado  
- Historial de cambios  
- Búsqueda para clientes  

## HU_MANAGE_USERS ✓
- Visualización de perfil del cliente  
- Búsqueda por nombre/email/cedula  
- Historial de pedidos  
- Estadísticas del usuario  

## HU_HOME_PRODUCTS ✓
- Listado por categoría/subcategoría  
- Carrito anónimo y autenticado  
- Validación de stock  
- Gestión de ítems en el carrito  

---

# 📩 Colas RabbitMQ

14 colas configuradas:

1. `email.verification`  
2. `email.password-reset`  
3. `email.order-confirmation`  
4. `email.order-status-update`  
5. `productos.crear`  
6. `productos.actualizar`  
7. `productos.imagen.crear`  
8. `productos.imagen.eliminar`  
9. `categorias.crear`  
10. `categorias.actualizar`  
11. `carrusel.imagen.crear`  
12. `carrusel.imagen.eliminar`  
13. `carrusel.imagen.reordenar`  
14. `pedido.estado.cambiar`  

---

# 🗄️ Esquema de Base de Datos (14 tablas)

- `Usuarios`  
- `Categorias`  
- `Subcategorias`  
- `Productos`  
- `ProductoImagenes`  
- `CarruselImagenes`  
- `Carts`  
- `CartItems`  
- `Pedidos`  
- `PedidoItems`  
- `PedidosHistorialEstado`  
- `InventarioHistorial`  
- `VerificationCodes`  
- `RefreshTokens`  

---

# 🏁 Getting Started

## Requisitos
- **Windows PowerShell 5.1+** (para ejecutar los scripts de instalación)
- **Docker Desktop** instalado y ejecutándose
- **Docker Compose** incluido con Docker Desktop
- Al menos **4GB de RAM** disponible para los contenedores
- Puertos **8000, 1433, 5672, 15672** disponibles
- **Conexión a Internet** (para descargar imágenes Docker y configurar email)

---

# 🐳 Setup con Docker (Recomendado)

## 🚀 Primera Vez - Instalación Automática con Scripts

**Recomendamos usar los scripts de PowerShell para una instalación guiada y sin errores.**

### Paso 1: Corregir Migraciones (Una sola vez)

```powershell
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd distribuidora-animales-back

# 2. Ejecutar script de corrección de migraciones
.\fix-migrations.ps1
```

**¿Qué hace `fix-migrations.ps1`?**
- ✅ Convierte `init-db.sh` de CRLF (Windows) a LF (Unix)
- ✅ Renumera migraciones secuencialmente (001-010)
- ✅ Elimina archivos de seeders duplicados
- ✅ Valida que todo esté listo para la migración

### Paso 2: Instalación Completa del Sistema

```powershell
# 3. Ejecutar script de instalación automática
.\setup.ps1
```

**¿Qué hace `setup.ps1`?**

El script realiza **8 pasos automatizados**:

1. **Validación de Prerequisitos**
   - Verifica que Docker esté instalado y corriendo
   - Valida Docker Compose

2. **Limpieza de Instalación Anterior**
   - Elimina contenedores previos
   - Limpia volúmenes y redes

3. **Configuración de Archivos `.env`**
   - Crea `backend/api/.env` desde `.env.example`
   - Crea `backend/worker/.env` desde `.env.example`

4. **Configuración de Email (Opcional)**
   - Solicita credenciales de Gmail
   - Guía para obtener contraseña de aplicación de Google
   - Configura SMTP automáticamente

5. **Validación de Archivos SQL**
   - Verifica `schema.sql`, `init-db.sh`
   - Cuenta migraciones y seeders

6. **Construcción e Inicio de Contenedores**
   - Ejecuta `docker-compose up -d --build`
   - Inicia: SQL Server, API, Worker, RabbitMQ, DB-Migrator

7. **Verificación de Servicios (con Healthchecks)**
   - **SQL Server**: hasta 120 segundos (24 intentos x 5s)
   - **API**: hasta 60 segundos (12 intentos x 5s)
   - **Worker**: verificación de estado
   - **Migrations**: confirma que se aplicaron correctamente

8. **Creación de Usuario Administrador**
   - Solicita email y contraseña
   - Crea usuario con rol `Admin`
   - Marca email como verificado automáticamente

**Tiempo estimado**: 3-5 minutos (primera vez)

### 🎯 Resultado Final

Al completar `setup.ps1` tendrás:

- ✅ Base de datos con **14 tablas** creadas
- ✅ **10 migraciones** aplicadas secuencialmente
- ✅ **3 seeders** con datos de ejemplo (categorías, productos, carrusel)
- ✅ Usuario **Administrador** creado y listo para usar
- ✅ Sistema de **verificación de email** configurado (si elegiste configurar Gmail)
- ✅ **4 servicios** corriendo:
  - API FastAPI en `http://localhost:8000`
  - Worker Node.js procesando colas
  - SQL Server en `localhost:1433`
  - RabbitMQ con UI en `http://localhost:15672`

### 📋 Servicios Disponibles

| Servicio | URL | Credenciales |
|----------|-----|-------------|
| **API (Swagger)** | http://localhost:8000/docs | - |
| **RabbitMQ UI** | http://localhost:15672 | guest / guest |
| **SQL Server** | localhost:1433 | sa / yourStrongPassword123# |
| **Health Check** | http://localhost:8000/health | - |

---

## 🔄 Instalación Manual (Sin Scripts)

Si prefieres ejecutar los comandos manualmente:

```bash
# 1. Configurar archivos .env
cp backend/api/.env.example backend/api/.env
cp backend/worker/.env.example backend/worker/.env

# 2. Editar archivos .env con tus credenciales de email

# 3. Iniciar servicios
docker-compose up -d --build

# 4. Verificar migración exitosa
docker logs distribuidora-db-migrator

# 5. Verificar API funcionando
curl http://localhost:8000/health
```

**Nota**: Con la instalación manual deberás crear el usuario administrador manualmente desde http://localhost:8000/docs

---

## ✅ Verificar Estado de los Servicios

```powershell
# Ver todos los servicios corriendo
docker-compose ps

# Ver logs en tiempo real
docker logs -f distribuidora-api
docker logs -f distribuidora-worker
docker logs -f sqlserver

# Ver logs de migración
docker logs distribuidora-db-migrator

# Verificar tablas creadas
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT name FROM sys.tables ORDER BY name"
```

---

## 🔧 Comandos Útiles

```powershell
# Reiniciar servicios (mantiene datos)
docker-compose restart

# Detener servicios (mantiene datos)
docker-compose down

# Reiniciar desde cero (⚠️ ELIMINA TODOS LOS DATOS)
docker-compose down -v
.\setup.ps1

# Ver logs de todos los servicios
docker-compose logs -f

# Acceder al contenedor de SQL Server
docker exec -it sqlserver /bin/bash

# Ejecutar query directamente
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT COUNT(*) FROM Productos"
```

---

## 🐛 Troubleshooting (Solución de Problemas)

### ❌ Error: "Docker no está corriendo"
**Solución**: Inicia Docker Desktop y espera a que aparezca el ícono verde en la bandeja del sistema.

### ❌ Error: "Puerto 8000 ya está en uso"
**Solución**: 
```powershell
# Buscar proceso usando el puerto
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
# Detener el proceso o cambiar el puerto en docker-compose.yml
```

### ❌ Error: "SQL Server no responde a tiempo"
**Solución**: SQL Server puede tardar hasta 2 minutos en iniciar. El script `setup.ps1` espera automáticamente. Si falla:
```powershell
# Ver logs de SQL Server
docker logs sqlserver
# Reintentar manualmente
docker-compose restart sqlserver
```

### ❌ Error: "Migraciones no se aplicaron"
**Solución**:
```powershell
# Ver logs del migrator
docker logs distribuidora-db-migrator
# Si hay error de CRLF, ejecutar fix-migrations.ps1
.\fix-migrations.ps1
# Reiniciar migración
docker-compose down -v
docker-compose up -d
```

### ❌ Error: "Email no se envía"
**Solución**:
1. Verifica que hayas configurado Gmail con contraseña de aplicación
2. Revisa los logs del worker: `docker logs distribuidora-worker`
3. Consulta la [Guía de Configuración de Email](./CONFIGURACION_EMAIL_ACTUALIZADA.md)

### ❌ Error: "Usuario administrador no se creó"
**Solución**: Créalo manualmente:
```powershell
# Opción 1: Desde Swagger UI
# 1. Ve a http://localhost:8000/docs
# 2. Endpoint POST /api/auth/register
# 3. Registra usuario
# 4. Actualiza rol a Admin en la BD:
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "UPDATE Usuarios SET rol='Admin', email_verificado=1 WHERE email='tumail@example.com'"
```

---

## 📖 Documentación Adicional

- [Arquitectura del Sistema](./ARCHITECTURE.md)
- [Flujo de Trabajo con IA](./AI_WORKFLOW.md)
- [Guía de Migraciones](./VERIFICACION_MIGRACION.md)
- [Historias de Usuario](./HU/README_HU.md)
- [Sistema de Calificaciones](./Promts/SISTEMA_CALIFICACIONES.md)
- [Configuración de Email](./Promts/CONFIGURACION_EMAIL_ACTUALIZADA.md)

---

# 💻 Setup Local (Sin Docker)

Si prefieres ejecutar los servicios localmente:
