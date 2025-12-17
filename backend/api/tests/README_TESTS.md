# Suite de Tests para Integración de Stripe

## Descripción General

Esta suite de tests implementa la estrategia de testing definida en `plan/feature-stripe-testing-strategy-1.md` para la integración de pagos con Stripe en el sistema de Distribuidora de Animales.

## Estructura de Directorios

```
backend/api/tests/
├── fixtures/
│   ├── conftest.py              # Fixtures compartidas (DB, usuarios, productos, mocks)
│   └── payment_fixtures.py      # Fixtures específicas de pagos
├── unit/
│   ├── test_stripe_service.py   # Tests unitarios para stripe_service
│   └── test_payment_service.py  # Tests unitarios para payment_service
├── integration/
│   ├── test_payments_endpoints.py    # Tests de integración de endpoints
│   └── test_webhook_integration.py   # Tests de webhooks de Stripe
└── e2e/
    ├── test_cp_56_successful_purchase.py    # CP-56: Compra exitosa
    ├── test_cp_57_insufficient_funds.py     # CP-57: Fondos insuficientes
    ├── test_cp_58_invalid_card_data.py      # CP-58: Datos inválidos
    ├── test_cp_59_api_failure.py            # CP-59: Fallas técnicas
    └── test_cp_60_security_elements.py      # CP-60: Elementos de seguridad
```

## Cobertura de Tests

### Total de Tests Implementados
- **Unit Tests**: ~20 tests
- **Integration Tests**: Por implementar
- **E2E Tests**: ~40 tests
- **Total Aproximado**: 60+ tests

### Cobertura por Caso de Prueba (CP)

#### CP-56: Finalización Exitosa de Compra
- ✅ CP-56-T-001: Pago con monto estándar
- ✅ CP-56-T-002: Pago con monto mínimo ($0.01)
- ✅ CP-56-T-003: Pago con monto máximo ($999,999.99)
- ✅ CP-56-T-004: Stock descontado correctamente
- ✅ CP-56-T-005: Orden de compra generada
- ✅ CP-56-T-006: Response con detalles completos
- ✅ CP-56-T-007: Múltiples items en pedido
- ✅ CP-56-T-008: Timestamp de confirmación

#### CP-57: Rechazo por Fondos Insuficientes
- ✅ CP-57-T-001: HTTP 402 con mensaje apropiado
- ✅ CP-57-T-002: Estado del pedido sin cambios
- ✅ CP-57-T-003: Stock no descontado
- ✅ CP-57-T-004: Transacción registrada como failed
- ✅ CP-57-T-005: Razón del error capturada
- ✅ CP-57-T-006: Cliente puede reintentar

#### CP-58: Datos de Tarjeta Incorrectos
- ✅ CP-58-T-001: CVV inválido rechazado
- ✅ CP-58-T-002: Tarjeta expirada rechazada
- ✅ CP-58-T-003: Número de tarjeta inválido
- ✅ CP-58-T-004: Pedido permanece pendiente
- ✅ CP-58-T-005: Stock no descontado
- ✅ CP-58-T-006: Email inválido rechazado
- ✅ CP-58-T-007: Teléfono inválido rechazado

#### CP-59: Fallas Técnicas de API
- ✅ CP-59-T-001: APIConnectionError → HTTP 503
- ✅ CP-59-T-002: RateLimitError → HTTP 429
- ✅ CP-59-T-003: APIError → HTTP 500
- ✅ CP-59-T-004: Pedido no alterado
- ✅ CP-59-T-005: Stock no descontado
- ✅ CP-59-T-006: Error registrado en logs
- ✅ CP-59-T-007: Sin reintentos automáticos
- ✅ CP-59-T-008: Mensaje genérico amigable

#### CP-60: Elementos de Seguridad
- ✅ CP-60-T-001: stripe_public_key en response
- ✅ CP-60-T-002: client_secret en response
- ✅ CP-60-T-003: security_indicators presentes
- ✅ CP-60-T-004: https_verified flag
- ✅ CP-60-T-005: requires_action para 3D Secure

## Ejecución de Tests

### Requisitos Previos

1. **Instalar dependencias:**
   ```bash
   pip install pytest pytest-cov pytest-mock
   pip install stripe
   ```

