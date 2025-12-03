# Guía de Pruebas - Backend y Frontend

## 📋 Tabla de Contenidos
- [Backend - Pruebas Python](#backend---pruebas-python)
- [Frontend - Pruebas React](#frontend---pruebas-react)
- [Ejecución de Pruebas](#ejecución-de-pruebas)
- [Cobertura de Código](#cobertura-de-código)
- [Buenas Prácticas](#buenas-prácticas)

---

## Backend - Pruebas Python

### Estructura de Pruebas

```
backend/api/tests/
├── __init__.py
├── conftest.py                      # Configuración de pytest
├── test_auth_utils.py               # Pruebas unitarias de seguridad
├── test_auth_integration.py         # Pruebas de integración de auth
├── test_products_integration.py     # Pruebas de integración de productos
└── test_cart_orders_integration.py  # Pruebas de integración de carrito/pedidos
```

### Tipos de Pruebas Backend

#### 1. Pruebas Unitarias
**Archivo**: `test_auth_utils.py`

Cubre:
- ✅ Hash y verificación de contraseñas
- ✅ Creación y validación de tokens JWT
- ✅ Validación de contraseñas fuertes
- ✅ Validación de formato de emails

```python
# Ejemplo de prueba unitaria
def test_password_hash_and_verify():
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
```

#### 2. Pruebas de Integración - Autenticación
**Archivo**: `test_auth_integration.py`

Cubre:
- ✅ Registro de usuarios
- ✅ Login y obtención de tokens
- ✅ Refresh de tokens
- ✅ Verificación de email
- ✅ Manejo de errores (emails duplicados, contraseñas débiles)

```python
# Ejemplo de prueba de integración
def test_register_new_user_success(client, test_user_data):
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 201
    assert "usuario_id" in response.json()["data"]
```

#### 3. Pruebas de Integración - Productos
**Archivo**: `test_products_integration.py`

Cubre:
- ✅ CRUD completo de productos
- ✅ Filtrado y búsqueda
- ✅ Paginación
- ✅ Gestión de inventario
- ✅ Historial de movimientos

#### 4. Pruebas de Integración - Carrito y Pedidos
**Archivo**: `test_cart_orders_integration.py`

Cubre:
- ✅ Agregar/actualizar/eliminar items del carrito
- ✅ Creación de pedidos
- ✅ Listado de pedidos del usuario
- ✅ Cancelación de pedidos
- ✅ Sistema de calificaciones

### Ejecución de Pruebas Backend

#### Ejecutar todas las pruebas
```bash
cd Distribuidora_Perros_Gatos_back
pytest
```

#### Ejecutar con cobertura
```bash
pytest --cov=backend/api/app --cov-report=html
```

#### Ejecutar pruebas específicas
```bash
# Solo pruebas unitarias
pytest -m unit

# Solo pruebas de integración
pytest -m integration

# Solo pruebas de autenticación
pytest -m auth

# Archivo específico
pytest backend/api/tests/test_auth_utils.py

# Prueba específica
pytest backend/api/tests/test_auth_utils.py::TestPasswordHashing::test_password_hash_and_verify
```

#### Ejecutar en modo verbose
```bash
pytest -v
```

#### Ejecutar con output de print
```bash
pytest -s
```

---

## Frontend - Pruebas React

### Estructura de Pruebas

```
src/__tests__/
├── OrderCard.test.js              # Pruebas de componente OrderCard
├── RatingStars.test.js            # Pruebas de componente RatingStars
├── authActions.test.js            # Pruebas de Redux actions
├── authReducer.test.js            # Pruebas de Redux reducers
├── useAuth.test.js                # Pruebas de custom hook
└── userFlow.integration.test.js   # Pruebas de integración E2E
```

### Tipos de Pruebas Frontend

#### 1. Pruebas de Componentes
**Archivos**: `OrderCard.test.js`, `RatingStars.test.js`

Cubre:
- ✅ Renderizado de componentes
- ✅ Interacciones de usuario (clicks, hover)
- ✅ Manejo de estados
- ✅ Props y variantes

```javascript
// Ejemplo de prueba de componente
test('expande y colapsa detalles al hacer clic', () => {
  render(<OrderCard order={mockOrder} />);
  const detailsButton = screen.getByText(/ver detalle/i);
  fireEvent.click(detailsButton);
  expect(screen.getByText(/Producto Test/i)).toBeInTheDocument();
});
```

#### 2. Pruebas de Redux
**Archivos**: `authActions.test.js`, `authReducer.test.js`

Cubre:
- ✅ Actions creators (síncronas y asíncronas)
- ✅ Reducers y transformación de estado
- ✅ Thunks y llamadas API
- ✅ Manejo de errores

```javascript
// Ejemplo de prueba de Redux
test('dispatch LOGIN_SUCCESS cuando login es exitoso', async () => {
  const store = mockStore({ auth: {} });
  await store.dispatch(actions.loginUser('test@example.com', 'password'));
  expect(store.getActions()).toContainEqual({ type: 'LOGIN_SUCCESS' });
});
```

#### 3. Pruebas de Hooks
**Archivo**: `useAuth.test.js`

Cubre:
- ✅ Retorno de valores correctos
- ✅ Métodos disponibles (login, logout, register)
- ✅ Manejo de estado de autenticación
- ✅ Errores

#### 4. Pruebas de Integración E2E
**Archivo**: `userFlow.integration.test.js`

Cubre:
- ✅ Flujo completo de registro → login
- ✅ Flujo de compra completo
- ✅ Flujo de calificación de productos
- ✅ Navegación entre páginas

```javascript
// Ejemplo de prueba de integración
test('Flujo completo: Registro → Verificación → Login', async () => {
  renderWithProviders(<App />);
  
  // Registrarse
  const registerLink = screen.getByText(/registrarse/i);
  fireEvent.click(registerLink);
  // ... llenar formulario y enviar
  
  // Login
  const loginLink = screen.getByText(/iniciar sesión/i);
  fireEvent.click(loginLink);
  // ... llenar formulario y enviar
  
  await waitFor(() => {
    expect(screen.getByText(/bienvenido/i)).toBeInTheDocument();
  });
});
```

### Ejecución de Pruebas Frontend

#### Ejecutar todas las pruebas
```bash
cd Distribuidora_Perros_Gatos_front
npm test
```

#### Ejecutar con cobertura
```bash
npm test -- --coverage
```

#### Ejecutar en modo watch (desarrollo)
```bash
npm test -- --watch
```

#### Ejecutar pruebas específicas
```bash
# Archivo específico
npm test OrderCard.test.js

# Por patrón
npm test -- --testNamePattern="auth"
```

#### Ejecutar sin watch mode (CI/CD)
```bash
npm test -- --watchAll=false
```

---

## Cobertura de Código

### Backend - Objetivo: >70%

Ver reporte de cobertura:
```bash
pytest --cov=backend/api/app --cov-report=html
# Abrir: htmlcov/index.html
```

### Frontend - Objetivo: >70%

Ver reporte de cobertura:
```bash
npm test -- --coverage --watchAll=false
# Abrir: coverage/lcov-report/index.html
```

---

## Buenas Prácticas

### General
1. ✅ **Nombrar pruebas descriptivamente**: El nombre debe indicar qué se prueba y qué se espera
2. ✅ **Arrange-Act-Assert**: Estructura clara en cada prueba
3. ✅ **Un assert por prueba**: Cuando sea posible
4. ✅ **Usar fixtures y mocks**: Evitar dependencias externas
5. ✅ **Independencia**: Cada prueba debe poder ejecutarse sola

### Backend
1. ✅ **Usar base de datos de prueba**: SQLite o Docker
2. ✅ **Limpiar estado**: Usar fixtures con scope apropiado
3. ✅ **Mock servicios externos**: RabbitMQ, emails, APIs
4. ✅ **Probar casos límite**: No solo el happy path
5. ✅ **Usar markers**: Organizar pruebas por tipo/módulo

```python
@pytest.mark.integration
@pytest.mark.auth
def test_login_success():
    # Prueba marcada como integración y auth
    pass
```

### Frontend
1. ✅ **Testing Library queries**: Preferir `getByRole`, `getByLabelText`
2. ✅ **User-centric**: Probar como lo haría un usuario
3. ✅ **Async/await**: Usar `waitFor` para operaciones asíncronas
4. ✅ **Mock API calls**: Usar `jest.fn()` o MSW
5. ✅ **Limpiar mocks**: `afterEach(() => jest.clearAllMocks())`

```javascript
// Buena práctica: Query por rol
const button = screen.getByRole('button', { name: /enviar/i });

// Evitar: Query por clase CSS
const button = container.querySelector('.submit-button');
```

---

## Integración Continua (CI/CD)

### GitHub Actions - Backend

```yaml
- name: Run Backend Tests
  run: |
    cd Distribuidora_Perros_Gatos_back
    pytest --cov=backend/api/app --cov-report=xml
```

### GitHub Actions - Frontend

```yaml
- name: Run Frontend Tests
  run: |
    cd Distribuidora_Perros_Gatos_front
    npm test -- --coverage --watchAll=false
```

---

## Comandos Rápidos

### Backend
```bash
# Ejecutar todas las pruebas con cobertura
pytest --cov

# Solo unitarias
pytest -m unit

# Solo integración
pytest -m integration

# Verbose + coverage
pytest -v --cov --cov-report=term-missing
```

### Frontend
```bash
# Todas las pruebas
npm test

# Con cobertura
npm test -- --coverage --watchAll=false

# Watch mode (desarrollo)
npm test -- --watch

# Específica
npm test OrderCard
```

---

## Solución de Problemas

### Backend

**Error**: `ModuleNotFoundError`
```bash
# Asegúrate de estar en el directorio correcto y tener el entorno activado
cd Distribuidora_Perros_Gatos_back
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Error**: `Database connection failed`
```bash
# Verificar que SQL Server Docker está corriendo
docker ps
# O usar base de datos de prueba SQLite
export DATABASE_URL="sqlite:///./test.db"
```

### Frontend

**Error**: `Cannot find module`
```bash
# Reinstalar dependencias
rm -rf node_modules
npm install
```

**Error**: `Test suite failed to run`
```bash
# Limpiar cache de Jest
npm test -- --clearCache
```

---

## Recursos Adicionales

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
- [Redux Testing](https://redux.js.org/usage/writing-tests)

---

**Última actualización**: 2024-01-15
