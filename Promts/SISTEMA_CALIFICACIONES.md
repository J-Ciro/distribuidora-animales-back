# Sistema de Calificaciones de Productos

## Resumen
Sistema completo de calificaciones con estrellas que permite a los clientes calificar productos después de recibirlos y a los administradores gestionar todas las calificaciones.

## Componentes Implementados

### Backend (Python/FastAPI)

#### Base de Datos
- **Tabla `Calificaciones`**: Almacena las calificaciones individuales
  - Campos: producto_id, usuario_id, pedido_id, calificacion (1-5), comentario, visible, aprobado
  - Constraint único: un usuario solo puede calificar un producto una vez por pedido
  
- **Tabla `ProductoStats`**: Caché de estadísticas agregadas
  - Promedio de calificación, total de calificaciones, distribución por estrellas
  - Se actualiza automáticamente mediante triggers SQL

- **Archivo**: `/sql/migrations/010_create_ratings.sql`

#### Modelos SQLAlchemy
- `Calificacion`: Modelo para calificaciones individuales
- `ProductoStats`: Modelo para estadísticas agregadas
- **Archivo**: `/backend/api/app/models.py`

#### Schemas Pydantic
- `CalificacionCreate`: Validación para crear calificaciones
- `CalificacionUpdate`: Validación para actualizar calificaciones
- `CalificacionResponse`: Respuesta con datos de calificación
- `ProductoStatsResponse`: Respuesta con estadísticas de producto
- **Archivo**: `/backend/api/app/schemas.py`

#### Servicio de Negocio
- `RatingsService`: Lógica de negocio para calificaciones
  - Validación de permisos (solo puede calificar productos de pedidos entregados)
  - CRUD completo
  - Obtención de estadísticas
  - **Archivo**: `/backend/api/app/services/ratings_service.py`

#### Endpoints API

##### Públicos (Clientes autenticados)
- `POST /api/calificaciones` - Crear calificación
- `GET /api/calificaciones/mis-calificaciones` - Obtener mis calificaciones
- `GET /api/calificaciones/producto/{id}` - Calificaciones de un producto
- `GET /api/calificaciones/producto/{id}/stats` - Estadísticas de un producto
- `PUT /api/calificaciones/{id}` - Actualizar mi calificación
- `DELETE /api/calificaciones/{id}` - Eliminar mi calificación
- `GET /api/calificaciones/productos-pendientes` - Productos que puedo calificar

##### Admin
- `GET /api/admin/calificaciones` - Todas las calificaciones (con filtros)
- `GET /api/admin/calificaciones/{id}` - Calificación por ID
- `PUT /api/admin/calificaciones/{id}` - Actualizar cualquier calificación
- `DELETE /api/admin/calificaciones/{id}` - Eliminar cualquier calificación
- `PATCH /api/admin/calificaciones/{id}/toggle-visibility` - Cambiar visibilidad

**Archivo**: `/backend/api/app/routers/ratings.py`

### Frontend (React)

#### Componentes UI

##### StarRating (Visualización)
- Muestra estrellas según calificación
- Soporta medias estrellas
- Tamaños: small, medium, large
- Muestra total de reseñas
- **Archivo**: `/src/components/ui/star-rating/index.js`

##### RatingInput (Interactivo)
- Permite seleccionar calificación (1-5 estrellas)
- Efecto hover
- Muestra etiqueta (Malo, Regular, Bueno, Muy bueno, Excelente)
- **Archivo**: `/src/components/ui/rating-input/index.js`

##### RatingModal
- Modal para calificar productos
- Muestra información del producto
- Input de calificación + comentario opcional
- **Archivo**: `/src/components/RatingModal/index.js`

#### Páginas

##### AdminCalificacionesPage
- Panel administrativo completo
- Estadísticas generales (total, promedio, visibles/ocultas)
- Gráfico de distribución de estrellas
- Tabla con todas las calificaciones
- Filtros: Todas, Visibles, Ocultas
- Acciones: Ver detalles, Cambiar visibilidad, Eliminar
- **Archivo**: `/src/pages/Admin/calificaciones/index.js`

##### MyOrders (Actualizada)
- Botón "Calificar" en cada producto de pedidos entregados
- Integración con RatingModal
- **Archivo**: `/src/pages/my-orders/MyOrders.jsx`

#### Servicios

##### CalificacionesService
- Cliente API para endpoints de calificaciones
- Métodos públicos y admin
- Caché de estadísticas para múltiples productos
- **Archivo**: `/src/services/calificaciones-service.js`

