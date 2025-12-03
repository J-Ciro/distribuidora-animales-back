# 🗄️ Sistema de Migración de Base de Datos

## 📋 Descripción General

Este proyecto utiliza un sistema automatizado de migraciones de base de datos que garantiza que cualquier persona que clone el repositorio tenga una experiencia perfecta y sin errores al inicializar la base de datos.

## 🎯 Características del Sistema

- ✅ **Inicialización Automática**: La base de datos se crea y migra automáticamente al ejecutar `docker-compose up`
- ✅ **Reintentos Robustos**: 60 intentos (5 minutos) para esperar a que SQL Server esté completamente listo
- ✅ **Validación de Errores**: Cada paso se valida y reporta errores claros
- ✅ **Idempotencia**: Puede ejecutarse múltiples veces sin causar problemas
- ✅ **Ordenamiento Garantizado**: Las migraciones se aplican en el orden correcto
- ✅ **Logs Detallados**: Información clara sobre cada paso del proceso

## 🚀 Inicio Rápido

### Primera Vez (Clonando el Repositorio)

```powershell
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Distribuidora_Perros_Gatos_back

# 2. Iniciar todos los servicios (incluida la migración automática)
docker-compose up -d

# 3. Verificar que la migración fue exitosa
docker logs distribuidora-db-migrator

# 4. Verificar que la API está funcionando
curl http://localhost:8000/health
```

¡Eso es todo! La base de datos estará completamente configurada y lista para usar.

## 🔧 Arquitectura del Sistema

### Servicios Docker

```yaml
1. sqlserver          → SQL Server 2022 (base de datos principal)
2. db-migrator        → Ejecuta migraciones automáticamente
3. api                → FastAPI backend (espera a que migrator termine)
4. worker             → Procesador de tareas (espera a que migrator termine)
5. rabbitmq           → Sistema de mensajería
```

### Orden de Ejecución

```
sqlserver (inicia) 
    ↓ (healthcheck espera ~120s)
sqlserver (listo) 
    ↓
db-migrator (inicia y ejecuta)
    ↓ (aplica schema, migrations, seeders)
db-migrator (completa exitosamente)
    ↓
api + worker (inician)
```

## 📁 Estructura de Archivos de Migración

```
sql/
├── init-db.sh              # Script principal de migración
├── schema.sql              # Schema completo de la base de datos
├── migrations/             # Migraciones incrementales
│   ├── 001_add_indexes.sql
│   ├── 002_add_metodo_pago.sql
│   ├── 003_add_on_delete_cascade_producto_subcategoria.sql
│   ├── 004_add_metodo_pago_to_pedidos.sql
│   ├── 005_add_location_fields_to_pedidos.sql
│   └── 010_create_ratings.sql
└── seeders/                # Datos iniciales
    ├── 001_initial_categories.sql
    ├── 002_sample_products.sql
    └── 003_carrusel_images.sql
```

## 🔄 Proceso de Migración Detallado

### Paso 1: Espera de SQL Server (0-300s)

```bash
⏳ SQL Server not ready yet (Attempt 1/60). Waiting 5 seconds...
⏳ SQL Server not ready yet (Attempt 2/60). Waiting 5 seconds...
...
✅ SQL Server is ready and accepting connections!
```

- **Tiempo máximo**: 5 minutos (60 intentos × 5 segundos)
- **SQL Server típicamente tarda**: 2-3 minutos en estar listo
- **Validación**: Conexión exitosa con `SELECT 1`

### Paso 2: Creación de Base de Datos

```bash
📦 Ensuring database 'distribuidora_db' exists...
✅ Database 'distribuidora_db' is ready
```

- Crea la base de datos `distribuidora_db` si no existe
- Es idempotente (no falla si ya existe)

### Paso 3: Aplicación de Schema

```bash
📋 Applying schema...
✅ Schema applied successfully
```

