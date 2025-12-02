# ✅ Checklist de Post-Instalación

Usa este checklist para verificar que la instalación fue exitosa y el proyecto está completamente funcional.

## 📋 Checklist Básico

### ✅ Backend (Docker)

- [ ] Docker Desktop está instalado y corriendo
- [ ] Ejecutaste `.\INSTALL.ps1` en la carpeta del backend sin errores
- [ ] Los 4 contenedores están corriendo:
  ```powershell
  docker ps
  # Deberías ver:
  # - distribuidora-api
  # - distribuidora-worker
  # - sqlserver
  # - rabbitmq
  ```
- [ ] SQL Server está saludable:
  ```powershell
  docker inspect sqlserver --format='{{.State.Health.Status}}'
  # Debería mostrar: healthy
  ```
- [ ] RabbitMQ está saludable:
  ```powershell
  docker inspect rabbitmq --format='{{.State.Health.Status}}'
  # Debería mostrar: healthy
  ```
- [ ] La API responde correctamente:
  - Abre http://localhost:8000/docs
  - Deberías ver la documentación Swagger

### ✅ Frontend (React)

- [ ] Node.js está instalado (versión 16+):
  ```powershell
  node --version
  # Debería mostrar v16.x.x o superior
  ```
- [ ] Ejecutaste `.\INSTALL.ps1` en la carpeta del frontend sin errores
- [ ] El archivo `.env` existe y contiene:
  ```
  REACT_APP_API_URL=http://localhost:8000/api
  REACT_APP_ENV=development
  ```
- [ ] La carpeta `node_modules` existe
- [ ] Puedes iniciar el servidor sin errores:
  ```powershell
  npm start
  ```
- [ ] La aplicación se abre en http://localhost:3000
- [ ] La página principal se carga correctamente

---

## 🔍 Checklist Avanzado

### ✅ Conectividad Backend-Frontend

- [ ] El frontend puede comunicarse con el backend:
  - Abre http://localhost:3000
  - La consola del navegador (F12) no muestra errores de conexión
  - Los productos se cargan en la página principal

- [ ] El carrusel de imágenes funciona correctamente

- [ ] Los filtros de categorías funcionan

### ✅ Base de Datos

- [ ] La base de datos `distribuidora_db` existe:
  ```powershell
  docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q "SELECT name FROM sys.databases WHERE name='distribuidora_db'"
  ```

- [ ] Las tablas principales existen:
  ```powershell
  docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -d distribuidora_db -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
  ```
  Deberías ver: Usuarios, Productos, Categorias, Pedidos, etc.

### ✅ Sistema de Mensajería (RabbitMQ)

- [ ] RabbitMQ Admin UI es accesible:
  - Abre http://localhost:15672
  - Login: guest / guest
  - Deberías ver el dashboard

- [ ] Las colas están configuradas (pueden estar vacías)

### ✅ Funcionalidades Principales

#### Usuarios
- [ ] Puedes acceder a la página de registro
- [ ] Puedes acceder a la página de login
- [ ] El formulario de registro se muestra correctamente

#### Productos
- [ ] Los productos se muestran en la página principal
- [ ] Puedes hacer clic en un producto y ver sus detalles
- [ ] El carrito de compras funciona (icono se actualiza)

#### Navegación
- [ ] El header se muestra correctamente con el logo
- [ ] Los botones de navegación funcionan
- [ ] El footer se muestra con los enlaces de redes sociales

---

## 🎯 Pruebas Funcionales

### Test 1: Registro de Usuario

1. [ ] Ve a http://localhost:3000/registro
2. [ ] Completa el formulario con datos válidos
3. [ ] Haz clic en "Registrarse"
4. [ ] Deberías ser redirigido a verificación de email
5. [ ] Verifica los logs del worker:
   ```powershell
   docker-compose logs worker
   # Deberías ver el intento de envío de email
   ```

### Test 2: Navegación de Productos

