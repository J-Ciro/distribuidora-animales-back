````markdown
# 📦 Instrucciones Técnicas para Implementar la HU: "Mis Pedidos - Vista de Cliente"

**Objetivo**: Implementar la lógica backend y frontend para que un cliente autenticado pueda visualizar todos sus pedidos, ver el detalle de cada pedido, rastrear el estado de envío y acceder al historial completo de compras. Este documento está pensado para ser leído y ejecutado por una IA o por un desarrollador.

---

## ⚙️ Alcance

### Backend (FastAPI)
- Endpoints REST para listar pedidos del usuario, ver detalle, consultar historial de estados
- Validación de pertenencia (usuario solo ve sus propios pedidos)
- Filtrado y ordenamiento

### Frontend (React)
- Página "Mis Pedidos" con lista de pedidos
- Modal/página de detalle con items y tracking
- Estados visuales (pendiente, enviado, entregado, cancelado)
- Historial de cambios de estado

---

## 🧾 Modelo de Datos (Backend)

Tablas principales:
- `Pedidos`:
  - `id`, `usuario_id`, `fecha_creacion`, `total`, `estado`, `direccion_envio`
  - Estados: 'Pendiente de envío', 'Enviado', 'Entregado', 'Cancelado'
  
- `PedidoItems`:
  - `id`, `pedido_id`, `producto_id`, `cantidad`, `precio_unitario`
  
- `PedidosHistorialEstado` (opcional - para tracking):
  - `id`, `pedido_id`, `estado_anterior`, `estado_nuevo`, `comentario`, `created_at`

Índices recomendados:
- `Pedidos(usuario_id, fecha_creacion DESC)`
- `PedidoItems(pedido_id)`

---

## 🔗 Flujo Backend

1. Cliente autenticado solicita `GET /api/pedidos/mis-pedidos`
2. Producer (FastAPI) valida JWT y extrae `usuario_id`
3. Query filtra `Pedidos WHERE usuario_id = :usuario_id`
4. Para cada pedido, obtener items desde `PedidoItems`
5. Responder con array de pedidos ordenados por fecha DESC (más recientes primero)

---

## 🧩 Endpoints Backend (FastAPI)

### **Listar mis pedidos**

- **Método**: `GET`
- **Ruta**: `/api/pedidos/mis-pedidos` o `/api/orders/mis-pedidos`
- **Auth**: Requiere usuario autenticado (JWT)
- **Query params**:
  - `skip` (default: 0)
  - `limit` (default: 20, max: 100)
  - `estado` (opcional) — filtrar por estado específico
  - `fecha_desde`, `fecha_hasta` (ISO dates) — rango de fechas
