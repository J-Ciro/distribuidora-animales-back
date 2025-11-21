# 🧩 Instrucciones Técnicas para Implementar la HU: "Gestión de Productos: Crear Nuevo Producto"

**Objetivo**: Implementar la lógica backend para que un administrador pueda crear un nuevo producto en el sistema **Distribuidora Perros y Gatos**, cumpliendo con todos los criterios de aceptación definidos.

> 🔍 Este documento está escrito para ser **consumido y ejecutado por IA**. Cada paso debe interpretarse literalmente. No asumir comportamientos no especificados.

---

## ⚙️ Arquitectura Técnica

- **Producer (API)**: Python (FastAPI)  
- **Consumer (Worker)**: Node.js (Express/TypeScript)  
- **Broker**: RabbitMQ  
- **Infraestructura**: Docker & Docker Compose  
- **Base de datos**: SQL Server  

---

## 🧾 Datos del Producto (Estructura Obligatoria en BD)

Todo producto debe tener los siguientes campos **almacenados en la base de datos**:

| Campo        | Tipo             | Requerido | Validación |
|--------------|------------------|-----------|------------|
| `nombre`     | string           | ✅        | Único en el sistema. Mínimo 2 caracteres. |
| `descripcion`| string           | ✅        | Mínimo 10 caracteres. Texto libre. |
| `precio`     | number (float)   | ✅        | > 0. Solo valores numéricos positivos. |
| `peso`       | number (integer) | ✅        | > 0. Representa **gramos** (entero). Ej: 500 = 500g, 1000 = 1kg. |
| `categoria`  | string           | ✅        | Debe coincidir con una categoría existente (ej: "Perros", "Gatos"). |
| `subcategoria`| string          | ✅        | Debe coincidir con una subcategoría existente dentro de la categoría seleccionada. |
| `imagenUrl`  | string           | ✅        | URL de la imagen subida (almacenada en sistema de archivos o CDN). |

> ⚠️ **Nota**: El peso se almacena **siempre en gramos como entero**, sin importar si el usuario ingresa kg o g. La UI puede mostrar "1 kg", pero el valor guardado es `1000`.

---

## 🔗 Flujo Backend

1. **FastAPI (Producer)**  
   - Endpoint: `POST /api/admin/productos`  
   - Recibe payload con datos del producto.  
   - Valida campos obligatorios y formato de imagen.  
   - Publica mensaje en **RabbitMQ** con datos del producto.  

2. **RabbitMQ (Broker)**  
   - Cola: `productos.crear`  
   - Mensaje contiene JSON con todos los atributos del producto.  

3. **Node.js Worker (Consumer)**  
   - Escucha cola `productos.crear`.  
   - Procesa validaciones adicionales:  
     - Nombre único (case-insensitive).  
     - Categoría y subcategoría válidas.  
     - Conversión de peso a gramos si viene en kilogramos.  
   - Inserta registro en **SQL Server**.  
   - Devuelve confirmación al Producer.  

4. **Respuesta al Producer**  
   - Si éxito → JSON `{ "status": "success", "message": "Producto creado exitosamente" }`  
   - Si error → JSON `{ "status": "error", "message": "<detalle>" }`  

---

## ✅ Criterios de Aceptación – Implementación Detallada

### AC 1: Creación exitosa
- **Condiciones**:
  - Todos los campos requeridos están completos y válidos.
  - `nombre` no existe en la base de datos.
- **Acciones Backend**:
  - Guardar registro en SQL Server.  
  - Confirmar creación.  
- **Resultado esperado**: El producto aparece en el catálogo público.

---

### AC 2: Validación de campos obligatorios
- **Condiciones**: Al enviar payload, falta un campo obligatorio.  
- **Acciones Backend**:
  - Rechazar petición.  
  - Responder con error: `"Por favor, completa todos los campos obligatorios."`  
- **Restricción**: No usar `window.alert()`. Solo respuesta JSON para Toast en frontend.

---

### AC 3: Asociación a categorías y subcategorías
- **Condiciones**: Categoría y subcategoría deben coincidir con listas predefinidas.  
- **Acciones Backend**:
  - Validar contra tabla de categorías/subcategorías en SQL Server.  
  - Si no existen → error.  
- **Resultado esperado**: Producto visible bajo la categoría/subcategoría correcta.

---

### AC 4: Gestión de imagen y validación numérica

#### Validación de imagen:
- **Formatos permitidos**: `.jpg`, `.jpeg`, `.png`, `.svg`, `.webp`  
- **Tamaño máximo**: 10 MB  
- **Si no cumple** → error: `"Formato o tamaño de imagen no válido."`