##### ProductosService (Actualizado)
- Enriquece productos con calificaciones al obtener catálogo
- **Archivo**: `/src/services/productos-service.js`

#### Integración

##### ProductCard (Actualizado)
- Muestra estrellas y total de reseñas
- Usa datos reales de calificaciones
- **Archivo**: `/src/components/ui/product-card/index.js`

##### Navegación
- Nueva ruta `/admin/calificaciones` en panel admin
- Icono de estrella en menú lateral
- **Archivos**: 
  - `/src/App.js`
  - `/src/components/layout/admin-layout/index.js`

## Flujo de Usuario

### Cliente
1. Usuario realiza un pedido
2. Pedido cambia a estado "Entregado"
3. En "Mis Pedidos", aparece botón "⭐ Calificar" en cada producto
4. Usuario hace clic y se abre modal de calificación
5. Selecciona estrellas (1-5) y opcionalmente escribe comentario
6. Envía calificación
7. La calificación es visible para todos los usuarios en las tarjetas de productos

### Administrador
1. Accede a "Calificaciones" en panel admin
2. Ve estadísticas generales y distribución de estrellas
3. Puede filtrar por: Todas, Visibles, Ocultas
4. Puede ver detalles de cada calificación
5. Puede cambiar visibilidad (ocultar calificaciones inapropiadas)
6. Puede eliminar calificaciones

## Características Técnicas

### Validaciones
- Solo se puede calificar productos de pedidos entregados
- Un usuario solo puede calificar un producto una vez por pedido
- Calificación debe ser entre 1 y 5 estrellas
- Comentario máximo 500 caracteres

### Optimizaciones
- Tabla `ProductoStats` cachea estadísticas agregadas
- Triggers SQL actualizan automáticamente las estadísticas
- Frontend obtiene múltiples stats en paralelo
- Las calificaciones se cargan bajo demanda

### Seguridad
- Endpoints protegidos con autenticación JWT
- Usuarios solo pueden editar/eliminar sus propias calificaciones
- Admins pueden moderar cualquier calificación
- Validación de propiedad en backend

## Diseño Visual
- Estrellas doradas (#FBBF24) con efecto de sombra
- Gradientes morados para badges y botones
- Diseño consistente con el resto de la aplicación
- Responsive y accesible

## Mejoras Futuras Sugeridas
- Notificaciones por email cuando se recibe una nueva calificación
- Respuestas del vendedor a las calificaciones
- Filtrar productos por calificación
- Ordenar productos por mejor calificación
- Sistema de reportes de calificaciones
- Verificación de "compra verificada"
- Estadísticas por categoría
- Exportar calificaciones a CSV

## Pruebas Recomendadas

1. **Backend**
   - Crear calificación para producto de pedido entregado ✓
   - Intentar calificar producto no entregado (debe fallar) ✓
   - Intentar calificar dos veces el mismo producto (debe fallar) ✓
   - Obtener estadísticas de producto ✓
   - Cambiar visibilidad de calificación (admin) ✓

2. **Frontend**
   - Ver estrellas en tarjetas de productos ✓
   - Abrir modal de calificación desde Mis Pedidos ✓
   - Enviar calificación con/sin comentario ✓
   - Ver panel admin de calificaciones ✓
   - Filtrar calificaciones ✓
   - Cambiar visibilidad ✓

## Instalación

### Base de Datos
```bash
# Ejecutar migración
sqlcmd -S localhost -U sa -P YourPassword -d distribuidora_db -i sql/migrations/010_create_ratings.sql
```

### Backend
Ya está integrado en el backend existente. Los nuevos endpoints estarán disponibles automáticamente al reiniciar el servidor.

### Frontend
Los nuevos componentes y servicios están integrados. Solo necesitas recargar la aplicación.

## Troubleshooting

### Las estrellas no aparecen en las tarjetas
- Verificar que el servicio de productos esté enriqueciendo con stats
- Revisar consola del navegador para errores
- Verificar que la migración de BD se ejecutó correctamente

### No puedo calificar un producto
- Verificar que el pedido esté en estado "Entregado"
- Verificar que no hayas calificado ese producto antes
- Revisar logs del backend para errores de validación

### Las estadísticas no se actualizan
- Verificar que los triggers SQL se crearon correctamente
- Revisar logs de SQL Server para errores
- Manualmente ejecutar: `SELECT * FROM ProductoStats WHERE producto_id = X`
