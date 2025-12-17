````markdown
# ⭐ Instrucciones Técnicas para Implementar la HU: "Sistema de Calificaciones y Reseñas de Productos"

**Objetivo**: Implementar la lógica backend para que los clientes puedan calificar y comentar productos que han comprado, y para que los administradores gestionen estas calificaciones. Este documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para crear, leer, actualizar y eliminar calificaciones; gestión de moderación y estadísticas.
- Broker: RabbitMQ — opcional: colas para notificaciones de nuevas calificaciones y recálculo de estadísticas.
- Consumer (Worker): Node.js/TypeScript — opcional: procesar eventos de calificaciones, actualizar stats agregadas.
- Base de datos: SQL Server — tablas `Calificaciones`, `ProductoStats`, `Productos`, `Pedidos`, `Usuarios`.
- Infraestructura: Docker & Docker Compose (`api`, `worker` opcional, `rabbitmq` opcional, `sqlserver`).

---

## 🧾 Modelo de Datos (requerido en BD)
- Tabla `Calificaciones`:
  - `id` (int) — PK, autoincrement
  - `producto_id` (int) — FK a Productos, indexado
  - `usuario_id` (int) — FK a Usuarios, indexado
  - `pedido_id` (int) — FK a Pedidos, indexado
  - `calificacion` (int) — Valor entre 1 y 5 estrellas
  - `comentario` (string, max 500 caracteres) — Texto opcional de la reseña
  - `fecha_creacion` (datetime) — Timestamp de creación
  - `fecha_actualizacion` (datetime) — Timestamp de última actualización
  - `aprobado` (boolean) — Default: true (para moderación futura)
  - `visible` (boolean) — Default: true (permite ocultar sin eliminar)

- Tabla `ProductoStats` (estadísticas precalculadas):
  - `producto_id` (int) — PK
  - `promedio_calificacion` (numeric(3,2)) — Promedio de calificaciones (0.00 - 5.00)
  - `total_calificaciones` (int) — Cantidad total de calificaciones
  - `total_5_estrellas` (int) — Contador de calificaciones con 5 estrellas
  - `total_4_estrellas` (int) — Contador de calificaciones con 4 estrellas
  - `total_3_estrellas` (int) — Contador de calificaciones con 3 estrellas
  - `total_2_estrellas` (int) — Contador de calificaciones con 2 estrellas
  - `total_1_estrella` (int) — Contador de calificaciones con 1 estrella
  - `fecha_actualizacion` (datetime) — Timestamp de última actualización

Notas de persistencia:
- Índices compuestos recomendados: `(producto_id, visible)`, `(usuario_id, pedido_id)`, `(pedido_id, producto_id)`.
- Constraint único: `(usuario_id, pedido_id, producto_id)` para evitar calificaciones duplicadas del mismo producto en el mismo pedido.
- Los stats se actualizan mediante trigger de BD o por Worker/servicio.

---

## 🔗 Flujo Backend (alto nivel)

### Flujo de creación de calificación:
1. Cliente autenticado envía `POST /api/calificaciones` con datos de la calificación.
2. Producer (FastAPI) valida:
   - Usuario autenticado.
   - Campos obligatorios (`producto_id`, `pedido_id`, `calificacion`).
   - `calificacion` entre 1 y 5.
   - Usuario tiene un pedido entregado que contiene el producto.
   - No existe calificación previa para ese `(usuario_id, pedido_id, producto_id)`.
3. Producer inserta registro en `Calificaciones`.
4. Trigger de BD o Worker actualiza `ProductoStats` automáticamente.
5. Producer responde con la calificación creada.

### Flujo de consulta:
- Endpoint público: `GET /api/calificaciones/producto/{producto_id}` — retorna calificaciones visibles de un producto.
- Endpoint público: `GET /api/calificaciones/producto/{producto_id}/stats` — retorna estadísticas agregadas.
- Endpoint de usuario: `GET /api/calificaciones/mis-calificaciones` — retorna todas las calificaciones del usuario autenticado.
- Endpoint de usuario: `GET /api/calificaciones/productos-pendientes` — retorna productos que el usuario puede calificar (pedidos entregados sin calificar).