1. [ ] Ve a http://localhost:3000
2. [ ] Verifica que el carrusel de imágenes funciona
3. [ ] Haz clic en un filtro de categoría
4. [ ] Los productos deberían filtrarse
5. [ ] Haz clic en "Todos" para ver todos los productos

### Test 3: Carrito de Compras

1. [ ] Haz clic en "Agregar al carrito" en un producto
2. [ ] El contador del carrito debería aumentar
3. [ ] Ve a /carrito
4. [ ] Deberías ver el producto agregado
5. [ ] Puedes modificar la cantidad
6. [ ] Puedes eliminar el producto

### Test 4: API Backend

1. [ ] Ve a http://localhost:8000/docs
2. [ ] Expande el endpoint GET `/api/home/productos`
3. [ ] Haz clic en "Try it out" y luego "Execute"
4. [ ] Deberías recibir una respuesta 200 con lista de productos

### Test 5: Logs y Monitoreo

1. [ ] Ver logs de la API:
   ```powershell
   docker-compose logs -f api
   ```
   Deberías ver las peticiones HTTP llegando

2. [ ] Ver logs del Worker:
   ```powershell
   docker-compose logs -f worker
   ```
   Debería estar escuchando mensajes de RabbitMQ

---

## 🚨 Problemas Comunes y Soluciones

### ❌ El backend no inicia

**Síntomas:**
- Contenedor `distribuidora-api` no aparece en `docker ps`
- Logs muestran errores de conexión

**Soluciones:**
1. Verificar que SQL Server esté saludable:
   ```powershell
   docker inspect sqlserver --format='{{.State.Health.Status}}'
   ```
2. Esperar 2-3 minutos más (SQL Server es lento)
3. Reiniciar contenedores:
   ```powershell
   docker-compose restart
   ```

### ❌ Frontend no puede conectar con backend

**Síntomas:**
- Console del navegador muestra errores CORS o Network
- Productos no cargan

**Soluciones:**
1. Verificar que el backend esté corriendo:
   ```powershell
   docker ps | Select-String "distribuidora-api"
   ```
2. Verificar `.env`:
   ```powershell
   cat .env
   # Debe contener: REACT_APP_API_URL=http://localhost:8000/api
   ```
3. Reiniciar el servidor React (Ctrl+C, luego npm start)

### ❌ Puerto en uso

**Síntomas:**
- Error: "port 8000 is already in use"
- Error: "port 3000 is already in use"

**Soluciones:**
```powershell
# Encontrar proceso usando puerto 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Get-Process -Id <PID> | Stop-Process -Force

# O cambiar puerto en docker-compose.yml (backend) o aceptar puerto alternativo (frontend)
```

---

## ✅ Verificación Automática

**La forma más fácil de verificar todo:**

```powershell
.\HEALTH-CHECK.ps1
```

Este script verifica automáticamente todos los puntos del checklist.

---

## 📝 Notas Finales

### Primer Uso Exitoso

Si completaste este checklist sin errores, ¡felicitaciones! 🎉

Tu instalación está completa y puedes comenzar a:
- Desarrollar nuevas funcionalidades
- Hacer pruebas
- Explorar el código

### Configuración Adicional

Para personalizar el proyecto:
- Revisa `CONFIGURACION.md` para cambiar configuraciones
- Revisa `SCRIPTS.md` para conocer todos los comandos disponibles

### Mantenimiento

Después de la instalación:
- Usa `.\START.ps1` para iniciar el proyecto diariamente
- Usa `.\STOP.ps1` para detener cuando termines
- Usa `.\HEALTH-CHECK.ps1` si algo no funciona

---

**¿Todo funcionando? ¡Excelente! Ahora estás listo para desarrollar! 🚀**

**¿Encontraste problemas?** Consulta:
- `INSTALACION_RAPIDA.md` - Guía detallada de instalación
- `SCRIPTS.md` - Documentación de scripts
- Logs de Docker: `docker-compose logs -f`
