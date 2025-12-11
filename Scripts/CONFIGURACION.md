# =============================================================================
# Archivo de Configuración del Proyecto
# =============================================================================
# Este archivo contiene todas las configuraciones importantes del proyecto
# Copia este archivo y ajusta los valores según tu entorno
# =============================================================================

# ==================== BACKEND (Docker Compose) ====================

## Base de Datos SQL Server
DB_SERVER=sqlserver
DB_PORT=1433
DB_NAME=distribuidora_db
DB_USER=SA
DB_PASSWORD=yourStrongPassword123#

## RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

## Email (SMTP Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=distribuidoraperrosgatos@gmail.com
SMTP_PASSWORD=ximz ubff zigp wnxj
EMAIL_FROM_NAME=Distribuidora Perros y Gatos
EMAIL_FROM_ADDRESS=distribuidoraperrosgatos@gmail.com

## API Configuration
API_HOST=0.0.0.0
API_PORT=8000

## Security (JWT)
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==================== FRONTEND (React) ====================

## API URL
REACT_APP_API_URL=http://localhost:8000/api

## Environment
REACT_APP_ENV=development

# ==================== PUERTOS ====================

# Estos son los puertos por defecto. Cámbielos si hay conflictos:
# - Frontend React: 3000
# - Backend API: 8000
# - SQL Server: 1433
# - RabbitMQ: 5672
# - RabbitMQ Admin UI: 15672

# Para cambiar puertos en Docker, edita docker-compose.yml
# Ejemplo: cambiar puerto de API de 8000 a 8001
#   ports:
#     - "8001:8000"  # host:container

# ==================== NOTAS IMPORTANTES ====================

# 1. SMTP GMAIL:
#    - Requiere "Contraseña de Aplicación" (no tu contraseña normal)
#    - Configurar en: https://myaccount.google.com/apppasswords
#    - Habilitar autenticación de 2 factores primero

# 2. SQL SERVER PASSWORD:
#    - Debe tener al menos 8 caracteres
#    - Incluir mayúsculas, minúsculas, números y símbolos
#    - Cambiar en producción

# 3. SECRET_KEY JWT:
#    - Generar con: openssl rand -hex 32
#    - O con Python: python -c "import secrets; print(secrets.token_hex(32))"
#    - NUNCA compartir o commitear esta clave

# 4. CORS ORIGINS:
#    - En producción, cambiar a dominios específicos
#    - Editar en backend/api/app/main.py

# ==================== CÓMO USAR ESTE ARCHIVO ====================

# Backend (Docker):
#   - Las variables se configuran en docker-compose.yml
#   - Para desarrollo local, edita docker-compose.yml directamente
#   - Para producción, usa docker-compose.prod.yml con secrets

# Frontend (React):
#   - Las variables se configuran en .env
#   - El script INSTALL.ps1 crea .env automáticamente
#   - Para personalizarlo, edita .env después de la instalación

# ==================== ARCHIVOS A EDITAR ====================

# Backend:
#   - docker-compose.yml (variables de entorno de todos los servicios)
#   - backend/api/.env.example (template para desarrollo local sin Docker)
#   - backend/worker/.env.example (template para worker local)

# Frontend:
#   - .env (creado automáticamente por INSTALL.ps1)
#   - .env.example (template de referencia)

# ==================== VERIFICACIÓN ====================

# Después de cambiar configuraciones, verifica que todo funcione:
#   .\HEALTH-CHECK.ps1

# Para reiniciar servicios con nueva configuración:
#   Backend: docker-compose down; docker-compose up -d
#   Frontend: Ctrl+C (detener), luego npm start
