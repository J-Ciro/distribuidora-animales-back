
# 🤖 AI_WORKFLOW.md

Documento vivo que define cómo el **Equipo 3 – Gatos y Perros** integra inteligencia artificial en su flujo de trabajo para el desarrollo del MVP de sistema de pedidos.

> **Propósito**: Usar IA como **asistente técnico**, no como reemplazo del pensamiento crítico del equipo.

---

## 🚀 Inicio Rápido del Proyecto

### Para Nuevos Desarrolladores

Si es tu primera vez clonando el repositorio, sigue estos pasos:

1. **Requisitos previos**:
   - Windows con PowerShell 5.1+
   - Docker Desktop instalado y corriendo
   - Git instalado

2. **Clonar y configurar**:
   ```powershell
   # Clonar el repositorio backend
   git clone https://github.com/julianrodriguez-Sofka/Distribuidora_Perros_Gatos_back.git
   cd Distribuidora_Perros_Gatos_back
   
   # Clonar el repositorio frontend (en otra carpeta)
   cd ..
   git clone https://github.com/<tu-org>/Distribuidora_Perros_Gatos_front.git
   ```

3. **Ejecutar scripts de instalación** (Backend):
   ```powershell
   cd Distribuidora_Perros_Gatos_back
   
   # Paso 1: Corregir archivos de migración (solo primera vez)
   .\fix-migrations.ps1
   
   # Paso 2: Instalación completa automatizada
   .\setup.ps1
   ```

4. **Configurar Frontend**:
   ```powershell
   cd ..\Distribuidora_Perros_Gatos_front
   
   # Instalar dependencias
   npm install
   
   # Configurar variables de entorno
   cp .env.example .env
   
   # Iniciar desarrollo
   npm start
   ```

5. **Verificar instalación**:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - RabbitMQ UI: http://localhost:15672 (guest/guest)

**Tiempo total estimado**: 5-10 minutos

---

## 🧩 Metodología

- Trabajamos con **Kanban** en GitHub Projects.
- Reuniones diarias a las 8:00 am
- Tareas pequeñas (<1 día) para facilitar integración continua.
- Todo el código pasa por **pull request con al menos una revisión**.

---

## 💬 Interacciones clave

| Canal          | Uso |
|----------------|-----|
| **Chat Google**    | Comunicación diaria, resolución rápida de dudas |
| **GitHub**     | Discusión técnica, pull requests, issues |
| **Reuniones**  | Toma de decisiones arquitectónicas, priorización |

---

## 📚 Documentos clave

| Documento             | Propósito |
|-----------------------|---------|
| `README.md`           | Guía completa de instalación y uso del sistema |
| `ARCHITECTURE.md`     | Diagrama y explicación del sistema (API → RabbitMQ → Worker) |
| `AI_WORKFLOW.md`      | Este documento: normas para uso de IA y setup inicial |
| `docker-compose.yml`  | Infraestructura local del MVP (5 servicios) |
| `setup.ps1`           | **Script principal de instalación automatizada** |
| `fix-migrations.ps1`  | **Script para corregir migraciones SQL** (ejecutar antes de setup.ps1) |
| `/HU/`                | Historias de usuario con instrucciones técnicas |
| `/Promts/`            | Guías, documentación y soluciones de problemas |
| `/sql/`               | Schema, migraciones y seeders de la base de datos |

---

## 🔧 Scripts de Automatización

El proyecto incluye **scripts de PowerShell** para facilitar la configuración:

### `fix-migrations.ps1`
**Cuándo ejecutar**: Una sola vez, antes de la primera instalación

**Qué hace**:
- Convierte `init-db.sh` de CRLF a LF (compatibilidad Linux)
- Renumera migraciones secuencialmente (001-010)
- Elimina archivos duplicados de seeders
- Valida integridad de archivos SQL

**Uso**:
```powershell
.\fix-migrations.ps1
```

### `setup.ps1`
**Cuándo ejecutar**: Primera instalación o reset completo del sistema

**Qué hace** (8 pasos automatizados):
1. Valida Docker y Docker Compose
2. Limpia instalaciones anteriores
3. Configura archivos `.env` (API y Worker)
4. Configura email Gmail (opcional, guiado)
5. Valida archivos SQL de migración
6. Construye e inicia contenedores Docker
7. Verifica servicios con healthchecks robustos
8. Crea usuario administrador automáticamente

**Uso**:
```powershell
.\setup.ps1
```

**Características del script**:
- ✅ Validación de prerequisitos
- ✅ Healthchecks robustos (SQL Server: 120s, API: 60s)
- ✅ Configuración guiada de email con instrucciones para Gmail
- ✅ Creación automática de usuario Admin
- ✅ Verificación de tablas de calificaciones
- ✅ Resumen final con URLs y comandos útiles

### Otros Scripts Útiles

```powershell
# Ejecutar tests del backend
.\run-tests-backend.ps1

# Verificar estado de migraciones
.\verify-migration.ps1

# Configurar solo SMTP
.\configurar-smtp.ps1
```

---

## 🐳 Workflow con Docker

### Flujo de Trabajo Diario

