# 📋 Resumen del Proyecto - Distribuidora Perros y Gatos

**Fecha de documentación**: 4 de Diciembre, 2025  
**Equipo de Desarrollo**: Equipo 3  
**Stack Tecnológico**: FastAPI (Python) + React + RabbitMQ + SQL Server

---

## 🎯 Descripción General del Proyecto

Sistema web distribuido para una distribuidora de productos para mascotas (perros y gatos) que implementa un modelo **producer-consumer** con procesamiento asíncrono mediante **RabbitMQ**. El sistema gestiona un catálogo de productos, autenticación de usuarios, carrito de compras, pedidos, inventario, sistema de calificaciones y un panel administrativo completo.

### Características Principales
- ✅ Autenticación JWT con refresh tokens
- ✅ Sistema de verificación por email
- ✅ Gestión completa de productos y categorías
- ✅ Control de inventario en tiempo real
- ✅ Sistema de pedidos con estados
- ✅ Calificaciones y reseñas de productos
- ✅ Panel administrativo con gestión de usuarios
- ✅ Carrusel de imágenes configurable
- ✅ Procesamiento asíncrono de emails
- ✅ Arquitectura escalable y desacoplada

---

## 🏗️ Arquitectura del Sistema

### Modelo Producer-Consumer

```
┌─────────────────┐                 ┌──────────────────┐
│  Frontend       │    HTTP/JSON    │  FastAPI API     │
│  (React/Redux)  │ <-------------> │  (Producer)      │
│  Puerto 3000    │                 │  Puerto 8000     │
└─────────────────┘                 └──────────┬───────┘
                                               │
                                               │ Publica
                                               ▼
                                    ┌──────────────────┐
                                    │   RabbitMQ       │
                                    │   (Message       │
                                    │    Broker)       │
                                    └──────────┬───────┘
                                               │
                                               │ Consume
                                               ▼
                        ┌──────────────────────────────┐
                        │  Node.js Worker              │
                        │  (Consumer)                  │
                        │  - Envío de emails           │
                        │  - Procesamiento asíncrono   │
                        └──────────────────────────────┘
                                    │
                                    │ Persiste
                                    ▼
                        ┌──────────────────────────────┐
                        │  SQL Server                  │
                        │  Base de Datos               │
                        └──────────────────────────────┘
```

### Componentes
1. **Frontend React**: Interfaz de usuario con Redux para gestión de estado
2. **Backend FastAPI**: API REST que actúa como producer de mensajes
3. **RabbitMQ**: Message broker para procesamiento asíncrono
4. **Worker Node.js**: Consumer que procesa tareas pesadas (emails, etc.)
5. **SQL Server**: Base de datos relacional

---

## 🎨 Principios SOLID Implementados

### 1. **Single Responsibility Principle (SRP)**

#### Backend - Capa de Servicios
**Archivo**: `backend/api/app/services/auth_service.py`
```python
class AuthService:
    """
    Centraliza TODA la lógica de negocio de autenticación
    Una sola responsabilidad: gestionar autenticación
    """
    def register_user(self, data: RegisterRequest) -> Usuario
    def verify_email(self, email: str, code: str) -> Usuario
    def login_user(self, credentials: LoginRequest) -> TokenResponse
```

**Beneficio**: La lógica de negocio está separada de los routers, facilitando testing y mantenimiento.

#### Backend - Segregación de Utilidades de Seguridad
**Archivo**: `backend/api/app/utils/security_v2.py`

**ANTES** (Violación SRP):
```python
class SecurityUtils:
    # Mezclaba: passwords, JWT, refresh tokens, verification codes
    # Una clase con 4 responsabilidades diferentes
```

**DESPUÉS** (Cumple SRP):
```python
class PasswordHasher:              # Solo hashing de passwords
class JWTManager:                  # Solo JWT access tokens
class RefreshTokenManager:         # Solo refresh tokens
class VerificationCodeGenerator:   # Solo códigos de verificación
```

**Beneficio**: Cada clase tiene una única razón para cambiar, módulos pueden importar solo lo necesario.

#### Frontend - Separación de Responsabilidades
**Estructura**:
```
services/
├── auth-service.js        # Solo autenticación
├── productos-service.js   # Solo productos
├── pedidos-service.js     # Solo pedidos
└── categorias-service.js  # Solo categorías
```

Cada servicio tiene una única responsabilidad del dominio.

---

### 2. **Open/Closed Principle (OCP)**

