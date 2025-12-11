# ✅ Verificación del Sistema de Migración

Este documento te ayudará a verificar que el sistema de migración de base de datos funciona correctamente después de clonar el repositorio.

## 🎯 Objetivo

Asegurar que la base de datos se inicializa automáticamente con:
- ✅ Schema completo (14 tablas)
- ✅ Todas las migraciones aplicadas (10 archivos)
- ✅ Datos iniciales cargados (4 seeders)
- ✅ API y Worker conectados y funcionando

## 📋 Pasos de Verificación

### 1. Verificar Estado de Contenedores

```powershell
docker-compose ps
```

**Resultado Esperado**:
```
NAME                   STATUS
distribuidora-api      Up (healthy)
distribuidora-worker   Up
rabbitmq               Up (healthy)
sqlserver              Up (healthy)
```

✅ **db-migrator NO debe aparecer** (se ejecuta y termina automáticamente)

---

### 2. Verificar que Migrator Completó Exitosamente

```powershell
docker ps -a | Select-String "db-migrator"
```

**Resultado Esperado**:
```
Exited (0)    # El código 0 indica éxito
```

❌ Si ves `Exited (1)` o cualquier otro número, la migración falló.

---

### 3. Ver Logs de Migración

```powershell
docker logs distribuidora-db-migrator
```

**Debes ver al final**:
```
==================================
✅ Database initialization complete!
==================================
Database: distribuidora_db
Status: All migrations and seeders applied successfully
==================================
```

**Debes ver estas secciones**:
- ✅ `SQL Server is ready and accepting connections!`
- ✅ `Database 'distribuidora_db' is ready`
- ✅ `Schema applied successfully`
- ✅ `Applied 10 migration(s) successfully`
- ✅ `Applied 4 seeder(s) successfully`

---

### 4. Verificar que la API Está Funcionando

```powershell
# Método 1: Abrir en navegador
Start-Process "http://localhost:8000/docs"

# Método 2: Desde PowerShell
Invoke-WebRequest -Uri http://localhost:8000/docs | Select-Object StatusCode
```

**Resultado Esperado**: StatusCode 200

---

### 5. Verificar Tablas en la Base de Datos

```powershell
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q "USE distribuidora_db; SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;"
```

**Resultado Esperado (14 tablas)**:
```
CartItems
Carts
CarruselImagenes
Categorias
InventarioHistorial
PedidoItems
Pedidos
PedidosHistorialEstado
ProductoImagenes
Productos
RefreshTokens
Subcategorias
Usuarios
VerificationCodes
```

---

### 6. Verificar Datos de Ejemplo

#### Categorías Iniciales

```powershell
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q "USE distribuidora_db; SELECT nombre, activo FROM Categorias;"
```

**Resultado Esperado**:
```
Perros    1
Gatos     1
```

#### Productos de Ejemplo

```powershell
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q "USE distribuidora_db; SELECT COUNT(*) as total FROM Productos;"
```

**Resultado Esperado**: `total: 5` (o más)

#### Imágenes del Carrusel

```powershell
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q "USE distribuidora_db; SELECT orden, activo FROM CarruselImagenes ORDER BY orden;"
```

**Resultado Esperado**: 5 filas con orden 1, 2, 3, 4, 5

---

### 7. Verificar Conexión de la API a la Base de Datos

```powershell
docker logs distribuidora-api --tail 20
```

**Debes ver**:
```
Database connection pool initialized successfully
INFO:     Application startup complete.
```

❌ **NO debes ver**: Errores de conexión a SQL Server

---

### 8. Verificar Conexión del Worker a RabbitMQ

```powershell
docker logs distribuidora-worker --tail 20
```

**Debes ver**:
```
✅ RabbitMQ connected
Worker started successfully
```

---

## 🐛 Problemas Comunes y Soluciones

### ❌ Problema: db-migrator muestra "Exited (1)"

**Diagnóstico**:
```powershell
docker logs distribuidora-db-migrator
```

**Soluciones Comunes**:

1. **SQL Server no estaba listo**:
   - Incrementar `start_period` en docker-compose.yml (ya está en 120s)
   - Verificar memoria disponible: `docker stats sqlserver`

2. **Error de password**:
   - Verificar que `SA_PASSWORD` sea consistente en docker-compose.yml
   - Actual: `yourStrongPassword123#`

3. **Archivo SQL con errores**:
   - Revisar el último archivo que intentó aplicar en los logs
   - Verificar sintaxis SQL

**Reintentar desde cero**:
```powershell
docker-compose down -v  # ⚠️ Elimina todos los datos
docker-compose up -d
```

---

### ❌ Problema: API no inicia o muestra errores de conexión