#### Validación numérica:
- **Precio**: > 0, float.  
- **Peso**: Entero ≥ 1, siempre almacenado en gramos.  

#### Nombre duplicado:
- Si ya existe → error: `"Ya existe un producto con ese nombre."`

---

### AC 5: Prevención de duplicados en creación (Producer)
- **Condiciones**: Si ya existe un producto con el mismo `nombre` (comparación case-insensitive) y se intenta crear otro con el mismo nombre.
- **Acciones Backend (Producer)**:
  - El Producer (FastAPI) debe verificar en la base de datos si existe un producto con el mismo nombre (case-insensitive) antes de publicar el mensaje en RabbitMQ.
  - Si existe, el Producer debe responder con un error 400 y el mensaje: `"Ya existe un producto con ese nombre."` y **no** publicar nada en RabbitMQ.
- **Resultado esperado**: No se permite la creación duplicada; el sistema devuelve el error y no se genera ningún registro nuevo ni mensaje en la cola.

---

### AC 6: Listar productos creados

- **Endpoint**: `GET /api/admin/productos` (Producer / API)
- **Funcionalidad**:
  - Devuelve una lista de productos activos almacenados en el sistema.
  - Permite filtrar por `categoria_id` y/o `subcategoria_id`.
  - Soporta paginación con los parámetros `skip` (por defecto `0`) y `limit` (por defecto `20`, máximo `100`).
  - Cada elemento en la respuesta debe incluir: `id`, `nombre`, `descripcion`, `precio`, `peso` (en gramos, entero), `categoria` (id y nombre), `subcategoria` (id y nombre), `imagenes` (array de URLs/rutas), y `cantidad_disponible`.
  - Si no hay resultados, devolver `200` con un arreglo vacío `[]`.

- **Códigos de respuesta**:
  - `200 OK`: Lista de productos (posible arreglo vacío).
  - `400 Bad Request`: Parámetros inválidos (por ejemplo, `limit` fuera de rango) con mensaje JSON explicativo.

- **Restricciones y notas**:
  - Sólo deben incluirse productos activos (`activo = 1`).
  - La respuesta debe ser estable y paginable para consumo por la UI.
  - Este endpoint se usará por la interfaz de administración y también podrá adaptarse para vistas públicas si se requiere.


## 🔁 Flujo de Validación (Producer + Consumer)

---

### AC 7: Eliminar producto por id

- **Endpoint**: `DELETE /api/admin/productos/{producto_id}` (Producer / API)
- **Funcionalidad**:
  - Realiza un borrado lógico (soft-delete) marcando `activo = 0` para el producto con el `producto_id` proporcionado.
  - Publica un mensaje en la cola `productos.eliminar` con `{ "producto_id": <id> }` para que consumidores/servicios realicen acciones adicionales si es necesario (por ejemplo, auditoría, limpieza externa).

- **Validaciones**:
  - Si el `producto_id` no existe o ya está inactivo, devolver `404 Not Found` con mensaje JSON `{ "status": "error", "message": "Producto no encontrado." }`.
  - Si ocurre un error interno al actualizar la base de datos, devolver `500` con mensaje JSON explicativo.

- **Códigos de respuesta**:
  - `200 OK`: Eliminación lógica realizada correctamente — ejemplo de cuerpo: `{ "status": "success", "message": "Producto eliminado correctamente" }`.
  - `404 Not Found`: Producto no encontrado.
  - `500 Internal Server Error`: Error interno al procesar la eliminación.

- **Restricciones y notas**:
  - El borrado debe ser lógico (no borrar la fila físicamente) para permitir auditoría y recuperación.
  - No es obligatorio eliminar inmediatamente las imágenes del sistema de archivos; decidir política de retención separadamente (por ejemplo, limpieza programada por worker).
  - El Producer debe encargarse de la validación de existencia y de publicar el mensaje; la operación DB de marcar `activo = 0` puede ejecutarse directamente por el Producer o delegarse al Worker según diseño (preferible que el Producer haga la marca y publique la notificación).


1. **Producer (FastAPI)** valida:  
   - Campos vacíos.  
   - Formato de imagen.  
   - Valores numéricos > 0.  

2. **Consumer (Node.js Worker)** valida:  
   - Nombre único.  
   - Categoría/subcategoría válidas.  
   - Conversión de peso a gramos.  

3. **SQL Server** almacena registro si todo es válido.  

---

## 🧪 Ejemplo de Payload Válido

```json
{
  "nombre": "Croquetas Premium para Gatos",
  "descripcion": "Alimento balanceado con proteína de salmón, ideal para gatos adultos.",
  "precio": 2499,
  "peso": 1500,
  "categoria": "Gatos",
  "subcategoria": "Alimento",
  "imagenFile": "<binary>"
}
