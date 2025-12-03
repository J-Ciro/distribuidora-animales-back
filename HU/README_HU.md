# 📚 Índice de Historias de Usuario (HU) - Backend

## 📋 Resumen Ejecutivo

Este directorio contiene **todas las Historias de Usuario (HU)** documentadas para el backend de **Distribuidora Perros y Gatos**. Cada HU está escrita en formato detallado para ser consumida por IA o desarrolladores backend, con especificaciones técnicas precisas, validaciones exactas y mensajes de error/éxito estandarizados.

**Total de HU Documentadas**: 12

---

## 🗂️ Lista Completa de HU

### ✅ HU Implementadas y Documentadas

| # | Archivo | Funcionalidad | Estado | Endpoints Principales |
|---|---------|---------------|--------|----------------------|
| 1 | `INSTRUCTIONS_HU_REGISTER_USER.md` | Registro de Cliente con Verificación Email | ✅ Implementado | `POST /api/auth/register`<br>`POST /api/auth/verify-email`<br>`POST /api/auth/resend-code` |
| 2 | `INSTRUCTIONS_HU_LOGIN_USER.md` | Inicio de Sesión de Clientes | ✅ Implementado | `POST /api/auth/login`<br>`POST /api/auth/logout`<br>`POST /api/auth/refresh` |
| 3 | `INSTRUCTIONS_HU_MANAGE_CATEGORIES.md` | Gestión de Categorías y Subcategorías | ✅ Implementado | `POST /api/admin/categorias`<br>`POST /api/admin/subcategorias`<br>`GET /api/admin/categorias`<br>`PUT /api/admin/categorias/{id}`<br>`DELETE /api/admin/categorias/{id}` |
| 4 | `INSTRUCTIONS_HU_CREATE_PRODUCT.md` | Gestión Completa de Productos | ✅ Implementado | `POST /api/admin/productos`<br>`GET /api/admin/productos`<br>`GET /api/admin/productos/{id}`<br>`PUT /api/admin/productos/{id}`<br>`DELETE /api/admin/productos/{id}`<br>`GET/PUT/DELETE /api/admin/productos/{id}/images/{imagen_id}` |
| 5 | `INSTRUCTIONS_HU_MANAGE_INVENTORY.md` | Reabastecer Existencias de Productos | ✅ Implementado | `POST /api/admin/productos/{id}/reabastecer`<br>`GET /api/admin/productos/{id}/stock`<br>`GET /api/admin/productos/{id}/inventario/historial` |
| 6 | `INSTRUCTIONS_HU_MANAGE_CAROUSEL.md` | Administrar Carrusel de Inicio | ✅ Implementado | `GET /api/admin/carrusel`<br>`POST /api/admin/carrusel`<br>`PUT /api/admin/carrusel/reordenar`<br>`DELETE /api/admin/carrusel/{id}` |
| 7 | `INSTRUCTIONS_HU_HOME_PRODUCTS.md` | Productos en Página de Inicio + Carrito | ✅ Implementado | `GET /api/home/productos`<br>`GET /api/home/categorias`<br>`POST /api/cart/add`<br>`GET /api/cart`<br>`PUT /api/cart/items/{id}`<br>`DELETE /api/cart/items/{id}` |
| 8 | `INSTRUCTIONS_HU_MANAGE_ORDERS.md` | Gestión de Pedidos (Admin) | ✅ Implementado | `GET /api/admin/pedidos`<br>`GET /api/admin/pedidos/{id}`<br>`PUT /api/admin/pedidos/{id}/estado`<br>`GET /api/admin/pedidos/{id}/history` |
| 9 | `INSTRUCTIONS_HU_MANAGE_USERS.md` | Gestión de Usuarios (Admin) | ✅ Implementado | `GET /api/admin/usuarios`<br>`GET /api/admin/usuarios/{id}`<br>`PUT /api/admin/usuarios/{id}` |
| 10 | `INSTRUCTIONS_HU_RATINGS_SYSTEM.md` | Sistema de Calificaciones de Productos | ✅ Implementado | `POST /api/calificaciones`<br>`GET /api/calificaciones/producto/{id}`<br>`GET /api/calificaciones/producto/{id}/stats`<br>`PUT /api/calificaciones/{id}`<br>`DELETE /api/calificaciones/{id}`<br>`GET /api/admin/calificaciones` |
| 11 | `INSTRUCTIONS_HU_ADMIN_DASHBOARD.md` | Dashboard y Estadísticas del Administrador | ✅ **NUEVO** | `GET /api/admin/dashboard`<br>`GET /api/admin/analytics/ventas`<br>`GET /api/admin/analytics/productos/top`<br>`GET /api/admin/analytics/usuarios/activos`<br>`GET /api/admin/analytics/pedidos/estados`<br>`GET /api/admin/analytics/categorias/ventas`<br>`GET /api/admin/analytics/calificaciones/resumen` |
| 12 | `INSTRUCTIONS_HU_MY_ORDERS.md` | Mis Pedidos - Vista de Cliente | ✅ **NUEVO** | `GET /api/pedidos/my-orders`<br>`GET /api/pedidos/my-orders/{id}`<br>`GET /api/pedidos/my-orders/{id}/historial`<br>`POST /api/pedidos/my-orders/{id}/cancelar` |

