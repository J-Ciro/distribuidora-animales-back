# Backend FastAPI Architecture (Clean Architecture)

## Folder Roles
- domain: Entities, value objects, repository interfaces, domain services, exceptions.
- application: Use cases (interactors), DTOs, input/output ports, transaction boundaries.
- infrastructure: DB models, ORM repositories, messaging (RabbitMQ) adapters, email adapters.
- presentation: FastAPI routers, request/response schemas (Pydantic), dependencies, middleware.

## Naming Conventions
- Folders: use lowercase with underscores: `presentation/routers`, `infrastructure/db`
- Modules: lowercase with underscores: `security_utils.py`, `email_service.py`
- Entities: `User`, `Product`, `Order`
- Use cases: `CreateOrder`, `RegisterUser`
- Repositories: `UserRepository`, `OrderRepository` (interfaces in domain, impl in infrastructure)
- Routers: `orders_router`, `auth_router`
- Schemas: `OrderCreate`, `OrderRead`

## Incremental Migration Map
- backend/api/app/models.py → infrastructure/models
- backend/api/app/repositories/ → domain/interfaces + infrastructure/repositories
- backend/api/app/services/ → application/use_cases (business logic) + infrastructure/adapters
- backend/api/app/routers/ → presentation/routers
- backend/api/app/schemas.py → presentation/schemas
- backend/api/app/dependencies.py → presentation/dependencies
- backend/api/app/database.py → infrastructure/db
- Keep original modules during transition; add shims in `presentation/routers` that re-export existing `app.routers.*` to minimize diffs.

## Import Rules
- presentation depends on application
- application depends on domain
- infrastructure depends on domain and application only via interfaces
- domain is pure and depends on nothing external

## Example Imports
- presentation → `from application.orders.create_order import CreateOrder`
- application → `from domain.orders.entities import Order`
- infrastructure → `from domain.orders.repositories import OrderRepository`
