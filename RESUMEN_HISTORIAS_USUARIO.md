# 📋 Resumen de Historias de Usuario - Proyecto Distribuidora Perros y Gatos

## 🤖 HU-01: Chatbot de Atención al Cliente "Max"

### Descripción
Como **cliente del sitio web**, quiero tener acceso a un chatbot inteligente que me ayude a resolver mis dudas sobre productos, categorías y funcionamiento de la tienda, para obtener respuestas rápidas sin necesidad de buscar manualmente.

### Funcionalidades Principales
- **Interfaz de chat flotante** en la esquina inferior derecha (disponible en todas las páginas)
- **Base de conocimiento** con información sobre:
  - Categorías de productos (alimentos, juguetes, accesorios, salud)
  - Proceso de compra y métodos de pago
  - Políticas de envío y devoluciones
  - Información de contacto
  - Horarios de atención
- **Sugerencias contextuales** según la pregunta del usuario
- **Respuestas automáticas** basadas en palabras clave
- **Interfaz amigable** con avatar de perro/gato

### Criterios de Aceptación

✅ **AC-1: Disponibilidad del Chat**
- El botón del chatbot debe estar visible en todas las páginas
- Al hacer clic, se abre una ventana de chat animada
- El chat saluda al usuario con un mensaje de bienvenida

✅ **AC-2: Búsqueda de Información**
- Usuario puede escribir preguntas en lenguaje natural
- Sistema reconoce palabras clave (ej: "alimento", "envío", "pago")
- Responde con información relevante en menos de 1 segundo

✅ **AC-3: Sugerencias Inteligentes**
- Muestra 3-5 sugerencias de preguntas frecuentes
- Ejemplos: "¿Qué alimentos tienen para gatos?", "¿Cuánto demora el envío?"
- Al hacer clic en sugerencia, muestra respuesta inmediata

✅ **AC-4: Respuestas Predefinidas**
- Debe tener respuestas para al menos 15 categorías de preguntas
- Si no entiende la pregunta, muestra: "Lo siento, no entendí. ¿Puedes reformular?"
- Ofrece botón "Contactar Soporte Humano" para casos complejos

✅ **AC-5: Experiencia de Usuario**
- Animaciones suaves al abrir/cerrar
- Historial de conversación durante la sesión
- Botón de minimizar/cerrar chat
- Responsive en móviles

---

## 📊 HU-02: Dashboard de Estadísticas para Administrador

### Descripción
Como **administrador del sistema**, quiero tener acceso a un panel de estadísticas y métricas en tiempo real, para tomar decisiones informadas sobre inventario, productos populares y comportamiento de usuarios.

### Funcionalidades Principales
- **Resumen ejecutivo** con KPIs principales
- **Gráficas de ventas** por período (día, semana, mes, año)
- **Top 10 productos** más vendidos y mejor calificados
- **Análisis de usuarios** (nuevos, activos, compradores frecuentes)
- **Estado de pedidos** (pendientes, en proceso, entregados)
- **Métricas de categorías** (más populares, con más ingresos)
- **Estadísticas de calificaciones** (promedio general, distribución)

### Criterios de Aceptación

✅ **AC-1: Dashboard Summary (Vista General)**
- Muestra 6 tarjetas con métricas clave:
  - Total de ventas del mes (en pesos)
  - Cantidad de pedidos del mes
  - Nuevos usuarios del mes
  - Productos en stock bajo (< 10 unidades)
  - Promedio de calificación general
  - Tasa de conversión (visitantes → compradores)

✅ **AC-2: Gráfica de Ventas por Fecha**
- Gráfico de líneas con ventas diarias de los últimos 30 días
- Selector de período: "Hoy", "7 días", "30 días", "3 meses", "Año"
- Muestra total de ingresos y cantidad de pedidos
- Permite comparar con período anterior

✅ **AC-3: Top 10 Productos**
- Tabla ordenada con los 10 productos más vendidos
- Columnas: Nombre, Categoría, Cantidad Vendida, Ingresos Totales, Stock Actual
- Indicador visual si el stock está bajo (< 10 unidades en rojo)
- Botón "Reabastecer" que redirige al módulo de inventario

✅ **AC-4: Análisis de Usuarios**
- Total de usuarios registrados
- Nuevos usuarios en los últimos 7/30 días
- Usuarios activos (con sesión en últimos 7 días)
- Usuarios con más compras (top 5)
- Gráfico de barras: usuarios por mes