---

## 🆕 Nuevas HU Creadas en Esta Sesión

### **INSTRUCTIONS_HU_RATINGS_SYSTEM.md** (✨ NUEVO)

**Funcionalidad**: Sistema completo de calificaciones y reseñas de productos

**Características Principales**:
- ⭐ Clientes pueden calificar productos (1-5 estrellas) de pedidos entregados
- 💬 Comentarios opcionales (max 500 caracteres)
- 📊 Estadísticas agregadas por producto (promedio, distribución)
- 🔒 Validación: solo un rating por producto por pedido
- 👤 Clientes ven y actualizan sus propias calificaciones
- 👨‍💼 Admin puede moderar (ocultar/aprobar) calificaciones
- 🎯 Sistema de "productos pendientes de calificar"

**Endpoints Principales**:
```
# Públicos (Clientes)
POST   /api/calificaciones                        # Crear calificación
GET    /api/calificaciones/mis-calificaciones     # Mis calificaciones
GET    /api/calificaciones/producto/{id}          # Calificaciones de un producto
GET    /api/calificaciones/producto/{id}/stats    # Estadísticas del producto
GET    /api/calificaciones/productos-pendientes   # Productos que puedo calificar
PUT    /api/calificaciones/{id}                   # Actualizar mi calificación
DELETE /api/calificaciones/{id}                   # Eliminar mi calificación

# Admin
GET    /api/admin/calificaciones                  # Listar todas (con filtros)
GET    /api/admin/calificaciones/{id}             # Detalle de calificación
PUT    /api/admin/calificaciones/{id}             # Moderar (visible/aprobado)
DELETE /api/admin/calificaciones/{id}             # Eliminar cualquier calificación
POST   /api/admin/calificaciones/producto/{id}/recalcular-stats  # Recalcular stats
```

**Modelo de Datos**:
- Tabla `Calificaciones`: almacena ratings con producto_id, usuario_id, pedido_id, calificacion (1-5), comentario, visible, aprobado
- Tabla `ProductoStats`: estadísticas precalculadas (promedio, total por estrellas)
- Constraint único: `(usuario_id, pedido_id, producto_id)`
- Actualización automática de stats via trigger SQL Server