### Flujo de actualización/eliminación:
- Cliente puede actualizar su calificación: `PUT /api/calificaciones/{rating_id}`.
- Cliente puede eliminar su calificación: `DELETE /api/calificaciones/{rating_id}`.
- Admin puede moderar (ocultar/aprobar) cualquier calificación.

---

## 🧩 Endpoints (Producer — FastAPI)

### Endpoints Públicos (Clientes autenticados)

- **Crear calificación**
  - Método: `POST`
  - Ruta: `/api/calificaciones`
  - Auth: Requiere usuario autenticado (JWT)
  - Payload (JSON):
    ```json
    {
      "producto_id": 123,
      "pedido_id": 456,
      "calificacion": 5,
      "comentario": "Excelente producto, mi gato lo adora"
    }
    ```
  - Validaciones en Producer:
    - `producto_id`, `pedido_id`, `calificacion` obligatorios.
    - `calificacion` debe ser entero entre 1 y 5.
    - `comentario` opcional, max 500 caracteres.
    - Usuario debe tener el pedido con estado "Entregado".
    - Producto debe estar en ese pedido.
    - No puede existir calificación previa para `(usuario_id, pedido_id, producto_id)`.
  - Mensajes exactos para UI:
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (HTTP 400)
    - Calificación fuera de rango: `{ "status": "error", "message": "La calificación debe ser entre 1 y 5 estrellas." }` (HTTP 400)
    - Pedido no entregado: `{ "status": "error", "message": "Solo puedes calificar productos de pedidos entregados." }` (HTTP 403)
    - Producto no en pedido: `{ "status": "error", "message": "Este producto no pertenece al pedido indicado." }` (HTTP 400)
    - Calificación duplicada: `{ "status": "error", "message": "Ya has calificado este producto en este pedido." }` (HTTP 409)
    - Creación exitosa: `{ "status": "success", "message": "Calificación creada exitosamente" }` + objeto `CalificacionResponse` (HTTP 201)

- **Obtener mis calificaciones**
  - Método: `GET`
  - Ruta: `/api/calificaciones/mis-calificaciones`
  - Auth: Requiere usuario autenticado
  - Query params: `skip` (default 0), `limit` (default 100, max 100)
  - Respuesta: Array de `CalificacionResponse`
  ```json
  [
    {
      "id": 1,
      "producto_id": 123,
      "producto_nombre": "Croquetas Premium",
      "usuario_id": 10,
      "usuario_nombre": "Juan Pérez",
      "pedido_id": 456,
      "calificacion": 5,
      "comentario": "Excelente",
      "fecha_creacion": "2025-12-01T10:00:00Z",
      "fecha_actualizacion": "2025-12-01T10:00:00Z",
      "visible": true,
      "aprobado": true
    }
  ]
  ```

- **Obtener calificaciones de un producto (público)**
  - Método: `GET`
  - Ruta: `/api/calificaciones/producto/{producto_id}`
  - Auth: No requiere autenticación
  - Query params: `skip` (default 0), `limit` (default 50, max 100)
  - Retorna solo calificaciones con `visible=true` y `aprobado=true`
  - Respuesta: Array de `CalificacionResponse`

- **Obtener estadísticas de un producto**
  - Método: `GET`
  - Ruta: `/api/calificaciones/producto/{producto_id}/stats`
  - Auth: No requiere autenticación
  - Respuesta: `ProductoStatsResponse`
  ```json
  {
    "producto_id": 123,
    "promedio_calificacion": 4.5,
    "total_calificaciones": 42,
    "total_5_estrellas": 30,
    "total_4_estrellas": 8,
    "total_3_estrellas": 2,
    "total_2_estrellas": 1,
    "total_1_estrella": 1,
    "fecha_actualizacion": "2025-12-02T15:30:00Z"
  }
  ```