✅ **AC-5: Estado de Pedidos**
- Contador de pedidos por estado:
  - Pendiente de pago
  - En preparación
  - Enviado
  - Entregado
  - Cancelado
- Gráfico de torta con distribución porcentual
- Alerta si hay pedidos pendientes > 3 días

✅ **AC-6: Métricas de Categorías**
- Tabla con categorías ordenadas por ingresos
- Columnas: Nombre, Productos Activos, Ventas del Mes, Ingresos
- Gráfico de barras horizontales con comparación

✅ **AC-7: Estadísticas de Calificaciones**
- Promedio general de calificaciones (1-5 estrellas)
- Total de calificaciones recibidas
- Distribución por estrellas (cuántas de 5★, 4★, 3★, 2★, 1★)
- Productos con mejor y peor calificación

✅ **AC-8: Actualización de Datos**
- Botón "Actualizar" para refrescar métricas
- Los datos deben cargarse en menos de 3 segundos
- Indicador de "Última actualización: hace X minutos"

---

## 📦 HU-03: Área de "Mis Pedidos" para Cliente

### Descripción
Como **cliente registrado**, quiero poder ver el historial de todos mis pedidos, consultar su estado actual y los detalles de cada compra, para hacer seguimiento de mis órdenes y tener control sobre mis transacciones.

### Funcionalidades Principales
- **Listado de pedidos** con filtros (todos, pendientes, entregados, cancelados)
- **Detalle de pedido** con productos, cantidades, precios
- **Tracking de estado** visual (timeline)
- **Opción de cancelar** pedidos pendientes
- **Descarga de factura** (si está disponible)
- **Historial completo** con paginación

### Criterios de Aceptación