#### Backend - Centralización de Constantes
**Archivo**: `backend/api/app/constants.py`
```python
class QueueNames:
    EMAIL_VERIFICATION = "email.verification"
    EMAIL_ORDER_CONFIRMATION = "email.order.confirmation"
    # Agregar nuevas colas sin modificar código existente

class EmailTemplates:
    VERIFICATION = "verification_email"
    ORDER_CONFIRMATION = "order_confirmation"
    # Extensible sin modificar clases que las usan
```

**Beneficio**: Nuevas constantes se agregan sin modificar el código que las consume.

#### Frontend - Redux Reducers Extensibles
```javascript
const authReducer = (state = initialState, action) => {
    switch (action.type) {
        case 'LOGIN_SUCCESS': return { ...state, user: action.payload }
        case 'LOGOUT': return { ...state, user: null }
        // Nuevos casos se agregan sin modificar los existentes
    }
};
```

**Beneficio**: Abierto para extensión (nuevos actions), cerrado para modificación (casos existentes).

---

### 3. **Liskov Substitution Principle (LSP)**

#### Backend - Herencia en Modelos SQLAlchemy
```python
# Todos los modelos heredan de Base y cumplen su contrato
class Usuario(Base):
    __tablename__ = "usuarios"
    # Cumple el contrato completo de Base

class Producto(Base):
    __tablename__ = "Productos"
    # Puede sustituir a Base sin romper funcionalidad
```

**Beneficio**: Cualquier modelo puede sustituir a Base en operaciones genéricas de SQLAlchemy.

---

### 4. **Interface Segregation Principle (ISP)**

#### Backend - Interfaces de Repositorios
**Archivo**: `backend/api/app/interfaces/repositories.py`
```python
class UserRepository(Protocol):
    """Interfaz específica para usuarios"""
    def find_by_id(self, user_id: int) -> Optional[Usuario]: ...
    def find_by_email(self, email: str) -> Optional[Usuario]: ...
    def create(self, user: Usuario) -> Usuario: ...

class VerificationCodeRepository(Protocol):
    """Interfaz específica para códigos de verificación"""
    def create(self, code: VerificationCode) -> VerificationCode: ...
    def find_valid_code(self, email: str) -> Optional[VerificationCode]: ...

class RefreshTokenRepository(Protocol):
    """Interfaz específica para refresh tokens"""
    def create(self, token: RefreshToken) -> RefreshToken: ...
    def revoke(self, token_hash: str) -> bool: ...
```

**Beneficio**: Cada repositorio tiene solo los métodos que necesita, no una interfaz genérica gigante.

---

### 5. **Dependency Inversion Principle (DIP)**

#### Backend - Abstracción de Message Broker
**Archivo**: `backend/api/app/interfaces/message_broker.py`
```python
class MessageBroker(Protocol):
    """Interfaz para message brokers"""
    def publish(self, queue_name: str, message: Dict) -> None: ...
```

**Implementación concreta**:
```python
class RabbitMQProducer(MessageBroker):
    """Implementación específica con RabbitMQ"""
    def publish(self, queue_name: str, message: Dict) -> None:
        # Implementación con pika
```

**Inyección de dependencias**:
```python
@router.post("/register")
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),  # ✅ DI
    message_broker: MessageBroker = Depends(get_message_broker)  # ✅ DI
):
    # El router depende de abstracciones, no implementaciones concretas
```

**Beneficio**: 
- Fácil cambiar de RabbitMQ a Kafka/SQS sin modificar routers
- Fácil mockear para testing
- Bajo acoplamiento

#### Frontend - Inversión con localStorage
**Problema detectado**: Dependencia directa en múltiples archivos
```javascript
// ANTES: Acoplamiento directo
const token = localStorage.getItem('access_token');
```

**Solución propuesta**: StorageService con interfaz abstracta
```javascript
class StorageService {
    get(key) { return localStorage.getItem(key); }
    set(key, value) { localStorage.setItem(key, value); }
}
// Componentes dependen de StorageService, no de localStorage directamente
```

---

## 🎨 Patrones de Diseño Implementados

### 1. **Repository Pattern** ⭐⭐⭐⭐⭐

**Problema Original**: Acceso directo a BD desde routers
```python
# ANTES (Acoplamiento fuerte)
@router.get("/usuarios")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(Usuario).filter(...).all()  # ❌ SQL en router
```

**Solución Implementada**:

**Interfaces** (`app/interfaces/repositories.py`):
```python
class UserRepository(Protocol):
    def find_by_id(self, user_id: int) -> Optional[Usuario]: ...
    def find_by_email(self, email: str) -> Optional[Usuario]: ...
    def email_exists(self, email: str) -> bool: ...
    def create(self, user: Usuario) -> Usuario: ...
```