Crea todas las tablas:
- Usuarios
- Categorias / Subcategorias
- Productos / ProductoImagenes
- CarruselImagenes
- Carts / CartItems
- Pedidos / PedidoItems
- PedidosHistorialEstado
- InventarioHistorial
- VerificationCodes
- RefreshTokens

### Paso 4: Aplicación de Migraciones

```bash
🔄 Applying migrations...
  📄 Applying migration: 001_add_indexes.sql
  📄 Applying migration: 002_add_metodo_pago.sql
  ...
✅ Applied 10 migration(s) successfully
```

Las migraciones se aplican en orden alfabético (por eso usamos prefijos numéricos).

### Paso 5: Aplicación de Seeders

```bash
🌱 Applying seeders...
  📄 Applying seeder: 001_initial_categories.sql
  📄 Applying seeder: 002_sample_products.sql
  📄 Applying seeder: 003_carrusel_images.sql
✅ Applied 3 seeder(s) successfully
```

Datos iniciales incluyen:
- Categorías de ejemplo (Perros, Gatos)
- Productos de muestra
- Imágenes del carrusel

### Paso 6: Finalización

```bash
==================================
✅ Database initialization complete!
==================================
Database: distribuidora_db
Status: All migrations and seeders applied successfully
==================================
```

El contenedor `db-migrator` se detiene automáticamente (restart: "no") y los servicios `api` y `worker` inician.

## 🔍 Verificación y Diagnóstico

### Verificar Estado de la Migración

```powershell
# Ver logs del migrator
docker logs distribuidora-db-migrator

# Ver logs de SQL Server
docker logs sqlserver

# Verificar que todos los servicios estén corriendo
docker-compose ps

# Inspeccionar la base de datos
docker exec -it distribuidora-sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#'
```

### Verificar Tablas Creadas

```sql
USE distribuidora_db;
GO

-- Listar todas las tablas
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
GO

-- Contar registros en categorías
SELECT COUNT(*) FROM Categorias;
GO

-- Contar registros en productos
SELECT COUNT(*) FROM Productos;
GO
```

### Verificar Datos de Ejemplo

```sql
-- Ver categorías iniciales
SELECT * FROM Categorias;

-- Ver productos de ejemplo
SELECT p.nombre, c.nombre AS categoria, p.precio 
FROM Productos p
INNER JOIN Categorias c ON p.categoria_id = c.id;

-- Ver imágenes del carrusel
SELECT orden, ruta_imagen, activo FROM CarruselImagenes ORDER BY orden;
```

## 🐛 Solución de Problemas

### Problema 1: "SQL Server not ready yet" por mucho tiempo

**Síntomas**:
```
⏳ SQL Server not ready yet (Attempt 50/60). Waiting 5 seconds...
```

**Diagnóstico**:
```powershell
# Ver logs de SQL Server
docker logs sqlserver

# Verificar uso de memoria
docker stats sqlserver
```

**Soluciones**:
1. **Insuficiente memoria**: SQL Server necesita al menos 2GB
   ```yaml
   # Ya configurado en docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
       reservations:
         memory: 1G
   ```

2. **SQL Server en recuperación**: Esperar más tiempo o reiniciar
   ```powershell
   docker-compose restart sqlserver
   ```

### Problema 2: "Migration failed" en un archivo específico

**Síntomas**:
```
❌ Migration failed: /docker-entrypoint-initdb.d/migrations/005_add_location_fields.sql
```

**Diagnóstico**:
```powershell
# Ver el contenido del archivo problemático
cat sql/migrations/005_add_location_fields.sql

# Ejecutar manualmente para ver el error detallado
docker exec -it distribuidora-sqlserver /opt/mssql-tools/bin/sqlcmd \
    -S localhost -U SA -P 'yourStrongPassword123#' \
    -d distribuidora_db \
    -i /docker-entrypoint-initdb.d/migrations/005_add_location_fields.sql
```

