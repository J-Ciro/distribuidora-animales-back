# 🌟 Sistema de Calificaciones - Inicio Rápido

## Instalación

### 1. Aplicar Migración de Base de Datos

#### Opción A: Script PowerShell (Recomendado)
```powershell
cd Distribuidora_Perros_Gatos_back
.\apply-ratings-migration.ps1
```

#### Opción B: Manual con sqlcmd
```powershell
sqlcmd -S localhost -U sa -P TuPassword -d distribuidora_db -i .\sql\migrations\010_create_ratings.sql
```

### 2. Reiniciar Backend
```powershell
cd .\backend\api
python main.py
```

El backend cargará automáticamente los nuevos endpoints de calificaciones.

### 3. Frontend
No requiere cambios adicionales. Solo recarga la página si ya estaba abierta.

## Uso del Sistema

### Como Cliente

#### 1. Realizar un Pedido
- Agrega productos al carrito
- Completa el checkout
- Espera a que el pedido sea marcado como "Entregado"

#### 2. Calificar Productos
1. Ve a "Mis Pedidos" (icono de usuario → Mis Pedidos)
2. Busca un pedido con estado "Entregado"
3. Haz clic en el botón "⭐ Calificar" junto a cada producto
4. Selecciona estrellas (1-5)
5. Opcionalmente escribe un comentario
6. Haz clic en "Enviar calificación"

#### 3. Ver Calificaciones
- Las calificaciones aparecen en las tarjetas de productos en la página principal
- Muestra el promedio y el número total de reseñas

### Como Administrador

#### 1. Acceder al Panel de Calificaciones
1. Inicia sesión como administrador
2. En el menú lateral izquierdo, haz clic en "⭐ Calificaciones"

#### 2. Ver Estadísticas
El panel muestra:
- Total de calificaciones
- Promedio general
- Calificaciones visibles vs ocultas
- Distribución por estrellas (gráfico de barras)

#### 3. Gestionar Calificaciones

**Filtrar:**
- Haz clic en "Todas", "Visibles" u "Ocultas"

**Ver Detalles:**
- Haz clic en el botón "Ver" en cualquier calificación

**Cambiar Visibilidad:**
- Haz clic en "Mostrar" u "Ocultar" para controlar qué calificaciones son públicas

**Eliminar:**
- En el modal de detalles, haz clic en "Eliminar"
- Confirma la acción

## Endpoints API

### Públicos (Cliente autenticado)
```
POST   /api/calificaciones                          # Crear calificación
GET    /api/calificaciones/mis-calificaciones       # Mis calificaciones
GET    /api/calificaciones/producto/{id}            # Calificaciones de producto
GET    /api/calificaciones/producto/{id}/stats      # Estadísticas de producto
PUT    /api/calificaciones/{id}                     # Actualizar mi calificación
DELETE /api/calificaciones/{id}                     # Eliminar mi calificación
```

### Admin
```
GET    /api/admin/calificaciones                    # Todas las calificaciones
GET    /api/admin/calificaciones/{id}               # Calificación por ID
PUT    /api/admin/calificaciones/{id}               # Actualizar calificación
DELETE /api/admin/calificaciones/{id}               # Eliminar calificación
PATCH  /api/admin/calificaciones/{id}/toggle-visibility  # Cambiar visibilidad
```

## Ejemplos de Uso con curl

### Crear Calificación (Cliente)
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    producto_id = 1
    pedido_id = 5
    calificacion = 5
    comentario = "Excelente producto, mi perro lo adora!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/calificaciones" -Method POST -Headers $headers -Body $body
```

### Obtener Calificaciones de un Producto (Público)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/calificaciones/producto/1"
```

### Obtener Estadísticas de un Producto (Público)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/calificaciones/producto/1/stats"
```

### Todas las Calificaciones (Admin)
```powershell
$headers = @{
    "Authorization" = "Bearer ADMIN_TOKEN"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/admin/calificaciones" -Headers $headers
```

## Validaciones Importantes

✅ **Puedes calificar si:**
- El pedido está en estado "Entregado"
- El producto está en ese pedido
- No has calificado ese producto antes en ese pedido

❌ **No puedes calificar si:**
- El pedido no está entregado
- El producto no está en tu pedido
- Ya calificaste ese producto en ese pedido

## Troubleshooting

### Error: "No puedes calificar este producto"
**Causa:** El pedido no está entregado o ya calificaste el producto
**Solución:** 
1. Verifica que el pedido esté en estado "Entregado"
2. Revisa si ya calificaste ese producto en "Mis Calificaciones"

### No aparecen las estrellas en los productos
**Causa:** El backend no tiene estadísticas o hay error en la carga
**Solución:**
1. Verifica que la migración se aplicó correctamente
2. Revisa la consola del navegador para errores
3. Intenta crear una calificación manualmente

### Error 401 al calificar
**Causa:** No estás autenticado o el token expiró
**Solución:**
1. Cierra sesión y vuelve a iniciar sesión
2. Verifica que el token esté en localStorage

## Componentes Clave

### Frontend
- **StarRating**: Muestra estrellas (solo lectura)
- **RatingInput**: Selección interactiva de estrellas
- **RatingModal**: Modal para calificar productos
- **AdminCalificacionesPage**: Panel de administración

### Backend
- **RatingsService**: Lógica de negocio
- **ratings.py**: Endpoints API
- **Calificacion**: Modelo de BD
- **ProductoStats**: Estadísticas precalculadas

## Próximos Pasos Sugeridos

1. Prueba el flujo completo: compra → entrega → calificación
2. Verifica que las estadísticas se actualizan correctamente
3. Prueba ocultar/mostrar calificaciones desde el admin
4. Revisa cómo se ven las estrellas en diferentes productos

## Soporte

Para más información, consulta: `SISTEMA_CALIFICACIONES.md`