**Implementación** (`app/repositories/user_repository.py`):
```python
class SQLAlchemyUserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(
            func.lower(Usuario.email) == func.lower(email)
        ).first()
```

**Uso en Router**:
```python
@router.get("/usuarios")
async def get_users(
    user_repo: UserRepository = Depends(get_user_repository)  # ✅ Abstracción
):
    users = await user_repo.find_all()  # ✅ Sin SQL directo
```

**Beneficios**:
- ✅ Abstracción de acceso a datos
- ✅ Fácil cambiar de SQL Server a PostgreSQL
- ✅ Fácil mockear para testing
- ✅ Lógica de queries centralizada

---

### 2. **Service Layer Pattern** ⭐⭐⭐⭐⭐

**Implementación**: `app/services/auth_service.py`
```python
class AuthService:
    def __init__(
        self, 
        db: Session,
        user_repo: UserRepository,
        message_broker: MessageBroker
    ):
        self.db = db
        self.user_repo = user_repo
        self.message_broker = message_broker
    
    async def register_user(self, data: RegisterRequest) -> Usuario:
        # Toda la lógica de negocio aquí
        if await self.user_repo.email_exists(data.email):
            raise EmailAlreadyExistsError()
        
        user = await self.user_repo.create(...)
        code = self._generate_verification_code()
        await self.message_broker.publish("email.verification", {...})
        return user
```

**Beneficios**:
- ✅ Lógica de negocio separada de routers
- ✅ Testeable independientemente
- ✅ Reutilizable en diferentes contextos

---

### 3. **Dependency Injection Pattern** ⭐⭐⭐⭐⭐

**Archivo**: `app/dependencies.py`
```python
def get_user_repository(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    """Provee instancia del repositorio de usuarios"""
    return SQLAlchemyUserRepository(db)

def get_message_broker() -> MessageBroker:
    """Provee instancia del message broker"""
    return rabbitmq_producer

def get_auth_service(
    db: Session = Depends(get_db),
    user_repo = Depends(get_user_repository),
    message_broker: MessageBroker = Depends(get_message_broker)
) -> AuthService:
    """Provee instancia del servicio de autenticación con todas sus dependencias"""
    return AuthService(db, user_repo, message_broker)
```

**Uso en Routers**:
```python
@router.post("/register")
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)  # ✅ Inyección
):
    user, message = auth_service.register_user(request)
    return StandardResponse(status="success", message=message)
```

**Beneficios**:
- ✅ Desacoplamiento total
- ✅ Testing simplificado (inyectar mocks)
- ✅ Configuración centralizada

---

### 4. **Singleton Pattern** ⭐⭐⭐⭐⭐

**Implementación**: `app/utils/rabbitmq.py`
```python
# Instancia global única de RabbitMQ producer
rabbitmq_producer = RabbitMQProducer()
```

**Beneficio**: Una única conexión a RabbitMQ en toda la aplicación, evitando overhead de conexiones múltiples.

---

### 5. **Factory Pattern** ⭐⭐⭐⭐

**Implementación**: `app/database.py`
```python
def get_db() -> Generator[Session, None, None]:
    """Factory para crear sesiones de BD con cleanup automático"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Beneficio**: Creación consistente de sesiones con gestión automática de recursos.

---

### 6. **Flux/Redux Pattern (Frontend)** ⭐⭐⭐⭐⭐

**Flujo unidireccional de datos**:
```
Component → Action → Reducer → Store → Component
```

**Implementación**:
```javascript
// src/redux/
├── actions/
│   └── authActions.js        // Acciones para autenticación
├── reducers/
│   └── authReducer.js        // Reducer de autenticación
└── store.js                  // Store central
```

**Beneficio**: Estado predecible y centralizado, debugging facilitado.

---

### 7. **Container/Presentational Pattern (Frontend)** ⭐⭐⭐⭐

**Separación de lógica y presentación**:
```javascript
// Container (lógica)
const HomePage = () => {
    const dispatch = useDispatch();
    const catalog = useSelector(state => state.productos.catalog);
    
    useEffect(() => { loadCatalog(); }, []);
    
    return <HomeView catalog={catalog} />;  // ✅ Delega presentación
};

