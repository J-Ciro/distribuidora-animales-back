# Quick Links

- [Copilot Instructions](../copilot-instructions.md)
- [Architecture](../ARCHITECTURE.md)
- [Product](../PRODUCT.md)
- [Contributing](../CONTRIBUTING.md)
- [**Migration Guide** ⭐](./MIGRATION_GUIDE.md)

# Distribuidora Perros y Gatos - Backend

Backend API for Distribuidora Perros y Gatos e-commerce platform - a multi-vendor platform for pet supplies (dogs and cats).

## 🚀 Quick Start (2 minutes)

### Prerequisites
- Podman or Docker installed and running

### Setup

1. **Clone and navigate** to backend directory:
   ```bash
   cd distribuidora-animales-back
   ```

2. **Build and start all services**:
   ```bash
   podman compose build
   podman compose up
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs
   - API Docs (ReDoc): http://localhost:8000/redoc

4. **Login with default admin**:
   - Email: `admin@gmail.com`
   - Password: `Admin123!@#`

That's it! The system automatically:
- ✅ Waits for SQL Server to be ready
- ✅ Applies all pending database migrations
- ✅ Creates default admin user
- ✅ Seeds initial data (categories, products, carousel)
- ✅ Starts the FastAPI server

### Subsequent Runs

```bash
# Start services
podman compose up

# Stop services
podman compose down

# Full reset (warning: deletes all data)
podman compose down -v
podman compose build
podman compose up
```

For more details on migrations, see [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md).

---

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
├── podman-compose.yml
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
- **Podman** o **Docker** instalado y ejecutándose
- Al menos **4GB de RAM** disponible para los contenedores
- Puertos **8000, 1433, 5672, 15672** disponibles
- **Conexión a Internet** (para descargar imágenes y configurar email)

---

# 🐳 Setup con Podman (Recomendado)

## 🚀 Primera Vez - Instalación Completa

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd distribuidora-animales-back

# 2. Construir imágenes
podman compose build

# 3. Iniciar todos los servicios
podman compose up
```

**Eso es todo!** El sistema realiza automáticamente:

1. **Espera a que SQL Server esté listo**
   - Verifica conexión a la base de datos
   - Reintentos automáticos

2. **Aplica migraciones secuencialmente**
   - Crea 14 tablas
   - Aplica 10 migraciones
   - Ejecuta 3 seeders (categorías, productos, carrusel)

3. **Crea usuario administrador automáticamente**
   - Email: `admin@gmail.com`
   - Contraseña: `Admin123!@#`
   - Email verificado automáticamente

4. **Inicia todos los servicios**
   - API FastAPI en `http://localhost:8000`
   - Worker Node.js procesando colas
   - SQL Server en `localhost:1433`
   - RabbitMQ con UI en `http://localhost:15672`

**Tiempo estimado**: 2-3 minutos (primera vez)

### 📋 Servicios Disponibles

| Servicio | URL | Credenciales |
|----------|-----|-------------|
| **API (Swagger)** | http://localhost:8000/docs | - |
| **API (ReDoc)** | http://localhost:8000/redoc | - |
| **RabbitMQ UI** | http://localhost:15672 | guest / guest |
| **SQL Server** | localhost:1433 | sa / yourStrongPassword123# |
| **Health Check** | http://localhost:8000/health | - |

---

## 🔄 Comandos Útiles

```bash
# Iniciar servicios (primera vez completa)
podman compose build
podman compose up

# Iniciar servicios (mantiene datos previos)
podman compose up

# Detener servicios (mantiene datos)
podman compose down

# Reiniciar servicios (mantiene datos)
podman compose restart

# Ver logs en tiempo real
podman logs -f distribuidora-api
podman logs -f distribuidora-worker
podman logs -f sqlserver

# Ver logs de todos los servicios
podman compose logs -f

# Reiniciar desde cero (⚠️ ELIMINA TODOS LOS DATOS)
podman compose down -v
podman compose build
podman compose up

# Ver estado de los servicios
podman compose ps
```

---

## ✅ Verificar Estado de los Servicios

```bash
# Ver todos los servicios corriendo
podman compose ps

# Ver logs en tiempo real
podman logs -f distribuidora-api

# Verificar tablas creadas
podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT name FROM sys.tables ORDER BY name"

# Verificar que el admin se creó
podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT email, rol FROM Usuarios WHERE email='admin@gmail.com'"

# Verificar migraciones aplicadas
podman logs distribuidora-db-migrator
```

---

## 🐛 Troubleshooting (Solución de Problemas)

### ❌ Error: "Podman no está corriendo"
**Solución**: Inicia Podman Desktop o el servicio de Podman y espera a que esté listo.

### ❌ Error: "Puerto 8000 ya está en uso"
**Solución**:
```bash
# Detener servicio anterior
podman compose down

# O cambiar el puerto en podman-compose.yml
```

### ❌ Error: "SQL Server no responde a tiempo"
**Solución**: SQL Server puede tardar hasta 2 minutos en iniciar. El sistema reintentar automáticamente:
```bash
# Ver logs de SQL Server
podman logs sqlserver

# Reintentar
podman compose down -v
podman compose build
podman compose up
```

### ❌ Error: "Migraciones no se aplicaron"
**Solución**:
```bash
# Ver logs del migrator
podman logs distribuidora-db-migrator

# Reiniciar desde cero
podman compose down -v
podman compose build
podman compose up
```

### ❌ Error: "No puedo acceder con las credenciales de admin"
**Solución**: El usuario admin se crea automáticamente. Verifica que exista:
```bash
# Verificar que el admin existe
podman exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT email, rol, email_verificado FROM Usuarios WHERE email='admin@gmail.com'"

# Las credenciales son:
# Email: admin@gmail.com
# Contraseña: Admin123!@#
```

### ❌ Error: "Email no se envía"
**Solución**:
1. Verifica que hayas configurado SMTP en `.env`
2. Revisa los logs del worker: `podman logs distribuidora-worker`
3. Consulta la [Guía de Configuración de Email](./CONFIGURACION_EMAIL_ACTUALIZADA.md)

---

## 📖 Documentación Adicional
- [Arquitectura del Sistema](./ARCHITECTURE.md)
- [Guía de Migraciones](./VERIFICACION_MIGRACION.md)
- [Historias de Usuario](./HU/README_HU.md)
---