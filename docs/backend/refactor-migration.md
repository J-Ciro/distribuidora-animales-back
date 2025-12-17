# Backend Refactor Migration Guide

## Goals
- Align FastAPI backend with Clean Architecture.
- Keep tests passing during incremental moves.

## Steps
1. Create new folders under `src/api/app`: `domain`, `application`, `infrastructure`, `presentation`.
2. Move `schemas.py` into `presentation/schemas` (update imports in routers accordingly).
3. Move `routers/` into `presentation/routers`.
4. Split `services/`:
   - Business rules → `application` use cases.
   - External integrations (email, RabbitMQ) → `infrastructure/adapters`.
5. Move `repositories/` interfaces to `domain/interfaces` and implementations to `infrastructure/repositories`.
6. Move `models.py` to `infrastructure/models` and `database.py` to `infrastructure/db`.
7. Keep `dependencies.py` and `middleware/` under `presentation/`.
8. Add temporary compatibility imports file to avoid breaking old imports.

## Compatibility Layer
Create `src/api/app/compat_imports.py` re-exporting moved symbols during transition.

## Testing Strategy
- After each move, run: `./run-tests-backend.ps1`.
- Update only the affected test import paths per batch.

## Naming & Style
- Use explicit names (no one-letter vars).
- Avoid inline comments unless necessary.
- Keep minimal changes per PR to reduce risk.
