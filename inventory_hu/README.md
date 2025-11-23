HU: Manage Inventory - Estructura y cómo usar

Estructura propuesta:

- inventory_hu/
  - api/
    - app/
      - main.py
      - database.py
      - models.py
      - schemas.py
      - rabbitmq.py
      - routers/
        - productos.py
    - Dockerfile
    - requirements.txt
  - worker/
    - package.json
    - tsconfig.json
    - src/
      - index.ts
      - config.ts
      - consumer.ts
      - db.ts
    - Dockerfile
  - sql/
    - schema.sql
    - migrations/
      - 001_create_tables.sql
  - docker-compose.hu.yml

Resumen de comportamiento implementado:
- Producer (FastAPI) publica mensajes a la cola `inventario.reabastecer` con payload JSON y `requestId` UUID.
- Worker (Node.js + TypeScript) consume `inventario.reabastecer`, valida, ejecuta transacción SQL Server con SELECT ... WITH (UPDLOCK), actualiza `Productos.stock` y crea un registro en `InventarioHistorial`.
- Si hay éxito, el worker publica una respuesta en `inventario.reabastecer.responses` (JSON con requestId y status).

Mensajes literales implementados (exactos según requisito):
- "Por favor, completa todos los campos obligatorios."
- "La cantidad debe ser un número positivo."
- "Producto no encontrado."
- "Existencias actualizadas exitosamente"
- "El producto tiene al menos 10 unidades en stock."

Instrucciones rápidas para levantar (desde la raíz del repo donde está este directorio):

1) Build y up:

```powershell
# desde PowerShell
docker compose -f inventory_hu/docker-compose.hu.yml up -d --build
```

2) Comprobaciones:
- API: http://localhost:8001/docs
- RabbitMQ management: http://localhost:15672 (guest:guest)
- MailHog etc no incluido aquí.

Notas:
- Reemplaza credenciales en `docker-compose.hu.yml` antes de usar en producción.
- Este código es una implementación mínima funcional según la historia de usuario.