- **Respuesta**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 456,
      "fecha_creacion": "2025-11-28T10:30:00Z",
      "total": 2850.00,
      "estado": "Entregado",
      "direccion_envio": "Calle 123, Ciudad",
      "items_count": 3,
      "fecha_entrega": "2025-11-30T14:20:00Z"
    },
    {
      "id": 457,
      "fecha_creacion": "2025-12-01T15:00:00Z",
      "total": 1200.00,
      "estado": "Enviado",
      "direccion_envio": "Calle 456, Ciudad",
      "items_count": 1,
      "fecha_estimada_entrega": "2025-12-04"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 12
  }
}
```

**Códigos HTTP**:
- `200 OK` — pedidos retornados (puede ser array vacío)
- `401 Unauthorized` — no autenticado

**Mensajes**:
- Si no hay pedidos: retornar `data: []` (no error)

---

### **Obtener detalle de un pedido**

- **Método**: `GET`
- **Ruta**: `/api/pedidos/mis-pedidos/{pedido_id}`
- **Auth**: Requiere usuario autenticado
- **Validación**: Verificar que `pedido.usuario_id == current_user.id`
- **Respuesta**:
```json
{
  "status": "success",
  "data": {
    "id": 456,
    "fecha_creacion": "2025-11-28T10:30:00Z",
    "fecha_actualizacion": "2025-11-30T14:20:00Z",
    "total": 2850.00,
    "estado": "Entregado",
    "direccion_envio": "Calle 123, Apt 4B, Ciudad, CP 12345",
    "items": [
      {
        "id": 1,
        "producto_id": 123,
        "producto_nombre": "Croquetas Premium",
        "producto_imagen": "https://...",
        "cantidad": 2,
        "precio_unitario": 1200.00,
        "subtotal": 2400.00
      },
      {
        "id": 2,
        "producto_id": 456,
        "producto_nombre": "Juguete para Gato",
        "producto_imagen": "https://...",
        "cantidad": 1,
        "precio_unitario": 450.00,
        "subtotal": 450.00
      }
    ],
    "historial_estado": [
      {
        "estado": "Pendiente de envío",
        "fecha": "2025-11-28T10:30:00Z",
        "comentario": "Pedido recibido"
      },
      {
        "estado": "Enviado",
        "fecha": "2025-11-29T09:15:00Z",
        "comentario": "En camino con transportadora ABC"
      },
      {
        "estado": "Entregado",
        "fecha": "2025-11-30T14:20:00Z",
        "comentario": "Entregado y firmado por cliente"
      }
    ],
    "puede_calificar": true
  }
}
```

**Validaciones**:
- Si `pedido_id` no existe: HTTP 404 `{ "status": "error", "message": "Pedido no encontrado." }`
- Si pedido no pertenece al usuario: HTTP 403 `{ "status": "error", "message": "No tienes permiso para ver este pedido." }`

---

### **Obtener historial de estados de un pedido**

- **Método**: `GET`
- **Ruta**: `/api/pedidos/mis-pedidos/{pedido_id}/historial`
- **Auth**: Requiere usuario autenticado
- **Validación**: Verificar pertenencia del pedido
- **Respuesta**:
```json
{
  "status": "success",
  "data": [
    {
      "estado": "Pendiente de envío",
      "fecha": "2025-11-28T10:30:00Z",
      "comentario": "Pedido recibido y en preparación"
    },
    {
      "estado": "Enviado",
      "fecha": "2025-11-29T09:15:00Z",
      "comentario": "Despachado con guía #ABC123456"
    },
    {
      "estado": "Entregado",
      "fecha": "2025-11-30T14:20:00Z",
      "comentario": "Recibido por cliente"
    }
  ]
}
```

---

### **Cancelar un pedido** (opcional)

- **Método**: `POST`
- **Ruta**: `/api/pedidos/mis-pedidos/{pedido_id}/cancelar`
- **Auth**: Requiere usuario autenticado
- **Validaciones**:
  - Solo se puede cancelar si `estado == 'Pendiente de envío'`
  - No se puede cancelar si ya fue enviado o entregado
- **Payload**:
```json
{
  "motivo": "Ya no lo necesito"
}
```
- **Respuesta éxito**:
```json
{ "status": "success", "message": "Pedido cancelado exitosamente" }
```
- **Errores**:
```json
{ "status": "error", "message": "No se puede cancelar un pedido que ya fue enviado." }
{ "status": "error", "message": "No tienes permiso para cancelar este pedido." }
```

---

## 🎨 Frontend - Componentes React

### 1. **MyOrdersPage Component**

**Ubicación**: `src/pages/MyOrdersPage.jsx`

**Ruta**: `/mi-cuenta/pedidos` o `/mis-pedidos`

**Estructura**:
```jsx
import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { pedidosService } from '../services/pedidos-service';
import OrderCard from '../components/OrderCard';
import OrderDetailModal from '../components/OrderDetailModal';
import EmptyState from '../components/EmptyState';
import Spinner from '../components/Spinner';