**Soluciones**:
1. **Sintaxis SQL incorrecta**: Revisar y corregir el archivo SQL
2. **Columna/tabla ya existe**: Agregar verificación `IF NOT EXISTS` en la migración
3. **Dependencia faltante**: Asegurar que migraciones anteriores se hayan ejecutado

### Problema 3: Contenedor db-migrator no termina

**Síntomas**:
```powershell
$ docker-compose ps
# db-migrator sigue en estado "running" indefinidamente
```

**Diagnóstico**:
```powershell
# Ver logs en tiempo real
docker logs -f distribuidora-db-migrator

# Ver últimas 100 líneas
docker logs --tail 100 distribuidora-db-migrator
```

**Soluciones**:
1. **Script bloqueado**: Verificar que no haya comandos interactivos
2. **Error silencioso**: Revisar logs para identificar el último paso exitoso
3. **Reiniciar migración**:
   ```powershell
   docker-compose stop db-migrator
   docker-compose rm -f db-migrator
   docker-compose up -d db-migrator
   ```

### Problema 4: "Permission denied" al escribir logs

**Síntomas**:
```
connection_error.log: Permission denied
```

**Solución**:
- Este error no afecta la funcionalidad (el script ya no intenta escribir este archivo)
- La nueva versión del script elimina la dependencia de archivos de log

### Problema 5: API no puede conectar a la base de datos

**Síntomas**:
```
Cannot connect to database: distribuidora_db
```

**Diagnóstico**:
```powershell
# Verificar que db-migrator completó exitosamente
docker-compose ps | grep db-migrator
# Debe mostrar "exited (0)" no "running" o "exited (1)"

# Verificar configuración de la API
docker logs distribuidora-api | grep DB_
```

**Soluciones**:
1. **Nombre de base de datos incorrecto**: Verificar variable `DB_NAME=distribuidora_db`
2. **Password incorrecto**: Verificar `SA_PASSWORD=yourStrongPassword123#`
3. **Migrator no completó**: Reiniciar migración como se mostró arriba

## 🔄 Reiniciar Desde Cero

Si necesitas empezar completamente de cero:

```powershell
# 1. Detener todos los contenedores
docker-compose down

# 2. ELIMINAR VOLÚMENES (⚠️ esto borra todos los datos)
docker-compose down -v

# 3. Eliminar contenedores huérfanos
docker-compose rm -f

# 4. Iniciar todo de nuevo
docker-compose up -d

# 5. Monitorear la migración
docker logs -f distribuidora-db-migrator
```

## 📊 Healthchecks y Dependencias

### SQL Server Healthcheck

```yaml
healthcheck:
  test: >
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA 
    -P 'yourStrongPassword123#' -C -Q 'SELECT 1'
  interval: 30s
  timeout: 20s
  retries: 10
  start_period: 120s  # 2 minutos para inicialización completa
```

### Dependencias de Servicios

```yaml
db-migrator:
  depends_on:
    sqlserver:
      condition: service_healthy  # Espera a que SQL Server esté saludable

api:
  depends_on:
    sqlserver:
      condition: service_healthy
    db-migrator:
      condition: service_completed_successfully  # Espera a que migrator termine

worker:
  depends_on:
    sqlserver:
      condition: service_healthy
    db-migrator:
      condition: service_completed_successfully
```

## 🎓 Mejores Prácticas

### Para Crear Nuevas Migraciones

1. **Nombrar con prefijo numérico**:
   ```
   011_add_campo_nuevo.sql  (siguiente número disponible)
   ```

2. **Usar IF NOT EXISTS para idempotencia**:
   ```sql
   -- Agregar columna solo si no existe
   IF NOT EXISTS (
       SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
       WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'telefono'
   )
   BEGIN
       ALTER TABLE Usuarios ADD telefono NVARCHAR(20);
   END
   GO
   ```

