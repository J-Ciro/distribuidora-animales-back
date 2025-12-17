import os

ADMIN_CREATED_MSG = os.getenv("ADMIN_CREATED_MSG", "Administrador creado")
ADMIN_SKIPPED_MSG = os.getenv("ADMIN_SKIPPED_MSG", "El usuario Administrador ya existe. Proceso omitido.")


def test_log_contains_creation_message(read_backend_logs):
    logs = read_backend_logs()
    assert logs
    assert (ADMIN_CREATED_MSG in logs) or ("Admin user created" in logs)


def test_log_contains_skip_message(read_backend_logs):
    logs = read_backend_logs()
    assert logs
    assert (
        (ADMIN_SKIPPED_MSG in logs)
        or ("Admin already exists. Skipping." in logs)
        or ("✨ Admin seeding skipped (already exists)" in logs)
    )
