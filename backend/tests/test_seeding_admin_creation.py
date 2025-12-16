import os
from helpers import admin_exists, login_admin

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.local")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Passw0rd!")


def test_admin_created_on_first_boot():
    assert admin_exists(ADMIN_EMAIL) is True


def test_can_login_with_seeded_admin_credentials():
    js = login_admin(ADMIN_EMAIL, ADMIN_PASS)
    assert js.get("token")
    assert js.get("role") in ("admin", "Administrador")
