````markdown
# 📊 Instrucciones Técnicas para Implementar la HU: "Dashboard de Estadísticas del Administrador"

**Objetivo**: Implementar la lógica backend para que un administrador pueda visualizar estadísticas clave del negocio: ventas, pedidos, productos más vendidos, usuarios activos, ingresos y tendencias. Este documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para obtener estadísticas agregadas, métricas de ventas, top productos, usuarios activos, y datos de dashboard.
- Broker: RabbitMQ — opcional: `analytics.events` para publicar eventos de métricas calculadas.
- Consumer (Worker): Node.js/TypeScript — opcional: procesar eventos analytics y actualizar tablas de métricas precalculadas.
- Base de datos: SQL Server — tablas `Pedidos`, `PedidoItems`, `Productos`, `Usuarios`, `Calificaciones`, y tabla opcional `DashboardMetrics` para cache.
- Infraestructura: Docker & Docker Compose (`api`, `worker` opcional, `rabbitmq` opcional, `sqlserver`).

---

## 🧾 Modelo de Datos (opcional para cache)

- Tabla `DashboardMetrics` (opcional - para cache de métricas):
  - `id` (int) — PK
  - `metric_key` (string) — 'total_sales', 'total_orders', 'active_users', etc.
  - `metric_value` (decimal/json) — valor de la métrica
  - `period` (string) — 'daily', 'weekly', 'monthly', 'all_time'
  - `date` (date) — fecha de la métrica
  - `updated_at` (datetime) — timestamp de actualización

Notas:
- Las métricas se pueden calcular en tiempo real o cachear para performance.
- Usar índices en `Pedidos.fecha_creacion`, `Pedidos.estado`, `PedidoItems.producto_id`.

---

## 🔗 Flujo Backend (alto nivel)

1. Admin solicita dashboard mediante `GET /api/admin/dashboard` o endpoints específicos de métricas.
2. Producer (FastAPI) ejecuta queries agregadas en SQL Server para calcular estadísticas.
3. Opcionalmente, Producer consulta tabla `DashboardMetrics` si existe cache reciente.
4. Producer responde con JSON conteniendo todas las métricas para el dashboard.
5. Opcionalmente, Worker recalcula métricas en background y actualiza cache.

---

## 🧩 Endpoints (Producer — FastAPI)

### **Dashboard General**