- **Obtener productos pendientes de calificar**
  - Método: `GET`
  - Ruta: `/api/calificaciones/productos-pendientes`
  - Auth: Requiere usuario autenticado
  - Respuesta: Array de productos del usuario que fueron entregados y aún no han sido calificados
  ```json
  [
    {
      "producto_id": 123,
      "producto_nombre": "Croquetas Premium",
      "pedido_id": 456,
      "fecha_entrega": "2025-11-28T10:00:00Z"
    }
  ]
  ```

- **Actualizar mi calificación**
  - Método: `PUT`
  - Ruta: `/api/calificaciones/{rating_id}`
  - Auth: Requiere usuario autenticado (solo puede actualizar sus propias calificaciones)
  - Payload:
  ```json
  {
    "calificacion": 4,
    "comentario": "Actualicé mi opinión"
  }
  ```
  - Validaciones:
    - `calificacion` entre 1 y 5 si se proporciona.
    - `comentario` max 500 caracteres si se proporciona.
    - El `rating_id` debe pertenecer al usuario autenticado.
  - Mensajes:
    - No encontrado o no autorizado: `{ "status": "error", "message": "Calificación no encontrada o no tienes permiso para modificarla." }` (HTTP 404)
    - Actualización exitosa: `{ "status": "success", "message": "Calificación actualizada exitosamente" }` + objeto actualizado (HTTP 200)

- **Eliminar mi calificación**
  - Método: `DELETE`
  - Ruta: `/api/calificaciones/{rating_id}`
  - Auth: Requiere usuario autenticado
  - Validaciones: Solo puede eliminar sus propias calificaciones
  - Mensajes:
    - No encontrado o no autorizado: `{ "status": "error", "message": "Calificación no encontrada o no tienes permiso para eliminarla." }` (HTTP 404)
    - Eliminación exitosa: `{ "status": "success", "message": "Calificación eliminada exitosamente" }` (HTTP 200)

---

### Endpoints Admin

- **Listar todas las calificaciones (admin)**
  - Método: `GET`
  - Ruta: `/api/admin/calificaciones`
  - Auth: Requiere admin (`es_admin=true`)
  - Query params:
    - `skip` (default 0), `limit` (default 100, max 100)
    - `producto_id` (optional) — filtrar por producto
    - `usuario_id` (optional) — filtrar por usuario
    - `visible_only` (optional boolean) — si true, solo visibles; si false, solo ocultas; si null, todas
  - Respuesta: `CalificacionesListResponse`
  ```json
  {
    "status": "success",
    "data": [ /* array de CalificacionResponse */ ],
    "meta": {
      "page": 1,
      "pageSize": 100,
      "total": 320
    }
  }
  ```

- **Obtener calificación por ID (admin)**
  - Método: `GET`
  - Ruta: `/api/admin/calificaciones/{rating_id}`
  - Auth: Requiere admin
  - Respuesta: `CalificacionResponse` completo

- **Actualizar calificación (admin — moderación)**
  - Método: `PUT`
  - Ruta: `/api/admin/calificaciones/{rating_id}`
  - Auth: Requiere admin
  - Payload:
  ```json
  {
    "visible": false,
    "aprobado": false
  }
  ```
  - Permite cambiar `visible`, `aprobado` y otros campos
  - Respuesta: `CalificacionResponse` actualizado (HTTP 200)

- **Eliminar calificación (admin)**
  - Método: `DELETE`
  - Ruta: `/api/admin/calificaciones/{rating_id}`
  - Auth: Requiere admin
  - Respuesta: `{ "status": "success", "message": "Calificación eliminada exitosamente" }` (HTTP 200)