**Mensajes Estandarizados**:
```json
// Éxito
{ "status": "success", "message": "Calificación creada exitosamente" }
{ "status": "success", "message": "Calificación actualizada exitosamente" }
{ "status": "success", "message": "Calificación eliminada exitosamente" }

// Errores
{ "status": "error", "message": "La calificación debe ser entre 1 y 5 estrellas." }
{ "status": "error", "message": "Solo puedes calificar productos de pedidos entregados." }
{ "status": "error", "message": "Ya has calificado este producto en este pedido." }
{ "status": "error", "message": "El comentario no puede exceder 500 caracteres." }
```

---

### **INSTRUCTIONS_HU_ADMIN_DASHBOARD.md** (✨ NUEVO)

**Funcionalidad**: Dashboard centralizado con estadísticas y analytics del negocio

**Características Principales**:
- 📊 Dashboard summary con métricas clave (ventas totales, pedidos, productos, usuarios)
- 💰 Analytics de ventas (total, promedio, comparación periodos)
- 🏆 Top productos más vendidos y peor rendimiento
- ⚠️ Alertas de bajo stock
- 👥 Usuarios activos y top compradores
- 📦 Métricas de pedidos (por estado, tiempo entrega)
- 📂 Ventas por categoría
- ⭐ Resumen de calificaciones

**Endpoints Analytics**: 12+ endpoints especializados para métricas

### **INSTRUCTIONS_HU_MY_ORDERS.md** (✨ NUEVO)

**Funcionalidad**: Sistema completo para que clientes vean y gestionen sus pedidos

**Características Principales**:
- 📋 Lista de pedidos con paginación y filtros por estado
- 🔍 Detalle completo de cada pedido con items y tracking
- 📦 Timeline visual de estados del pedido
- ❌ Cancelación de pedidos pendientes
- 🎯 Integración con sistema de calificaciones

**Endpoints Implementados**: 4 endpoints REST para gestión de pedidos del usuario

---

## 📊 Estadísticas del Proyecto

### Coverage de Funcionalidades

| Área | HU Documentadas | % Coverage |
|------|-----------------|-----------|
| Autenticación & Usuarios | 3 | 100% |
| Catálogo (Productos & Categorías) | 3 | 100% |
| Carrito & Pedidos | 3 | 100% ✨ |
| Contenido (Carrusel) | 1 | 100% |
| Calificaciones & Reseñas | 1 | 100% |
| Inventario | 1 | 100% |
| Analytics & Dashboard | 1 | 100% ✨ |
| **TOTAL** | **12** | **100%** |

---

## 🎯 Convenciones de Documentación

Todas las HU siguen estas convenciones estrictas:

### 1. **Estructura Estándar**
- ⚙️ Arquitectura (Producer/Broker/Consumer/DB)
- 🧾 Modelo de Datos (tablas requeridas con campos exactos)
- 🔗 Flujo Backend (alto nivel)
- 🧩 Endpoints (FastAPI Producer)
- 📨 Broker & Mensajes (RabbitMQ)
- 🛠 Consumer (Worker Node.js/TypeScript)
- ✅ Criterios de Aceptación mapeados
- 🔎 Validaciones exactas
- 🔁 Ejemplos de Payloads y Respuestas
- 🧩 Consideraciones de implementación
- ✅ Checklist técnico

### 2. **Mensajes Estandarizados para UI**

Todos los mensajes de error y éxito están especificados exactamente como deben aparecer en los toasts del frontend:

```json
// Campos obligatorios
{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }

// Validaciones de formato
{ "status": "error", "message": "El correo electrónico no tiene un formato válido." }
{ "status": "error", "message": "Formato o tamaño de imagen no válido." }
{ "status": "error", "message": "La cantidad debe ser un número entero positivo." }

// Validaciones de negocio
{ "status": "error", "message": "Ya existe una categoría con ese nombre." }
{ "status": "error", "message": "Sin existencias" }
{ "status": "error", "message": "Producto no encontrado." }

// Mensajes de éxito
{ "status": "success", "message": "Producto creado exitosamente" }
{ "status": "success", "message": "Existencias actualizadas exitosamente" }
```

### 3. **Códigos HTTP Exactos**