- **Obtener resumen del dashboard**
  - Método: `GET`
  - Ruta: `/api/admin/dashboard`
  - Auth: Requiere admin (`es_admin=true`)
  - Query params opcionales:
    - `periodo` (string) — 'today', 'week', 'month', 'year', 'all' (default: 'month')
    - `fecha_inicio` (ISO date) — inicio del rango personalizado
    - `fecha_fin` (ISO date) — fin del rango personalizado
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "resumen": {
        "total_ventas": 125000.50,
        "total_pedidos": 342,
        "pedidos_pendientes": 12,
        "pedidos_entregados": 315,
        "pedidos_cancelados": 15,
        "total_usuarios": 156,
        "usuarios_activos": 89,
        "productos_total": 78,
        "productos_sin_stock": 5,
        "calificacion_promedio_general": 4.3
      },
      "ventas_por_dia": [
        { "fecha": "2025-12-01", "total": 3500.00, "pedidos": 12 },
        { "fecha": "2025-12-02", "total": 4200.00, "pedidos": 15 }
      ],
      "top_productos": [
        {
          "producto_id": 123,
          "nombre": "Croquetas Premium",
          "categoria": "Perros",
          "unidades_vendidas": 145,
          "ingresos_totales": 12500.00,
          "calificacion_promedio": 4.8
        }
      ],
      "top_categorias": [
        {
          "categoria_id": 1,
          "nombre": "Perros",
          "total_vendido": 45000.00,
          "porcentaje": 36.0
        }
      ],
      "usuarios_nuevos": [
        { "fecha": "2025-12-01", "count": 5 },
        { "fecha": "2025-12-02", "count": 8 }
      ],
      "estado_inventario": {
        "productos_bajo_stock": 12,
        "productos_sin_stock": 5,
        "valor_inventario_total": 85000.00
      }
    },
    "meta": {
      "periodo": "month",
      "fecha_inicio": "2025-11-01",
      "fecha_fin": "2025-12-02",
      "generado_at": "2025-12-02T15:30:00Z"
    }
  }
  ```

---

### **Métricas de Ventas**

- **Obtener ventas por período**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/ventas`
  - Auth: Requiere admin
  - Query params:
    - `periodo` — 'daily', 'weekly', 'monthly' (default: 'daily')
    - `fecha_inicio`, `fecha_fin` (ISO dates)
    - `agrupar_por` — 'dia', 'semana', 'mes', 'categoria' (default: 'dia')
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": [
      {
        "periodo": "2025-12-01",
        "total_ventas": 3500.00,
        "total_pedidos": 12,
        "ticket_promedio": 291.67,
        "productos_vendidos": 45
      }
    ]
  }
  ```

- **Obtener ingresos totales**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/ingresos`
  - Query params: `fecha_inicio`, `fecha_fin`
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "ingresos_totales": 125000.50,
      "pedidos_totales": 342,
      "ticket_promedio": 365.50,
      "comparacion_periodo_anterior": {
        "cambio_porcentual": 12.5,
        "ingresos_anteriores": 111250.00
      }
    }
  }
  ```

---

### **Métricas de Productos**

- **Obtener productos más vendidos**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/productos/top`
  - Query params:
    - `limit` (default: 10)
    - `fecha_inicio`, `fecha_fin`
    - `categoria_id` (opcional)
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": [
      {
        "producto_id": 123,
        "nombre": "Croquetas Premium",
        "categoria": "Perros",
        "unidades_vendidas": 145,
        "ingresos_totales": 12500.00,
        "stock_actual": 20,
        "calificacion_promedio": 4.8,
        "total_calificaciones": 42
      }
    ]
  }
  ```

- **Obtener productos con bajo stock**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/productos/bajo-stock`
  - Query params:
    - `umbral` (default: 10) — cantidad considerada "bajo stock"
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": [
      {
        "producto_id": 456,
        "nombre": "Arena para Gatos",
        "stock_actual": 3,
        "stock_minimo_recomendado": 20,
        "ultima_venta": "2025-12-01T10:00:00Z",
        "promedio_ventas_diarias": 2.5
      }
    ]
  }
  ```

---

### **Métricas de Usuarios**

- **Obtener usuarios activos**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/usuarios/activos`
  - Query params:
    - `periodo` — 'day', 'week', 'month' (default: 'month')
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "usuarios_activos": 89,
      "usuarios_con_pedidos": 67,
      "usuarios_nuevos": 12,
      "tasa_retencion": 75.5
    }
  }
  ```

- **Obtener usuarios top (por compras)**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/usuarios/top`
  - Query params:
    - `limit` (default: 10)
    - `ordenar_por` — 'total_gastado', 'total_pedidos' (default: 'total_gastado')
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": [
      {
        "usuario_id": 10,
        "nombre": "Juan Pérez",
        "email": "juan@example.com",
        "total_gastado": 5600.00,
        "total_pedidos": 23,
        "ultimo_pedido": "2025-11-30T14:20:00Z",
        "categoria_preferida": "Perros"
      }
    ]
  }
  ```

---

### **Métricas de Pedidos**

- **Obtener distribución de estados de pedidos**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/pedidos/estados`
  - Query params: `fecha_inicio`, `fecha_fin`
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "Pendiente de envío": 12,
      "Enviado": 8,
      "Entregado": 315,
      "Cancelado": 15,
      "total": 350
    }
  }
  ```

- **Obtener tiempo promedio de entrega**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/pedidos/tiempo-entrega`
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "promedio_dias": 3.5,
      "mediana_dias": 3,
      "mas_rapido_dias": 1,
      "mas_lento_dias": 12
    }
  }
  ```

---

### **Métricas de Categorías**

- **Obtener ventas por categoría**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/categorias/ventas`
  - Query params: `fecha_inicio`, `fecha_fin`
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": [
      {
        "categoria_id": 1,
        "nombre": "Perros",
        "total_vendido": 45000.00,
        "unidades_vendidas": 567,
        "porcentaje_total": 36.0,
        "productos_activos": 35
      },
      {
        "categoria_id": 2,
        "nombre": "Gatos",
        "total_vendido": 38000.00,
        "unidades_vendidas": 489,
        "porcentaje_total": 30.4,
        "productos_activos": 28
      }
    ]
  }
  ```

---

### **Métricas de Calificaciones**

- **Obtener resumen de calificaciones**
  - Método: `GET`
  - Ruta: `/api/admin/analytics/calificaciones/resumen`
  - Respuesta:
  ```json
  {
    "status": "success",
    "data": {
      "calificacion_promedio_general": 4.3,
      "total_calificaciones": 856,
      "distribución": {
        "5_estrellas": 512,
        "4_estrellas": 234,
        "3_estrellas": 78,
        "2_estrellas": 21,
        "1_estrella": 11
      },
      "productos_mejor_calificados": [
        {
          "producto_id": 123,
          "nombre": "Croquetas Premium",
          "calificacion_promedio": 4.9,
          "total_calificaciones": 145
        }
      ],
      "productos_peor_calificados": [
        {
          "producto_id": 789,
          "nombre": "Juguete X",
          "calificacion_promedio": 2.1,
          "total_calificaciones": 8
        }
      ]
    }
  }
  ```

---

## 📊 Queries SQL Recomendadas

### Resumen de Ventas

```sql
-- Ventas por día
SELECT 
  CAST(fecha_creacion AS DATE) as fecha,
  COUNT(*) as total_pedidos,
  SUM(total) as total_ventas,
  AVG(total) as ticket_promedio