const MyOrdersPage = () => {
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPedido, setSelectedPedido] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [filterEstado, setFilterEstado] = useState('');

  useEffect(() => {
    fetchPedidos();
  }, [filterEstado]);

  const fetchPedidos = async () => {
    try {
      setLoading(true);
      const data = await pedidosService.getMyOrders({
        estado: filterEstado || undefined
      });
      setPedidos(data);
    } catch (error) {
      toast.error('Error al cargar tus pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (pedidoId) => {
    try {
      const detail = await pedidosService.getMyOrderDetail(pedidoId);
      setSelectedPedido(detail);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Error al cargar detalle');
    }
  };

  return (
    <div className="mis-pedidos-page">
      <div className="page-header">
        <h1>Mis Pedidos</h1>
        <p className="subtitle">Historial completo de tus compras</p>
      </div>

      {/* Filtros */}
      <div className="filters">
        <select 
          value={filterEstado} 
          onChange={(e) => setFilterEstado(e.target.value)}
        >
          <option value="">Todos los estados</option>
          <option value="Pendiente de envío">Pendiente de envío</option>
          <option value="Enviado">Enviado</option>
          <option value="Entregado">Entregado</option>
          <option value="Cancelado">Cancelado</option>
        </select>
      </div>

      {/* Lista de pedidos */}
      {loading && <Spinner />}
      
      {!loading && pedidos.length === 0 && (
        <EmptyState 
          icon="📦"
          title="No tienes pedidos aún"
          message="Explora nuestro catálogo y realiza tu primera compra"
          actionText="Ver Productos"
          actionLink="/productos"
        />
      )}

      {!loading && pedidos.length > 0 && (
        <div className="orders-list">
          {pedidos.map(pedido => (
            <OrderCard 
              key={pedido.id}
              pedido={pedido}
              onViewDetail={() => handleViewDetail(pedido.id)}
            />
          ))}
        </div>
      )}

      {/* Modal de detalle */}
      <OrderDetailModal 
        isOpen={detailModalOpen}
        pedido={selectedPedido}
        onClose={() => setDetailModalOpen(false)}
        onRefresh={fetchPedidos}
      />
    </div>
  );
};

export default MyOrdersPage;
```

---

### 2. **OrderCard Component**

**Ubicación**: `src/components/OrderCard.jsx`

```jsx
const OrderCard = ({ pedido, onViewDetail }) => {
  const getStatusBadge = (estado) => {
    const colors = {
      'Pendiente de envío': 'warning',
      'Enviado': 'info',
      'Entregado': 'success',
      'Cancelado': 'danger'
    };
    return colors[estado] || 'secondary';
  };

  return (
    <div className="order-card">
      <div className="order-header">
        <div className="order-info">
          <h3>Pedido #{pedido.id}</h3>
          <span className="order-date">
            {new Date(pedido.fecha_creacion).toLocaleDateString('es-ES', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </span>
        </div>
        <span className={`badge badge-${getStatusBadge(pedido.estado)}`}>
          {pedido.estado}
        </span>
      </div>

      <div className="order-body">
        <div className="order-summary">
          <div className="summary-item">
            <span className="label">Total:</span>
            <span className="value">${pedido.total.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Items:</span>
            <span className="value">{pedido.items_count}</span>
          </div>
          {pedido.fecha_entrega && (
            <div className="summary-item">
              <span className="label">Entregado:</span>
              <span className="value">
                {new Date(pedido.fecha_entrega).toLocaleDateString('es-ES')}
              </span>
            </div>
          )}
          {pedido.fecha_estimada_entrega && pedido.estado === 'Enviado' && (
            <div className="summary-item">
              <span className="label">Entrega estimada:</span>
              <span className="value">
                {new Date(pedido.fecha_estimada_entrega).toLocaleDateString('es-ES')}
              </span>
            </div>
          )}
        </div>

        <div className="order-address">
          <span className="label">Dirección:</span>
          <span className="value">{pedido.direccion_envio}</span>
        </div>
      </div>

      <div className="order-footer">
        <button 
          onClick={onViewDetail}
          className="btn btn-primary"
        >
          Ver Detalle
        </button>
      </div>
    </div>
  );
};
```

---

### 3. **OrderDetailModal Component**

**Ubicación**: `src/components/OrderDetailModal.jsx`

```jsx
const OrderDetailModal = ({ isOpen, pedido, onClose, onRefresh }) => {
  if (!isOpen || !pedido) return null;

  const handleCancelOrder = async () => {
    if (!window.confirm('¿Estás seguro de cancelar este pedido?')) return;
    
    try {
      await pedidosService.cancelMyOrder(pedido.id, {
        motivo: 'Cancelado por el cliente'
      });
      toast.success('Pedido cancelado exitosamente');
      onRefresh();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Error al cancelar pedido');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="large">
      <div className="order-detail-modal">
        <div className="modal-header">
          <h2>Pedido #{pedido.id}</h2>
          <span className={`badge badge-${getStatusBadge(pedido.estado)}`}>
            {pedido.estado}
          </span>
        </div>

        <div className="modal-body">
          {/* Info general */}
          <section className="order-info-section">
            <h3>Información del Pedido</h3>
            <div className="info-grid">
              <div className="info-item">
                <label>Fecha:</label>
                <span>{new Date(pedido.fecha_creacion).toLocaleString('es-ES')}</span>
              </div>
              <div className="info-item">
                <label>Total:</label>
                <span className="total">${pedido.total.toFixed(2)}</span>
              </div>
              <div className="info-item">
                <label>Dirección de Envío:</label>
                <span>{pedido.direccion_envio}</span>
              </div>
            </div>
          </section>

          {/* Items del pedido */}
          <section className="order-items-section">
            <h3>Productos</h3>
            <div className="items-list">
              {pedido.items.map(item => (
                <div key={item.id} className="order-item">
                  <img 
                    src={item.producto_imagen} 
                    alt={item.producto_nombre}
                    className="item-image"
                  />
                  <div className="item-info">
                    <h4>{item.producto_nombre}</h4>
                    <p className="item-quantity">Cantidad: {item.cantidad}</p>
                    <p className="item-price">
                      ${item.precio_unitario.toFixed(2)} c/u
                    </p>
                  </div>
                  <div className="item-subtotal">
                    ${item.subtotal.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Tracking / Historial de estados */}
          <section className="order-tracking-section">
            <h3>Seguimiento del Pedido</h3>
            <div className="tracking-timeline">
              {pedido.historial_estado?.map((estado, index) => (
                <div 
                  key={index} 
                  className={`timeline-item ${index === pedido.historial_estado.length - 1 ? 'active' : ''}`}
                >
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    <h4>{estado.estado}</h4>
                    <p className="timeline-date">
                      {new Date(estado.fecha).toLocaleString('es-ES')}
                    </p>
                    {estado.comentario && (
                      <p className="timeline-comment">{estado.comentario}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Acciones */}
          {pedido.puede_calificar && pedido.estado === 'Entregado' && (
            <section className="order-actions-section">
              <button 
                className="btn btn-primary"
                onClick={() => {/* Abrir modal de calificación */}}
              >
                Calificar Productos
              </button>
            </section>
          )}

          {pedido.estado === 'Pendiente de envío' && (
            <section className="order-actions-section">
              <button 
                className="btn btn-danger"
                onClick={handleCancelOrder}
              >
                Cancelar Pedido
              </button>
            </section>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">
            Cerrar
          </button>
        </div>
      </div>
    </Modal>
  );
};
```

---

## 📡 Servicio de API Frontend

**Ubicación**: `src/services/pedidos-service.js`

```javascript
import apiClient from './api-client';

class PedidosService {
  // Obtener mis pedidos
  async getMyOrders({ skip = 0, limit = 20, estado } = {}) {
    const response = await apiClient.get('/pedidos/mis-pedidos', {
      params: { skip, limit, estado }
    });
    return response.data.data || response.data;
  }

  // Obtener detalle de mi pedido
  async getMyOrderDetail(pedidoId) {
    const response = await apiClient.get(`/pedidos/mis-pedidos/${pedidoId}`);
    return response.data.data || response.data;
  }

  // Obtener historial de estados
  async getMyOrderHistory(pedidoId) {
    const response = await apiClient.get(`/pedidos/mis-pedidos/${pedidoId}/historial`);
    return response.data.data || response.data;
  }

  // Cancelar mi pedido
  async cancelMyOrder(pedidoId, data) {
    const response = await apiClient.post(`/pedidos/mis-pedidos/${pedidoId}/cancelar`, data);
    return response.data;
  }
}

export const pedidosService = new PedidosService();
```

---

## 🎨 Estilos CSS

```css
.mis-pedidos-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.subtitle {
  color: #6b7280;
  font-size: 1rem;
}

/* Order Card */
.order-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  transition: box-shadow 0.2s;
}

.order-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.order-info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.order-date {
  color: #6b7280;
  font-size: 0.875rem;
}

/* Status Badges */
.badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-info {
  background: #dbeafe;
  color: #1e40af;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
}

/* Tracking Timeline */
.tracking-timeline {
  position: relative;
  padding-left: 40px;
}

.timeline-item {
  position: relative;
  padding-bottom: 24px;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -25px;
  top: 8px;
  bottom: -24px;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item:last-child::before {
  display: none;
}

.timeline-marker {
  position: absolute;
  left: -31px;
  top: 0;
  width: 14px;
  height: 14px;
  background: #e5e7eb;
  border-radius: 50%;
}

.timeline-item.active .timeline-marker {
  background: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
}

.timeline-content h4 {
  font-weight: 600;
  margin-bottom: 4px;
}

.timeline-date {
  color: #6b7280;
  font-size: 0.875rem;
}

.timeline-comment {
  color: #4b5563;
  font-size: 0.875rem;
  margin-top: 4px;
}
```

---

## ✅ Criterios de Aceptación

### AC 1: Cliente ve todos sus pedidos
- **Endpoint**: `GET /api/pedidos/mis-pedidos`
- **Ordenamiento**: Más recientes primero
- **Filtros**: Por estado

### AC 2: Detalle de pedido con items
- **Endpoint**: `GET /api/pedidos/mis-pedidos/{id}`
- **Incluye**: Lista de productos, cantidades, precios
- **Validación**: Solo el dueño puede ver

### AC 3: Tracking de estado del pedido
- **Visualización**: Timeline con historial completo
- **Estados**: Pendiente → Enviado → Entregado
- **Incluye**: Fechas y comentarios de cada cambio

### AC 4: Cancelación de pedidos
- **Solo**: Pedidos en estado "Pendiente de envío"
- **Mensaje**: Confirmación antes de cancelar
- **Actualización**: Cambio a estado "Cancelado"

### AC 5: Integración con calificaciones
- **Botón**: "Calificar Productos" si estado = Entregado
- **Navega**: A página/modal de calificaciones

---

## 🔎 Validaciones

### Backend
- Usuario solo puede ver sus propios pedidos
- Verificar pertenencia en cada endpoint
- Solo cancelar si estado = 'Pendiente de envío'

### Frontend
- Validar autenticación antes de acceder
- Manejar estado vacío (sin pedidos)
- Loading states en todas las operaciones

Mensajes:
```json
{ "status": "error", "message": "Pedido no encontrado." }
{ "status": "error", "message": "No tienes permiso para ver este pedido." }
{ "status": "error", "message": "No se puede cancelar un pedido que ya fue enviado." }
{ "status": "success", "message": "Pedido cancelado exitosamente" }
```

---

## ✅ Checklist Técnico

### Backend
- [ ] Endpoint `GET /api/pedidos/mis-pedidos` con filtros y paginación
- [ ] Endpoint `GET /api/pedidos/mis-pedidos/{id}` con validación de pertenencia
- [ ] Endpoint `GET /api/pedidos/mis-pedidos/{id}/historial`
- [ ] Endpoint `POST /api/pedidos/mis-pedidos/{id}/cancelar`
- [ ] Validación de autenticación en todos los endpoints
- [ ] Verificación de pertenencia del pedido al usuario

### Frontend
- [ ] Página `MyOrdersPage` con lista de pedidos
- [ ] Componente `OrderCard` con info resumida
- [ ] Modal `OrderDetailModal` con items y tracking
- [ ] Timeline de estados del pedido
- [ ] Filtro por estado
- [ ] Empty state cuando no hay pedidos
- [ ] Botón "Calificar" si pedido entregado
- [ ] Botón "Cancelar" si pedido pendiente
- [ ] Servicio `pedidos-service.js` completo

---

**Archivo**: `HU/INSTRUCTIONS_HU_MY_ORDERS.md`

````