- **Recalcular estadísticas de un producto (admin)**
  - Método: `POST`
  - Ruta: `/api/admin/calificaciones/producto/{producto_id}/recalcular-stats`
  - Auth: Requiere admin
  - Acción: Forzar recálculo de `ProductoStats` para el producto
  - Respuesta: `ProductoStatsResponse` actualizado (HTTP 200)

---

## 📨 Broker & Mensajes (opcional)
- Cola: `calificaciones.creada` — publicar cuando se crea una calificación nueva (para analytics, notificaciones).
- Cola: `calificaciones.actualizada` — publicar cuando se actualiza una calificación.
- Cola: `calificaciones.eliminada` — publicar cuando se elimina.
- Cola: `stats.recalcular` — Worker consume y recalcula `ProductoStats`.

Ejemplo de mensaje:
```json
{
  "requestId": "<uuid>",
  "action": "calificacion_creada",
  "payload": {
    "calificacion_id": 123,
    "producto_id": 456,
    "usuario_id": 789,
    "calificacion": 5
  },
  "meta": {
    "timestamp": "2025-12-02T10:00:00Z"
  }
}
```

---

## 🛠 Consumer / Trigger (actualización de estadísticas)

### Opción A: Trigger de SQL Server (recomendado)
- Crear trigger en tabla `Calificaciones` que al INSERT/UPDATE/DELETE recalcula automáticamente `ProductoStats`:
  ```sql
  CREATE TRIGGER trg_UpdateProductoStats
  ON Calificaciones
  AFTER INSERT, UPDATE, DELETE
  AS
  BEGIN
    -- Recalcular stats para los productos afectados
    MERGE INTO ProductoStats AS target
    USING (
      SELECT 
        producto_id,
        AVG(CAST(calificacion AS NUMERIC(3,2))) AS promedio_calificacion,
        COUNT(*) AS total_calificaciones,
        SUM(CASE WHEN calificacion = 5 THEN 1 ELSE 0 END) AS total_5_estrellas,
        SUM(CASE WHEN calificacion = 4 THEN 1 ELSE 0 END) AS total_4_estrellas,
        SUM(CASE WHEN calificacion = 3 THEN 1 ELSE 0 END) AS total_3_estrellas,
        SUM(CASE WHEN calificacion = 2 THEN 1 ELSE 0 END) AS total_2_estrellas,
        SUM(CASE WHEN calificacion = 1 THEN 1 ELSE 0 END) AS total_1_estrella
      FROM Calificaciones
      WHERE producto_id IN (SELECT producto_id FROM inserted UNION SELECT producto_id FROM deleted)
        AND visible = 1 AND aprobado = 1
      GROUP BY producto_id
    ) AS source
    ON target.producto_id = source.producto_id
    WHEN MATCHED THEN
      UPDATE SET
        promedio_calificacion = source.promedio_calificacion,
        total_calificaciones = source.total_calificaciones,
        total_5_estrellas = source.total_5_estrellas,
        total_4_estrellas = source.total_4_estrellas,
        total_3_estrellas = source.total_3_estrellas,
        total_2_estrellas = source.total_2_estrellas,
        total_1_estrella = source.total_1_estrella,
        fecha_actualizacion = GETDATE()
    WHEN NOT MATCHED BY TARGET THEN
      INSERT (producto_id, promedio_calificacion, total_calificaciones, 
              total_5_estrellas, total_4_estrellas, total_3_estrellas,
              total_2_estrellas, total_1_estrella, fecha_actualizacion)
      VALUES (source.producto_id, source.promedio_calificacion, source.total_calificaciones,
              source.total_5_estrellas, source.total_4_estrellas, source.total_3_estrellas,
              source.total_2_estrellas, source.total_1_estrella, GETDATE());
  END;
  ```

### Opción B: Worker (Node.js)
- Consumer escucha cola `calificaciones.creada/actualizada/eliminada`.
- Recalcula stats en memoria y actualiza `ProductoStats`.