FROM Pedidos
WHERE estado != 'Cancelado'
  AND fecha_creacion >= @fecha_inicio
  AND fecha_creacion <= @fecha_fin
GROUP BY CAST(fecha_creacion AS DATE)
ORDER BY fecha DESC;
```

### Top Productos

```sql
-- Productos más vendidos
SELECT TOP 10
  p.id as producto_id,
  p.nombre,
  c.nombre as categoria,
  SUM(pi.cantidad) as unidades_vendidas,
  SUM(pi.cantidad * pi.precio_unitario) as ingresos_totales,
  p.cantidad_disponible as stock_actual,
  ps.promedio_calificacion,
  ps.total_calificaciones
FROM PedidoItems pi
INNER JOIN Productos p ON pi.producto_id = p.id
INNER JOIN Categorias c ON p.categoria_id = c.id
LEFT JOIN ProductoStats ps ON ps.producto_id = p.id
INNER JOIN Pedidos ped ON pi.pedido_id = ped.id
WHERE ped.estado != 'Cancelado'
  AND ped.fecha_creacion >= @fecha_inicio
  AND ped.fecha_creacion <= @fecha_fin
GROUP BY p.id, p.nombre, c.nombre, p.cantidad_disponible, ps.promedio_calificacion, ps.total_calificaciones
ORDER BY ingresos_totales DESC;
```

### Usuarios Activos

```sql
-- Usuarios con pedidos en el período
SELECT COUNT(DISTINCT usuario_id) as usuarios_activos
FROM Pedidos
WHERE fecha_creacion >= @fecha_inicio
  AND fecha_creacion <= @fecha_fin;
```

### Ventas por Categoría

```sql
-- Distribución de ventas por categoría
SELECT 
  c.id as categoria_id,
  c.nombre,
  SUM(pi.cantidad * pi.precio_unitario) as total_vendido,
  SUM(pi.cantidad) as unidades_vendidas,
  COUNT(DISTINCT p.id) as productos_activos
FROM PedidoItems pi
INNER JOIN Productos p ON pi.producto_id = p.id
INNER JOIN Categorias c ON p.categoria_id = c.id
INNER JOIN Pedidos ped ON pi.pedido_id = ped.id
WHERE ped.estado != 'Cancelado'
  AND ped.fecha_creacion >= @fecha_inicio
  AND ped.fecha_creacion <= @fecha_fin