```powershell
# 1. Iniciar servicios
docker-compose up -d

# 2. Ver logs en tiempo real
docker-compose logs -f

# 3. Trabajar en tu código...

# 4. Reiniciar servicios después de cambios
docker-compose restart api worker

# 5. Detener servicios al finalizar
docker-compose down
```

### Comandos Frecuentes

```powershell
# Ver estado de contenedores
docker-compose ps

# Ver logs de un servicio específico
docker logs -f distribuidora-api
docker logs -f distribuidora-worker

# Reconstruir después de cambios en Dockerfile
docker-compose up -d --build

# Acceder a SQL Server
docker exec -it sqlserver /bin/bash

# Ejecutar query SQL
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "yourStrongPassword123#" -d distribuidora_db -Q "SELECT * FROM Usuarios"

# Limpiar todo y empezar de cero (⚠️ ELIMINA DATOS)
docker-compose down -v
.\setup.ps1
```

---

## 🤖 Dinámicas de interacción con IA

### ✅ Uso permitido
- Generar **esqueletos de código**: componentes React, Dockerfiles, workers en Python.
- Explicar conceptos técnicos: patrón Saga, colas de mensajes, accesibilidad WCAG.
- Redactar o mejorar **documentación técnica** (README, guías).
- Simular conversaciones de equipo para alinear ideas.

### 🚫 Uso prohibido
- Entregar código generado 100% por IA sin comprensión del equipo.
- Usar IA para resolver exámenes, tareas individuales o entregas académicas sin autoría clara.

### 🔁 Validación obligatoria
1. Todo output de IA se **revisa en pareja** antes de commitear.
2. El código generado debe:
   - Pasar pruebas locales.
   - Seguir las convenciones del equipo.
   - Ser entendido por al menos dos miembros.
3. Si la IA sugiere una solución arquitectónica, se **discute en reunión** antes de implementar.

### 📁 Gestión de prompts
- Los prompts útiles se guardan en `/Promts/` con nombre descriptivo:  
  - `SISTEMA_CALIFICACIONES.md` - Documentación del sistema de ratings
  - `CONFIGURACION_EMAIL_ACTUALIZADA.md` - Guía de configuración SMTP
  - `VERIFICACION_MIGRACION.md` - Troubleshooting de migraciones
  - `INICIO_RAPIDO.md` - Guía rápida de inicio

### 🌍 Ética y responsabilidad
- La IA es una **herramienta de productividad**, no un actor autónomo.
- El equipo asume **responsabilidad total** sobre el código y decisiones técnicas.
- Priorizamos **transparencia**: si algo se generó con IA, se menciona en el PR o commit (ej: `feat: card de producto (asistido por IA)`).

---

## 📋 Checklist para Nuevos Miembros del Equipo

### Día 1: Setup Inicial
- [ ] Instalar Docker Desktop
- [ ] Clonar repositorios (backend y frontend)
- [ ] Ejecutar `fix-migrations.ps1` en el backend
- [ ] Ejecutar `setup.ps1` en el backend
- [ ] Crear cuenta de Gmail para testing (opcional)
- [ ] Configurar frontend con `npm install`
- [ ] Verificar acceso a Swagger UI (http://localhost:8000/docs)
- [ ] Probar login con usuario administrador creado

### Día 2-3: Familiarización
- [ ] Leer `README.md` completo
- [ ] Revisar `ARCHITECTURE.md` para entender el flujo
- [ ] Explorar historias de usuario en `/HU/`
- [ ] Ejecutar tests: `run-tests-backend.ps1`
- [ ] Revisar código de una funcionalidad completa (ej: HU_REGISTER_USER)
- [ ] Hacer un cambio pequeño y crear PR de prueba

### Semana 1: Contribución
- [ ] Tomar primera tarea del backlog
- [ ] Seguir convenciones del equipo
- [ ] Crear PR con descripción clara
- [ ] Responder a comentarios de code review
- [ ] Asistir a daily standup

---

## 🆘 Soporte y Resolución de Problemas

### Problemas Comunes y Soluciones

| Problema | Solución |
|----------|----------|
| Docker no inicia | Reiniciar Docker Desktop, verificar recursos asignados (4GB+ RAM) |
| Puerto en uso | Ver `README.md` sección Troubleshooting |
| Migraciones fallan | Ejecutar `fix-migrations.ps1` y revisar logs con `docker logs distribuidora-db-migrator` |
| Email no envía | Verificar configuración Gmail en `/Promts/CONFIGURACION_EMAIL_ACTUALIZADA.md` |
| Tests fallan | Verificar que servicios estén corriendo con `docker-compose ps` |

### Canales de Ayuda

1. **Primera opción**: Revisar documentación en `/Promts/`
2. **Segunda opción**: Preguntar en el chat del equipo
3. **Tercera opción**: Crear issue en GitHub con etiqueta `help-wanted`
4. **Última opción**: Pedir revisión en reunión diaria

---

> 🐾 *"La IA no piensa, pero nos ayuda a pensar mejor."*  
> — Equipo 3, Gatos y Perros

---

## 📚 Referencias Técnicas

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Guide](https://docs.sqlalchemy.org/en/20/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [React + Redux Toolkit](https://redux-toolkit.js.org/)

**Última actualización**: Diciembre 2025