3. **Probar antes de commit**:
   ```powershell
   # Ejecutar la migración manualmente
   docker exec -it distribuidora-sqlserver /opt/mssql-tools/bin/sqlcmd \
       -S localhost -U SA -P 'yourStrongPassword123#' \
       -d distribuidora_db \
       -i /ruta/a/tu/nueva-migracion.sql
   ```

4. **Documentar cambios**:
   ```sql
   -- Migración: 011_add_campo_telefono
   -- Fecha: 2024-01-15
   -- Autor: Tu Nombre
   -- Descripción: Agrega campo telefono a tabla Usuarios para sistema de notificaciones
   ```

### Para Crear Nuevos Seeders

1. **Usar prefijos numéricos** para orden de ejecución:
   ```
   004_nuevos_productos.sql
   ```

2. **Verificar existencia antes de insertar**:
   ```sql
   -- Insertar solo si no existe
   IF NOT EXISTS (SELECT 1 FROM Categorias WHERE nombre = 'Aves')
   BEGIN
       INSERT INTO Categorias (nombre, descripcion, activo)
       VALUES ('Aves', 'Productos para aves', 1);
   END
   GO
   ```

3. **Usar transacciones para datos relacionados**:
   ```sql
   BEGIN TRANSACTION;
   
   -- Insertar categoría
   INSERT INTO Categorias (nombre, descripcion) VALUES ('Peces', 'Productos para peces');
   DECLARE @categoria_id INT = SCOPE_IDENTITY();
   
   -- Insertar productos relacionados
   INSERT INTO Productos (nombre, categoria_id, precio, ...)
   VALUES ('Alimento para peces', @categoria_id, 15.99, ...);
   
   COMMIT TRANSACTION;
   GO
   ```

## 📈 Monitoreo de Performance

### Verificar Tiempo de Migración

```powershell
# Ver tiempo total de ejecución del migrator
docker inspect distribuidora-db-migrator --format='{{.State.StartedAt}} - {{.State.FinishedAt}}'
```

### Verificar Uso de Recursos

```powershell
# Monitorear durante la migración
docker stats sqlserver db-migrator
```

**Tiempos esperados**:
- SQL Server startup: 90-150 segundos
- Schema creation: 5-10 segundos
- Migrations (10 files): 15-30 segundos
- Seeders (3 files): 5-10 segundos
- **Total: 2-3.5 minutos aproximadamente**

## 🔐 Seguridad

### Contraseñas

- **NUNCA** commitear contraseñas reales en docker-compose.yml
- Usar variables de entorno para producción:
  ```yaml
  environment:
    - SA_PASSWORD=${SQL_SERVER_PASSWORD}
  ```

### Acceso a la Base de Datos

- El puerto 1433 NO está expuesto públicamente
- Solo los contenedores en la red `distribuidora-network` pueden acceder
- Para acceso externo, usar túnel SSH o VPN

## 📚 Referencias

- [SQL Server Docker Official Images](https://hub.docker.com/_/microsoft-mssql-server)
- [Docker Compose Healthchecks](https://docs.docker.com/compose/compose-file/05-services/#healthcheck)
- [SQL Server Best Practices](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-files-and-filegroups)

## ✅ Checklist de Verificación Post-Migración

- [ ] El contenedor `db-migrator` tiene estado "exited (0)"
- [ ] Logs de migrator muestran "✅ Database initialization complete!"
- [ ] API está corriendo y responde en http://localhost:8000/health
- [ ] Worker está corriendo sin errores
- [ ] Todas las tablas están creadas (usar consulta SQL arriba)
- [ ] Datos de ejemplo están presentes (categorías, productos)
- [ ] No hay errores en logs de ningún contenedor

---

**¿Tienes problemas?** Revisa la sección de "Solución de Problemas" o abre un issue en GitHub con:
- Logs de `db-migrator` (`docker logs distribuidora-db-migrator`)
- Logs de `sqlserver` (`docker logs sqlserver`)
- Salida de `docker-compose ps`
- Sistema operativo y versión de Docker