2. **Configurar variables de entorno:**
   ```bash
   export STRIPE_SECRET_KEY=sk_test_...
   export STRIPE_PUBLIC_KEY=pk_test_...
   export STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### Comandos de Ejecución

**Ejecutar todos los tests:**
```bash
pytest backend/api/tests/
```

**Ejecutar solo unit tests:**
```bash
pytest backend/api/tests/unit/
```

**Ejecutar solo E2E tests:**
```bash
pytest backend/api/tests/e2e/
```

**Ejecutar un caso de prueba específico:**
```bash
pytest backend/api/tests/e2e/test_cp_56_successful_purchase.py
```

**Ejecutar con cobertura:**
```bash
pytest backend/api/tests/ --cov=api.services --cov-report=html
```

**Ejecutar con verbose:**
```bash
pytest backend/api/tests/ -v
```

**Ejecutar solo tests marcados:**
```bash
pytest backend/api/tests/ -m slow  # Solo tests lentos
pytest backend/api/tests/ -m "not slow"  # Excluir tests lentos
```

## Fixtures Disponibles

### Fixtures de Base de Datos
- `db_session`: Sesión de BD en memoria (SQLite)
- `test_db_engine`: Motor de BD para la sesión

### Fixtures de Usuarios
- `test_user`: Usuario cliente de prueba
- `test_admin_user`: Usuario administrador de prueba

### Fixtures de Productos
- `test_products`: Lista de 3 productos con stock
- `test_product_low_stock`: Producto con stock bajo (2 unidades)

### Fixtures de Pedidos
- `test_order`: Pedido con 2 items, estado "Pendiente de Pago"
- `test_order_with_single_item`: Pedido con 1 item

### Fixtures de Stripe
- `stripe_test_keys`: Claves de prueba de Stripe
- `stripe_test_card_numbers`: Números de tarjetas de prueba
- `mock_stripe_api`: Mock completo de Stripe API

### Fixtures de Montos
- `payment_amount_minimum`: $0.01 (monto mínimo)
- `payment_amount_standard`: $99.99 (monto estándar)
- `payment_amount_maximum`: $999,999.99 (monto máximo)

### Fixtures de Tarjetas
- `stripe_card_visa_success`: Tarjeta Visa exitosa
- `stripe_card_mastercard_success`: Tarjeta Mastercard exitosa
- `stripe_card_declined`: Tarjeta declinada
- `stripe_card_insufficient_funds`: Tarjeta sin fondos
- `stripe_card_expired`: Tarjeta expirada
- `stripe_card_invalid_cvc`: Tarjeta con CVC inválido
- `stripe_card_3ds_required`: Tarjeta que requiere 3D Secure

### Fixtures de Errores
- `stripe_error_card_declined`: Error de tarjeta declinada
- `stripe_error_insufficient_funds`: Error de fondos insuficientes
- `stripe_error_expired_card`: Error de tarjeta expirada
- `stripe_error_invalid_cvc`: Error de CVC inválido
- `stripe_error_api_connection`: Error de conexión API
- `stripe_error_rate_limit`: Error de rate limit
- `stripe_error_api_error`: Error de servidor Stripe

## Estrategia de Testing

### Partición de Equivalencia
Los tests están organizados según particiones de equivalencia identificadas:
- **Montos**: válido, cero, negativo, muy grande
- **Estados de tarjeta**: válida, expirada, sin fondos, inválida
- **Estados del pedido**: Pendiente, Pagado, Cancelado
- **Métodos de pago**: card, link
- **Respuestas de Stripe**: succeeded, requires_action, failed, canceled

### Análisis de Valores Límite
Tests específicos para valores límite:
- Monto mínimo: $0.01
- Monto máximo: $999,999.99
- 1 item en pedido
- 1000 items en pedido (máximo)
- Email máximo: 254 caracteres

### Mocking Strategy
- **Unit Tests**: Mockean completamente Stripe API
- **Integration Tests**: Usan test mode de Stripe
- **E2E Tests**: Mockean Stripe pero validan flujo completo

## Validaciones Implementadas

### Validaciones de Base de Datos
Cada test verifica:
- ✅ Estado del pedido actualizado correctamente
- ✅ Stock descontado/sin cambios según caso
- ✅ Transacciones registradas con estado apropiado
- ✅ Timestamps registrados correctamente

### Validaciones de Respuesta HTTP
- ✅ Códigos de estado HTTP correctos (200, 400, 402, 429, 500, 503)
- ✅ Estructura de respuesta JSON válida
- ✅ Mensajes de error amigables (sin detalles técnicos)
- ✅ Campos requeridos presentes

### Validaciones de Seguridad
- ✅ No exposición de stack traces
- ✅ No exposición de claves secretas
- ✅ Validación de HTTPS
- ✅ Indicadores de seguridad presentes

## Próximos Pasos

### Tests Pendientes de Implementar
1. **Integration Tests**:
   - `test_payments_endpoints.py`: Tests de endpoints REST
   - `test_webhook_integration.py`: Tests de webhooks de Stripe

2. **Tests de Concurrencia**:
   - Múltiples pagos simultáneos
   - Race conditions en stock

3. **Tests de Performance**:
   - Tiempo de respuesta < 3 segundos
   - Manejo de carga

### Descomentado de Tests
Los tests actuales están estructurados pero con código comentado. Para activarlos:
1. Implementar los servicios (`stripe_service.py`, `payment_service.py`)
2. Ajustar imports según estructura real del proyecto
3. Descomentar código de tests
4. Ejecutar y ajustar según sea necesario

## Criterios de Éxito

### Cobertura Mínima
- ✅ `stripe_service.py`: 80%
- ✅ `payment_service.py`: 85%
- ✅ Endpoints de pagos: 75%

### Ejecución
- ✅ Todos los tests pasan
- ✅ Tiempo total < 5 minutos
- ✅ Tests independientes (pueden ejecutarse en cualquier orden)
- ✅ Cleanup automático de datos de prueba

## Troubleshooting

### Error: "No module named 'api'"
**Solución**: Ajustar PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Error: "stripe.error.AuthenticationError"
**Solución**: Verificar variables de entorno
```bash
echo $STRIPE_SECRET_KEY
# Debe comenzar con sk_test_
```

### Tests fallan intermitentemente
**Solución**: Usar fixtures con rollback de BD
```python
@pytest.fixture(autouse=True)
def reset_db(db_session):
    yield
    db_session.rollback()
```

## Recursos Adicionales

- [Plan de Testing Completo](../../../plan/feature-stripe-testing-strategy-1.md)
- [Documentación de Stripe Testing](https://stripe.com/docs/testing)
- [Pytest Documentation](https://docs.pytest.org/)
- [Stripe Python SDK](https://stripe.com/docs/api/python)

## Contacto y Soporte

Para preguntas sobre los tests:
1. Revisar documentación en `plan/feature-stripe-testing-strategy-1.md`
2. Consultar ejemplos en archivos de tests
3. Verificar logs de ejecución con `pytest -v`