**Diagnóstico**:
```powershell
docker logs distribuidora-api
```

**Causas Comunes**:

1. **db-migrator no completó**:
   - Verificar estado: `docker ps -a | Select-String "db-migrator"`
   - Debe mostrar `Exited (0)`

2. **Configuración de base de datos incorrecta**:
   - Verificar variables de entorno en docker-compose.yml
   - `DB_SERVER=sqlserver` (nombre del servicio)
   - `DB_PASSWORD=yourStrongPassword123#`

3. **SQL Server no está saludable**:
   ```powershell
   docker inspect sqlserver | Select-String "Health"
   ```

**Solución**:
```powershell
docker-compose restart api
```

---

### ❌ Problema: Worker no inicia o no conecta a RabbitMQ

**Diagnóstico**:
```powershell
docker logs distribuidora-worker
```

**Solución**:
```powershell
# Verificar que RabbitMQ esté saludable
docker-compose ps rabbitmq

# Reiniciar worker
docker-compose restart worker
```

---

### ❌ Problema: Tablas no existen o datos faltantes

**Diagnóstico**:
```powershell
# Ver cuántas tablas se crearon
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -Q "USE distribuidora_db; SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
```

**Solución**: Reiniciar migración completa
```powershell
# 1. Detener todo
docker-compose down

# 2. Eliminar SOLO el volumen de la base de datos
docker volume rm distribuidora_perros_gatos_back_sqlserver_data

# 3. Reiniciar
docker-compose up -d

# 4. Monitorear migración
docker logs -f distribuidora-db-migrator
```

---

## 📊 Checklist de Verificación Completa

Usa este checklist para confirmar que TODO funciona:

- [ ] `docker-compose ps` muestra todos los servicios UP (excepto db-migrator)
- [ ] `docker ps -a | Select-String "db-migrator"` muestra `Exited (0)`
- [ ] `docker logs distribuidora-db-migrator` termina con `Database initialization complete!`
- [ ] API responde en http://localhost:8000/docs (200 OK)
- [ ] Logs de API muestran `Database connection pool initialized successfully`
- [ ] Logs de Worker muestran `RabbitMQ connected`
- [ ] Base de datos tiene 14 tablas
- [ ] Existen 2+ categorías (Perros, Gatos)
- [ ] Existen 5+ productos de ejemplo
- [ ] Existen 5 imágenes de carrusel (orden 1-5)

---

## ⏱️ Tiempos Esperados

En un sistema con recursos normales:

| Fase | Tiempo |
|------|--------|
| SQL Server startup | 90-150 segundos |
| db-migrator esperando SQL Server | 0-30 segundos |
| Aplicación de schema | 5-10 segundos |
| Aplicación de 10 migraciones | 15-30 segundos |
| Aplicación de 4 seeders | 5-10 segundos |
| **Total migración** | **2-3.5 minutos** |
| API startup | 10-20 segundos |
| Worker startup | 5-10 segundos |
| **Total primera ejecución** | **3-4 minutos** |

---

## 🎓 Comandos Útiles Rápidos

```powershell
# Ver estado general
docker-compose ps

# Ver logs de migración
docker logs distribuidora-db-migrator

# Ver logs de API
docker logs distribuidora-api

# Ver logs de Worker
docker logs distribuidora-worker

# Reiniciar un servicio específico
docker-compose restart api

# Reiniciar todo desde cero (⚠️ elimina datos)
docker-compose down -v; docker-compose up -d

# Monitorear migración en tiempo real
docker logs -f distribuidora-db-migrator

# Acceder a SQL Server directamente
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#'
```

---

## 📚 Documentación Relacionada

- **Guía Completa de Migración**: [MIGRACION_BASE_DATOS.md](./MIGRACION_BASE_DATOS.md)
- **README Principal**: [README.md](./README.md)
- **Docker Compose**: [docker-compose.yml](./docker-compose.yml)

---

## ✅ Confirmación Final

Si completaste el checklist y no tienes errores:

**🎉 ¡FELICIDADES! El sistema de migración funciona perfectamente.**

La base de datos está lista para usar y cualquier persona que clone el repositorio tendrá la misma experiencia exitosa.

---

**¿Encontraste un problema que no está aquí?**

1. Revisa los logs completos: `docker logs distribuidora-db-migrator`
2. Consulta la guía completa: [MIGRACION_BASE_DATOS.md](./MIGRACION_BASE_DATOS.md)
3. Abre un issue en GitHub con:
   - Sistema operativo
   - Versión de Docker: `docker --version`
   - Logs del migrator
   - Logs de SQL Server: `docker logs sqlserver`
   - Salida de `docker-compose ps`