GROUP BY c.id, c.nombre
ORDER BY total_vendido DESC;
```

---

## 📨 Broker & Mensajes (opcional)

- Cola: `analytics.metrics_updated` — publicar cuando se actualizan métricas
- Mensaje ejemplo:
```json
{
  "requestId": "<uuid>",
  "action": "metrics_updated",
  "payload": {
    "metric_keys": ["total_sales", "total_orders"],
    "period": "daily",
    "date": "2025-12-02"
  },
  "meta": {
    "timestamp": "2025-12-02T23:59:59Z"
  }
}
```

---

## 🛠 Consumer (Worker — opcional)

- Calcular métricas en background (ej: cada hora o diariamente)
- Actualizar tabla `DashboardMetrics` con valores precalculados
- Publicar eventos de actualización

---

## ✅ Criterios de Aceptación

### AC 1: Dashboard muestra resumen general
- **Endpoint**: `GET /api/admin/dashboard`
- **Métricas incluidas**:
  - Total ventas del período
  - Total pedidos (y por estado)
  - Usuarios activos
  - Productos sin stock
  - Calificación promedio general

### AC 2: Gráficas de ventas por período
- **Endpoint**: `GET /api/admin/analytics/ventas`
- **Soporta agrupación**: día, semana, mes
- **Incluye**: total ventas, pedidos, ticket promedio

### AC 3: Top productos más vendidos
- **Endpoint**: `GET /api/admin/analytics/productos/top`
- **Orden**: por ingresos o unidades vendidas
- **Incluye**: calificación promedio, stock actual

### AC 4: Alertas de inventario bajo
- **Endpoint**: `GET /api/admin/analytics/productos/bajo-stock`
- **Umbral configurable**
- **Incluye**: promedio ventas diarias, última venta

### AC 5: Usuarios top y estadísticas de retención
- **Endpoints**: 
  - `GET /api/admin/analytics/usuarios/top`
  - `GET /api/admin/analytics/usuarios/activos`
- **Métricas**: total gastado, pedidos, tasa retención

### AC 6: Comparación con períodos anteriores
- **En endpoint de ingresos**
- **Muestra**: cambio porcentual vs período anterior

---

## 🔎 Validaciones

- **Autenticación**: Todos los endpoints requieren `es_admin=true`
- **Fechas**: Validar formato ISO y que `fecha_inicio <= fecha_fin`
- **Período**: Solo valores válidos ('today', 'week', 'month', 'year', 'all')

Mensajes de error:
```json
{ "status": "error", "message": "Acceso denegado. Se requieren permisos de administrador." }
{ "status": "error", "message": "Rango de fechas inválido." }
{ "status": "error", "message": "Período no válido." }
```

---

## 🔁 Ejemplos de Uso

### Dashboard general del mes actual

```bash
GET /api/admin/dashboard?periodo=month
```

### Top 5 productos más vendidos en el último trimestre

```bash
GET /api/admin/analytics/productos/top?limit=5&fecha_inicio=2025-09-01&fecha_fin=2025-12-02
```

### Productos con menos de 5 unidades en stock

```bash
GET /api/admin/analytics/productos/bajo-stock?umbral=5
```

---

## 🧩 Consideraciones de Implementación

- **Performance**: Usar índices en columnas de fecha y estado
- **Cache**: Considerar cachear métricas del dashboard (TTL 5-15 min)
- **Agregación**: Usar vistas materializadas o tablas precalculadas para métricas pesadas
- **Paginación**: Aplicar en endpoints que puedan retornar muchos resultados
- **Filtros**: Todos los endpoints soportan filtrado por rango de fechas

---

## ✅ Checklist Técnico

- [ ] Endpoint `GET /api/admin/dashboard` implementado con resumen completo
- [ ] Endpoints de analytics de ventas con agrupación por período
- [ ] Top productos con filtros y ordenamiento
- [ ] Productos bajo stock con umbral configurable
- [ ] Usuarios activos y top usuarios
- [ ] Distribución de pedidos por estado
- [ ] Ventas por categoría con porcentajes
- [ ] Resumen de calificaciones agregadas
- [ ] Comparación con período anterior
- [ ] Autenticación admin en todos los endpoints
- [ ] Índices en tablas para performance
- [ ] Cache opcional para métricas frecuentes

---

## 📌 Notas Finales

- Documento exclusivo para backend
- Métricas pueden calcularse en tiempo real o cachear según volumen
- Considerar usar Redis para cache de dashboard si el volumen es alto
- Worker opcional puede recalcular métricas en background para mejor UX

---

**Archivo**: `HU/INSTRUCTIONS_HU_ADMIN_DASHBOARD.md`

````