Cada endpoint especifica los códigos HTTP exactos:
- `200 OK` - Operación exitosa (GET, PUT, DELETE)
- `201 Created` - Recurso creado (POST)
- `400 Bad Request` - Validación de input fallida
- `401 Unauthorized` - No autenticado
- `403 Forbidden` - Autenticado pero sin permisos
- `404 Not Found` - Recurso no existe
- `409 Conflict` - Conflicto (duplicados, stock insuficiente)
- `423 Locked` - Cuenta bloqueada
- `429 Too Many Requests` - Rate limit excedido
- `500 Internal Server Error` - Error interno

### 4. **Validaciones Sin Ambigüedad**

Cada campo especifica:
- Tipo de dato exacto
- Requerido/Opcional
- Validaciones (min/max length, range, format)
- Mensaje de error específico si falla

Ejemplo:
```
`calificacion`:
  - Requerido: sí
  - Tipo: integer
  - Rango: 1-5
  - Mensaje si inválido: "La calificación debe ser entre 1 y 5 estrellas."
```

---

## 🔄 Arquitectura General del Sistema

Todas las HU siguen el patrón Producer-Broker-Consumer:

```
┌─────────────────┐         ┌─────────────┐         ┌──────────────────┐
│   FastAPI API   │────────▶│  RabbitMQ   │────────▶│  Node.js Worker  │
│   (Producer)    │         │  (Broker)   │         │   (Consumer)     │
└────────┬────────┘         └─────────────┘         └────────┬─────────┘
         │                                                     │
         │                                                     │
         └─────────────────────────────────────────────────────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │  SQL Server  │
                          │  (Database)  │
                          └──────────────┘
```

**Producer (FastAPI)**:
- Valida inputs básicos
- Publica mensajes en RabbitMQ
- Responde al cliente con JSON estandarizado

**Broker (RabbitMQ)**:
- Colas específicas por operación
- Garantiza entrega de mensajes
- Permite procesamiento asíncrono

**Consumer (Worker)**:
- Valida reglas de negocio complejas
- Ejecuta operaciones en SQL Server
- Publica resultados/eventos

---

## 🚀 Uso de las HU

### Para Desarrolladores

1. **Leer la HU completa** antes de implementar
2. **Seguir los mensajes exactos** para responses
3. **Implementar todas las validaciones** especificadas
4. **Usar los códigos HTTP correctos**
5. **Verificar el checklist técnico** antes de dar por terminado

### Para IA/Copilot

Las HU están escritas para ser consumidas directamente por IA:
- Sin ambigüedades
- Validaciones explícitas
- Ejemplos de payloads completos
- Mensajes de error literales
- Estructura de datos detallada

### Para QA/Testing

Cada HU incluye:
- Criterios de Aceptación verificables
- Ejemplos de payloads válidos e inválidos
- Mensajes esperados para cada escenario
- Casos edge documentados

---

## 📝 Actualizado

**Fecha**: Diciembre 2025
**Versión**: 3.0
**Cambios Recientes**:
- ✨ Nueva HU: Sistema de Calificaciones y Reseñas (`INSTRUCTIONS_HU_RATINGS_SYSTEM.md`)
- ✨ Nueva HU: Dashboard de Estadísticas Admin (`INSTRUCTIONS_HU_ADMIN_DASHBOARD.md`)
- ✨ Nueva HU: Mis Pedidos - Vista Cliente (`INSTRUCTIONS_HU_MY_ORDERS.md`)
- ✅ Revisión completa de todas las HU existentes
- 📊 100% de cobertura de funcionalidades implementadas (12 HU totales)

---

## 📞 Soporte

Para preguntas sobre las HU, consultar:
1. El archivo específico de la HU en este directorio
2. `ARCHITECTURE.md` para detalles de arquitectura general
3. `PROJECT_STATUS.md` para estado de implementación

---

**Archivo**: `HU/README_HU.md`