// Presentational (UI pura)
const HomeView = ({ catalog }) => (
    <div>{catalog.map(product => <ProductCard {...product} />)}</div>
);
```

**Beneficio**: Componentes UI reutilizables, lógica centralizada y testeable.

---

## 🧪 Principios FIRST en Testing

El proyecto implementa **110 tests** (42 backend + 68 frontend) siguiendo los principios **FIRST**:

### **F - Fast (Rápido)**
```python
# Backend: Tests ejecutan en ~32 segundos (42 tests)
# Frontend: Tests ejecutan en <10 segundos (68 tests)
```
- ✅ SQLite in-memory para tests backend (sin latencia de red)
- ✅ Mocks de api-client en frontend (sin HTTP real)
- ✅ Tests unitarios sin dependencias externas

### **I - Independent (Independiente)**
```python
# Backend: Cada test tiene su propia BD limpia
@pytest.fixture(scope="function")
def test_db():
    """Crea DB limpia para cada test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    # Cada test es completamente independiente
```

```javascript
// Frontend: Limpieza entre tests
beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    // Estado limpio para cada test
});
```

**Beneficio**: Tests pueden ejecutarse en cualquier orden sin afectarse mutuamente.

### **R - Repeatable (Repetible)**
- ✅ **Sin dependencias externas**: No se conectan a servicios reales (email, BD producción)
- ✅ **Datos controlados**: Fixtures y mocks garantizan mismo input
- ✅ **Aislamiento completo**: Cada test crea su propio entorno

```python
# Mismo resultado en cada ejecución
def test_password_hash_and_verify_success():
    password = "TestPassword123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    # ✅ Siempre pasa, en cualquier máquina, cualquier momento
```

### **S - Self-validating (Auto-validante)**
```python
# Assertions claras y explícitas
def test_create_user():
    user = repo.create(sample_user)
    
    assert user.id is not None              # ✅ Verifica ID asignado
    assert user.email == "test@example.com" # ✅ Verifica email
    assert user.is_active is True           # ✅ Verifica estado
    # Sin necesidad de inspección manual
```

```javascript
test('debe validar email correcto', () => {
    const result = validateEmail('test@example.com');
    
    expect(result.isValid).toBe(true);      // ✅ Auto-validante
    expect(result.error).toBe(null);        // ✅ Sin errores
});
```

**Beneficio**: No requiere inspección manual de logs o outputs.

### **T - Timely (Oportuno)**
- ✅ Tests escritos **junto con el código** de producción
- ✅ Tests ejecutados en **cada cambio** (via scripts automatizados)
- ✅ **Feedback inmediato** sobre regresiones

**Scripts de ejecución**:
```powershell
# Backend
.\run-tests-backend.ps1    # Ejecuta 42 tests + reporte cobertura

# Frontend
.\run-tests-frontend.ps1   # Ejecuta 68 tests + reporte cobertura
```

---

## 📊 Distribución de Tests

### Backend (42 tests - 100% ✅)

#### **Tests Unitarios (33 tests - 78%)**
1. **Seguridad** (`test_security_utils.py`) - 15 tests
   - Password hashing con bcrypt (3 tests)
   - JWT tokens - creación, verificación, expiración (4 tests)
   - Refresh tokens - generación, unicidad (2 tests)
   - Verification codes - generación, hashing, validación (6 tests)

2. **Repositorios** (`test_repositories.py`) - 18 tests
   - Usuario Repository: CRUD, búsquedas, validaciones (16 tests)
   - Verification Code Repository (1 test)
   - Refresh Token Repository (1 test)

#### **Tests de Integración (9 tests - 22%)**
3. **Endpoints** (`test_auth_endpoints.py`) - 9 tests
   - Registro con validaciones (5 tests)
   - Login y manejo de errores (3 tests)
   - Health check (1 test)

**Patrón AAA (Arrange-Act-Assert)**:
```python
def test_password_hash_and_verify_success():
    # ARRANGE
    password = "TestPassword123!"
    
    # ACT
    hashed = hash_password(password)
    result = verify_password(password, hashed)
    
    # ASSERT
    assert result is True
    assert hashed != password
```

---

### Frontend (68 tests - 100% ✅)

#### **Tests Unitarios (55 tests - 81%)**
1. **Validaciones** (`validation.test.js`) - 37 tests
   - Email, password, cédula, teléfono, nombre
   - Archivos de imagen
   - Formateo de datos (precio, fecha, peso)
   - Preferencias de mascotas

2. **Auth Utils** (`auth.test.js`) - 18 tests
   - Función `isAdminUser` con múltiples formatos
   - Edge cases (null, undefined, strings, numbers)

#### **Tests de Integración (13 tests - 19%)**
3. **Auth Service** (`auth-service.test.js`) - 13 tests
   - Login/Logout con localStorage (2 tests)
   - Register, verify, resend (3 tests)
   - Admin products (2 tests)
   - Manejo de errores de red y servidor (4 tests)

**Mock de dependencias externas**:
```javascript
// Mock del api-client completo
jest.mock('../services/api-client');

test('debe hacer login exitosamente', async () => {
    // ARRANGE: Mock de respuesta
    apiClient.post.mockResolvedValue({
        data: { access_token: 'fake-token', user: { role: 'customer' } }
    });
    
    // ACT: Llamar servicio
    const result = await authService.login('test@test.com', 'pass123');
    
    // ASSERT: Verificar resultado
    expect(result.access_token).toBe('fake-token');
    expect(localStorage.getItem('access_token')).toBe('fake-token');
});
```

---

## 🎯 Beneficios de la Arquitectura Implementada

### 1. **Escalabilidad**
- ✅ Workers pueden escalarse horizontalmente
- ✅ RabbitMQ maneja picos de carga
- ✅ Backend stateless (JWT)

### 2. **Mantenibilidad**
- ✅ Código organizado por capas (routers, services, repositories)
- ✅ Principios SOLID aplicados consistentemente
- ✅ 110 tests automatizados (100% pasando)
- ✅ Documentación exhaustiva

### 3. **Testabilidad**
- ✅ Inyección de dependencias facilita mocking
- ✅ Repository pattern desacopla BD
- ✅ Service layer testeable independientemente
- ✅ Principios FIRST en todos los tests

### 4. **Flexibilidad**
- ✅ Fácil cambiar de RabbitMQ a otro broker (abstracción MessageBroker)
- ✅ Fácil cambiar de SQL Server a PostgreSQL (Repository Pattern)
- ✅ Fácil agregar nuevos servicios sin modificar existentes (OCP)

### 5. **Seguridad**
- ✅ JWT con refresh tokens
- ✅ Bcrypt para passwords
- ✅ Validaciones en múltiples capas
- ✅ Sin credenciales hardcodeadas (variables de entorno)

---

## 📈 Métricas de Calidad

| Métrica | Backend | Frontend | Total |
|---------|---------|----------|-------|
| **Tests Totales** | 42 | 68 | 110 |
| **Tests Pasando** | 42 (100%) | 68 (100%) | 110 (100%) |
| **Cobertura Estimada** | ~85% | ~90% | ~87% |
| **Archivos de Tests** | 3 | 3 | 6 |
| **Principios SOLID** | ✅ 5/5 | ✅ 4/5 | - |
| **Patrones de Diseño** | 5 implementados | 2 implementados | 7 total |

---

## 🛠️ Tecnologías y Herramientas

### Backend
- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Testing**: pytest 7.4.3, pytest-asyncio 0.21.1, httpx 0.25.1
- **Seguridad**: bcrypt 4.1.1, python-jose 3.3.0
- **Message Broker**: pika (RabbitMQ client)
- **Base de Datos**: SQL Server (pyodbc)

### Frontend
- **Framework**: React 18.2.0
- **Estado**: Redux 4.2.1, React-Redux 8.0.5
- **Routing**: React Router DOM 6.8.1
- **HTTP Client**: Axios 1.6.0
- **Testing**: Jest (react-scripts 5.0.1), React Testing Library

### Infraestructura
- **Containerización**: Docker + Docker Compose
- **Message Broker**: RabbitMQ 3.12
- **Base de Datos**: SQL Server 2022

---

## 📚 Documentación Adicional

- **ARCHITECTURE.md**: Arquitectura detallada backend y frontend
- **TESTING_STATUS.md**: Estado completo de testing (backend y frontend)
- **AUDIT_REPORT.md**: Auditoría completa de principios SOLID y patrones
- **REFACTORING_SUMMARY.md**: Resumen de refactorizaciones aplicadas
- **AI_WORKFLOW.md**: Guía de desarrollo y flujos de trabajo

---

## ✅ Conclusión

El proyecto **Distribuidora Perros y Gatos** demuestra una implementación sólida de principios de ingeniería de software:

- ✅ **SOLID**: Los 5 principios aplicados consistentemente
- ✅ **Patrones de Diseño**: Repository, Service Layer, DI, Singleton, Factory, Flux/Redux
- ✅ **FIRST**: 110 tests que siguen los principios de testing efectivo
- ✅ **Clean Architecture**: Separación clara de responsabilidades en capas
- ✅ **Asincronismo**: Producer-consumer pattern con RabbitMQ
- ✅ **Escalabilidad**: Arquitectura desacoplada y stateless

El sistema está preparado para escalar, mantener y extender de manera eficiente.

---

**Desarrollado por**: Equipo 3  
**Última actualización**: 4 de Diciembre, 2025