---

## ✅ Criterios de Aceptación

### AC 1: Cliente puede calificar producto comprado
- **Condiciones**:
  - Usuario autenticado.
  - Tiene pedido con estado "Entregado" que contiene el producto.
  - No ha calificado previamente el producto en ese pedido.
- **Acciones Backend**:
  - Insertar registro en `Calificaciones`.
  - Actualizar `ProductoStats` automáticamente (trigger o worker).
- **Resultado**: Calificación creada y visible en el producto.

### AC 2: Validación de calificación (1-5 estrellas)
- **Validaciones**:
  - `calificacion` debe ser entero entre 1 y 5.
  - Si fuera de rango: `{ "status": "error", "message": "La calificación debe ser entre 1 y 5 estrellas." }` (HTTP 400)

### AC 3: Comentario opcional con límite de caracteres
- **Validaciones**:
  - `comentario` opcional.
  - Max 500 caracteres.
  - Si excede: `{ "status": "error", "message": "El comentario no puede exceder 500 caracteres." }` (HTTP 400)

### AC 4: Restricción: solo productos de pedidos entregados
- **Validaciones**:
  - Verificar que `Pedidos.estado = 'Entregado'`.
  - Si no: `{ "status": "error", "message": "Solo puedes calificar productos de pedidos entregados." }` (HTTP 403)

### AC 5: Prevención de calificaciones duplicadas
- **Validaciones**:
  - Constraint único en BD: `(usuario_id, pedido_id, producto_id)`.
  - Si ya existe: `{ "status": "error", "message": "Ya has calificado este producto en este pedido." }` (HTTP 409)

### AC 6: Cliente puede actualizar su calificación
- **Endpoint**: `PUT /api/calificaciones/{rating_id}`
- **Validaciones**: Solo el autor puede actualizar.
- **Respuesta**: `{ "status": "success", "message": "Calificación actualizada exitosamente" }`

### AC 7: Cliente puede eliminar su calificación
- **Endpoint**: `DELETE /api/calificaciones/{rating_id}`
- **Validaciones**: Solo el autor puede eliminar.
- **Respuesta**: `{ "status": "success", "message": "Calificación eliminada exitosamente" }`

### AC 8: Visualizar calificaciones de un producto (público)
- **Endpoint**: `GET /api/calificaciones/producto/{producto_id}`
- **Retorna**: Solo calificaciones con `visible=true` y `aprobado=true`.
- **Incluye**: `usuario_nombre`, `calificacion`, `comentario`, `fecha_creacion`.

### AC 9: Visualizar estadísticas agregadas
- **Endpoint**: `GET /api/calificaciones/producto/{producto_id}/stats`
- **Retorna**: `promedio_calificacion`, `total_calificaciones`, distribución por estrellas.

### AC 10: Admin puede moderar calificaciones
- **Endpoints admin**: Listar, ver detalle, actualizar `visible/aprobado`, eliminar.
- **Permisos**: Solo `es_admin=true`.

### AC 11: Ver productos pendientes de calificar
- **Endpoint**: `GET /api/calificaciones/productos-pendientes`
- **Retorna**: Productos de pedidos entregados que el usuario aún no ha calificado.

---

## 🔎 Validaciones exactas

- `producto_id`: entero, requerido, debe existir en `Productos`.
- `pedido_id`: entero, requerido, debe existir en `Pedidos`, debe pertenecer al usuario, debe tener estado "Entregado".
- `calificacion`: entero, requerido, rango 1-5.
- `comentario`: string, opcional, max 500 caracteres.

