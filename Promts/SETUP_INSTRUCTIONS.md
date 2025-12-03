# 🚀 Instrucciones de Configuración - Backend

## 📋 Requisitos Previos

- Docker Desktop instalado y corriendo
- Git instalado
- Puertos disponibles: 8000 (API), 5672 (RabbitMQ), 15672 (RabbitMQ UI), 1433 (SQL Server)

## 🔧 Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd Distribuidora_Perros_Gatos_back/Distribuidora_Perros_Gatos_back
```

### 2. Configurar Variables de Entorno

#### Backend API (Python/FastAPI)
```bash
# Copiar archivo de ejemplo
cp backend/api/.env.example backend/api/.env

# Editar y configurar las variables
notepad backend/api/.env
```

**Variables importantes:**
- `DATABASE_URL`: Conexión a SQL Server (ya configurada para Docker)
- `JWT_SECRET_KEY`: Clave secreta para JWT (cambiar en producción)
- `SMTP_*`: Configuración del servidor de correo para verificación

#### Backend Worker (Node.js/TypeScript)
```bash
# Copiar archivo de ejemplo
cp backend/worker/.env.example backend/worker/.env

# Editar si es necesario
notepad backend/worker/.env
```

### 3. Iniciar los Contenedores

```bash
# Construir e iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

### 4. Verificar la Base de Datos

```bash
# Los scripts de inicialización se ejecutan automáticamente
# Verificar que las tablas estén creadas
docker exec -it distribuidora-sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "USE distribuidora_db; SELECT name FROM sys.tables;"
```

## 🧪 Probar la API

```bash
# Health check
curl http://localhost:8000/

# Verificar documentación
# Abrir en navegador: http://localhost:8000/docs
```

## 📦 Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| API (FastAPI) | 8000 | Backend REST API |
| RabbitMQ | 5672 | Message Broker |
| RabbitMQ UI | 15672 | Interfaz web (guest/guest) |
| SQL Server | 1433 | Base de datos |
| Worker | N/A | Procesa colas de RabbitMQ |

## 🔄 Comandos Útiles

```bash
# Reiniciar un servicio específico
docker-compose restart api
docker-compose restart worker

# Ver logs de un servicio
docker-compose logs -f api
docker-compose logs -f worker

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO! Borra la BD)
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 Solución de Problemas

### Error: "Port already in use"
```bash
# Verificar qué está usando el puerto
netstat -ano | findstr :8000

# Detener el proceso o cambiar el puerto en docker-compose.yml
```

### Error: "Cannot connect to SQL Server"
```bash
# Verificar que el contenedor esté corriendo
docker-compose ps

# Reiniciar SQL Server
docker-compose restart sqlserver

# Ver logs
docker-compose logs sqlserver
```

### Error: "RabbitMQ connection failed"
```bash
# Verificar RabbitMQ
docker-compose logs rabbitmq

# Reiniciar RabbitMQ
docker-compose restart rabbitmq
```

## 📚 Estructura del Proyecto

```
backend/
├── api/                    # FastAPI Application
│   ├── app/
│   │   ├── routers/       # Endpoints REST
│   │   ├── models.py      # Modelos SQLAlchemy
│   │   ├── schemas.py     # Schemas Pydantic
│   │   ├── utils/         # Utilidades (email, JWT, etc)
│   │   └── database.py    # Configuración DB
│   ├── .env               # Variables de entorno (NO en Git)
│   └── requirements.txt   # Dependencias Python
│
├── worker/                # Node.js Worker
│   ├── src/
│   │   ├── consumers/     # Consumidores RabbitMQ
│   │   ├── services/      # Lógica de negocio
│   │   └── index.ts       # Punto de entrada
│   ├── .env               # Variables de entorno (NO en Git)
│   └── package.json       # Dependencias Node
│
└── sql/                   # Scripts SQL
    ├── schema.sql         # Esquema de base de datos
    ├── migrations/        # Migraciones
    └── seeders/           # Datos iniciales
```

## 📧 Configuración de Email (Opcional)

Para habilitar verificación por email, configura las variables SMTP en `backend/api/.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM=tu-email@gmail.com
```

**Nota:** Para Gmail, necesitas crear una "App Password" en la configuración de seguridad.

## 🔐 Seguridad

⚠️ **IMPORTANTE:** 
- Nunca subas archivos `.env` a Git
- Cambia las contraseñas por defecto en producción
- Genera un nuevo `JWT_SECRET_KEY` aleatorio
- Usa HTTPS en producción

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica que todos los servicios estén corriendo: `docker-compose ps`
3. Consulta la documentación en `/docs`