✅ **AC-1: Visualización del Listado**
- Página "Mis Pedidos" accesible desde menú de usuario
- Muestra todos los pedidos del usuario ordenados por fecha (más reciente primero)
- Cada card de pedido muestra:
  - Número de pedido (ej: #PED-001234)
  - Fecha de creación
  - Estado actual (badge con color)
  - Total del pedido
  - Cantidad de productos
- Paginación si hay más de 10 pedidos

✅ **AC-2: Filtros de Estado**
- Tabs para filtrar por estado:
  - "Todos"
  - "Pendientes" (Pendiente de pago, En preparación)
  - "En camino" (Enviado)
  - "Entregados"
  - "Cancelados"
- Contador de pedidos por tab
- Filtro se aplica sin recargar la página

✅ **AC-3: Detalle de Pedido**
- Al hacer clic en un pedido, se abre modal/página con detalle completo:
  - **Información general**: Número, fecha, estado, total
  - **Productos**: Lista con imagen, nombre, cantidad, precio unitario, subtotal
  - **Dirección de envío**: Completa con ciudad, dirección, teléfono
  - **Método de pago**: Tipo (tarjeta, efectivo, transferencia)
  - **Resumen de costos**: Subtotal, envío, total

✅ **AC-4: Tracking Visual de Estado**
- Timeline/stepper que muestra el progreso del pedido:
  1. Pedido recibido ✅ (fecha)
  2. Pago confirmado ✅ (fecha) o ⏳ Pendiente
  3. En preparación ⏳ o ✅ (fecha)
  4. Enviado ⏳ o ✅ (fecha)
  5. Entregado ⏳ o ✅ (fecha)
- Estados completados en verde, pendientes en gris
- Fecha estimada de entrega si está en tránsito

✅ **AC-5: Cancelación de Pedido**
- Botón "Cancelar Pedido" visible solo si estado = "Pendiente" o "En preparación"
- Al hacer clic, muestra modal de confirmación:
  - "¿Estás seguro de cancelar este pedido?"
  - Advertencia: "Esta acción no se puede deshacer"
- Si confirma, cambia estado a "Cancelado"
- Toast: "Pedido cancelado exitosamente"
- No permite cancelar si ya está "Enviado" o "Entregado"

✅ **AC-6: Calificar Productos (Integración)**
- Si pedido está "Entregado" y productos no han sido calificados:
  - Mostrar botón "Calificar Productos"
  - Redirige a página de calificaciones con productos de ese pedido
- Si ya fueron calificados, mostrar "Ya calificaste este pedido ✓"

✅ **AC-7: Descarga de Factura (Opcional)**
- Si el pedido tiene factura generada:
  - Botón "Descargar Factura" (PDF)
  - Archivo contiene: logo, datos del pedido, productos, totales
- Si no hay factura, mostrar "Factura no disponible"

✅ **AC-8: Estado Vacío**
- Si usuario no tiene pedidos, mostrar:
  - Ilustración amigable (carrito vacío)
  - Mensaje: "Aún no has realizado ningún pedido"
  - Botón "Explorar Productos" que redirige al catálogo

---

## ⭐ HU-04: Sistema de Calificaciones y Reseñas de Productos

### Descripción
Como **cliente que ha comprado un producto**, quiero poder calificar y dejar reseñas sobre los productos que he recibido, para ayudar a otros compradores y compartir mi experiencia, mientras que como **visitante** quiero poder ver las calificaciones de los productos antes de comprar.

### Funcionalidades Principales
- **Calificar productos** comprados (1-5 estrellas + comentario opcional)
- **Ver reseñas públicas** de cualquier producto (sin necesidad de login)
- **Editar/eliminar** mis propias calificaciones
- **Estadísticas agregadas** (promedio, distribución por estrellas)
- **Productos pendientes de calificar** (de pedidos entregados)
- **Panel de moderación admin** para gestionar reseñas

### Criterios de Aceptación

✅ **AC-1: Ver Calificaciones en Product Card (Público)**
- Cada tarjeta de producto muestra:
  - Promedio de estrellas (ej: ⭐⭐⭐⭐⭐ 4.5)
  - Cantidad de calificaciones (ej: "(42 reseñas)")
- Si no tiene calificaciones, muestra: "Sin calificaciones aún"
- Funciona sin necesidad de login

✅ **AC-2: Ver Reseñas Detalladas (Público)**
- En página de detalle de producto, sección "Reseñas de Clientes":
  - **Resumen estadístico**:
    - Promedio general (número grande + estrellas)
    - Total de calificaciones
    - Distribución por estrellas (barras):
      ```
      5★ ████████████████ 85% (34)
      4★ ███████          15% (6)
      3★ ██               5%  (2)
      2★                  0%  (0)
      1★                  0%  (0)
      ```
  - **Lista de reseñas individuales**:
    - Nombre del usuario
    - Calificación en estrellas
    - Comentario
    - Fecha de publicación
- Paginación cada 10 reseñas
- Ordenar por: "Más recientes", "Mejor calificadas", "Peor calificadas"

✅ **AC-3: Calificar Producto (Cliente Autenticado)**
- Solo usuarios con pedidos "Entregados" pueden calificar
- Desde "Mis Pedidos" o "Mis Calificaciones", botón "Calificar Producto"
- Modal con formulario:
  - **Calificación**: 1-5 estrellas (OBLIGATORIO)
    - Selector interactivo: pasar mouse/tocar cambia estrellas
  - **Comentario**: textarea (OPCIONAL, max 500 caracteres)
    - Contador de caracteres: "125/500"
  - Botones: "Cancelar" y "Publicar Calificación"
- Validaciones:
  - No puede estar vacía la calificación
  - No puede exceder 500 caracteres el comentario

✅ **AC-4: Restricciones de Calificación**
- Un usuario solo puede calificar un producto **UNA VEZ por pedido**
- Si intenta calificar el mismo producto del mismo pedido:
  - Error: "Ya has calificado este producto en este pedido."
- Solo puede calificar productos de pedidos con estado "Entregado"
- Si intenta calificar de pedido no entregado:
  - Error: "Solo puedes calificar productos de pedidos entregados."

✅ **AC-5: Editar Mi Calificación**
- En "Mis Calificaciones", cada calificación tiene botón "Editar"
- Abre modal con datos precargados:
  - Estrellas actuales seleccionadas
  - Comentario actual en textarea
- Permite modificar estrellas y/o comentario
- Al guardar: "Calificación actualizada exitosamente"
- Se actualiza el promedio del producto automáticamente

✅ **AC-6: Eliminar Mi Calificación**
- Botón "Eliminar" en "Mis Calificaciones"
- Modal de confirmación: "¿Estás seguro de eliminar esta calificación? Esta acción no se puede deshacer."
- Si confirma:
  - Elimina la calificación
  - Toast: "Calificación eliminada exitosamente"
  - Se actualiza el promedio del producto

✅ **AC-7: Página "Mis Calificaciones"**
- Accesible desde menú de usuario
- **Sección 1: Productos para Calificar**
  - Lista de productos de pedidos entregados que no han sido calificados
  - Muestra: imagen, nombre, fecha de entrega
  - Botón "Calificar Producto" por cada uno
  - Si no hay: "No tienes productos pendientes de calificar"
- **Sección 2: Mis Calificaciones**
  - Lista de todas las calificaciones que he hecho
  - Muestra: producto, estrellas, comentario, fecha
  - Botones: "Editar" y "Eliminar" por cada una
  - Si no hay: "Aún no has calificado ningún producto"

✅ **AC-8: Panel de Moderación Admin**
- Ruta: `/admin/calificaciones`
- Tabla con todas las calificaciones del sistema:
  - Columnas: ID, Producto, Usuario, Rating, Comentario, Fecha, Estado
- **Filtros**:
  - Por producto (select dropdown)
  - Por usuario (búsqueda)
  - Por rating: "Todas", "5★", "4★", "3★", "2★", "1★"
- **Acciones por calificación**:
  - **Ver detalles**: Modal con información completa
  - **Eliminar**: Botón de eliminar (permanente)
    - Modal de confirmación antes de eliminar
    - Solo admin puede eliminar reseñas de usuarios

✅ **AC-9: Actualización Automática de Estadísticas**
- Al crear/editar/eliminar una calificación:
  - Se actualiza automáticamente:
    - `promedio_calificacion` del producto
    - `total_calificaciones` del producto
    - `total_X_estrellas` (distribución)
  - Las stats se reflejan instantáneamente en las vistas públicas

✅ **AC-10: Mensajes de Éxito/Error**
- Crear: "Calificación creada exitosamente"
- Actualizar: "Calificación actualizada exitosamente"
- Eliminar: "Calificación eliminada exitosamente"
- Error validación: "La calificación debe ser entre 1 y 5 estrellas."
- Error restricción: "Solo puedes calificar productos de pedidos entregados."
- Error duplicado: "Ya has calificado este producto en este pedido."

---

## 🎯 Resumen Ejecutivo de Prioridades

| HU | Complejidad | Impacto en UX | Prioridad | Estado Actual |
|----|-------------|---------------|-----------|---------------|
| **Mis Pedidos** | Media | Alto | 🔴 Alta | ✅ Implementado |
| **Calificaciones** | Alta | Alto | 🔴 Alta | ✅ Implementado |
| **Dashboard Admin** | Media | Medio | 🟡 Media | ⏳ Pendiente |
| **Chatbot** | Baja | Medio | 🟢 Baja | ⏳ Pendiente |

### Recomendación de Implementación
1. ✅ **Mis Pedidos** - Completado
2. ✅ **Sistema de Calificaciones** - Completado
3. ⏳ **Dashboard de Estadísticas** - Siguiente prioridad
4. ⏳ **Chatbot de Atención** - Última fase

---

## 📌 Notas Técnicas

### Base de Datos
- Tabla `Pedidos`: Almacena información de pedidos con estados
- Tabla `PedidoItems`: Relación muchos a muchos entre pedidos y productos
- Tabla `Calificaciones`: Almacena calificaciones de usuarios
- Tabla `ProductoStats`: Stats agregadas calculadas automáticamente

### APIs Implementadas
- `GET /api/pedidos/myorders` - Lista pedidos del usuario
- `GET /api/pedidos/{id}` - Detalle de pedido específico
- `PUT /api/pedidos/{id}/cancel` - Cancelar pedido
- `POST /api/calificaciones` - Crear calificación
- `PUT /api/calificaciones/{id}` - Editar calificación
- `DELETE /api/calificaciones/{id}` - Eliminar calificación
- `GET /api/calificaciones/producto/{id}` - Calificaciones de producto
- `GET /api/calificaciones/producto/{id}/stats` - Estadísticas de producto
- `GET /api/calificaciones/mis-calificaciones` - Calificaciones del usuario
- `GET /api/calificaciones/productos-para-calificar` - Productos pendientes

### Pendientes de Implementación
- Dashboard de estadísticas admin (requiere endpoints de analytics)
- Chatbot con IA (requiere integración con servicio de NLP)
- Sistema de notificaciones en tiempo real
- Generación de facturas en PDF

---

**Fecha de Creación**: Diciembre 3, 2025  
**Versión**: 1.0  
**Proyecto**: Distribuidora Perros y Gatos - E-commerce