Mensajes exactos para UI:
- Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
- Calificación fuera de rango: `La calificación debe ser entre 1 y 5 estrellas.`
- Comentario muy largo: `El comentario no puede exceder 500 caracteres.`
- Pedido no entregado: `Solo puedes calificar productos de pedidos entregados.`
- Producto no en pedido: `Este producto no pertenece al pedido indicado.`
- Calificación duplicada: `Ya has calificado este producto en este pedido.`
- Calificación no encontrada/sin permiso: `Calificación no encontrada o no tienes permiso para modificarla.`
- Creación exitosa: `Calificación creada exitosamente`
- Actualización exitosa: `Calificación actualizada exitosamente`
- Eliminación exitosa: `Calificación eliminada exitosamente`

---

## 🔁 Ejemplos de Payloads

### Crear calificación:
```json
POST /api/calificaciones
{
  "producto_id": 123,
  "pedido_id": 456,
  "calificacion": 5,
  "comentario": "Excelente producto"
}
```
Respuesta (201):
```json
{
  "status": "success",
  "message": "Calificación creada exitosamente",
  "id": 789,
  "producto_id": 123,
  "producto_nombre": "Croquetas Premium",
  "usuario_id": 10,
  "usuario_nombre": "Juan Pérez",
  "pedido_id": 456,
  "calificacion": 5,
  "comentario": "Excelente producto",
  "fecha_creacion": "2025-12-02T10:00:00Z",
  "fecha_actualizacion": "2025-12-02T10:00:00Z",
  "visible": true,
  "aprobado": true
}
```

### Actualizar calificación:
```json
PUT /api/calificaciones/789
{
  "calificacion": 4,
  "comentario": "Muy bueno, actualicé mi opinión"
}
```
Respuesta (200): objeto `CalificacionResponse` actualizado

### Obtener stats de producto:
```json
GET /api/calificaciones/producto/123/stats
```
Respuesta (200):
```json
{
  "producto_id": 123,
  "promedio_calificacion": 4.5,
  "total_calificaciones": 42,
  "total_5_estrellas": 30,
  "total_4_estrellas": 8,
  "total_3_estrellas": 2,
  "total_2_estrellas": 1,
  "total_1_estrella": 1,
  "fecha_actualizacion": "2025-12-02T15:30:00Z"
}
```

---

## 🧩 Consideraciones de implementación

- **Concurrencia**: Usar transacciones para evitar race conditions al verificar duplicados.
- **Performance**: Índices en `(producto_id, visible)`, `(usuario_id, pedido_id)`.
- **Moderación**: Implementar flujo de aprobación si se desea revisar comentarios antes de publicarlos (cambiar `aprobado` default a `false`).
- **Notificaciones**: Publicar eventos en RabbitMQ para notificar al vendedor/admin de nuevas calificaciones.
- **Auditoría**: Registrar quién aprobó/ocultó cada calificación en logs o tabla de auditoría.

---

## ✅ Checklist técnico

- [ ] Endpoints públicos implementados: crear, listar por producto, ver stats, productos pendientes.
- [ ] Endpoints de usuario implementados: mis calificaciones, actualizar, eliminar.
- [ ] Endpoints admin implementados: listar todas, ver detalle, moderar (visible/aprobado), eliminar.
- [ ] Validación de restricciones: pedido entregado, producto en pedido, calificación 1-5, comentario max 500.
- [ ] Constraint único en BD: `(usuario_id, pedido_id, producto_id)`.
- [ ] Trigger o Worker actualiza `ProductoStats` automáticamente.
- [ ] Mensajes exactos implementados para toasts frontend.
- [ ] Índices creados para performance.
- [ ] Pruebas: crear calificación válida, intentar duplicar, calificar sin pedido entregado, actualizar, eliminar.

---

## 📌 Notas finales

- Documento exclusivo para backend.
- Los mensajes exactos deben usarse en toasts del frontend.
- Si se implementa moderación (aprobación manual), cambiar default de `aprobado` a `false` y requerir acción admin.
- Trigger de SQL Server es la opción más eficiente para actualizar stats en tiempo real.

---

Archivo: `HU/INSTRUCTIONS_HU_RATINGS_SYSTEM.md`

````
