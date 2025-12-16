import os
import requests
from helpers import admin_exists, login_admin

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.local")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Passw0rd!")


def test_admin_created_on_first_boot():
    assert admin_exists(ADMIN_EMAIL) is True


def test_can_login_with_seeded_admin_credentials():
    js = login_admin(ADMIN_EMAIL, ADMIN_PASS)
    token = js.get("access_token")
    assert token
    headers = {"Authorization": f"Bearer {token}"}
    resp_me = requests.get(f"{BACKEND_BASE_URL}/api/auth/me", headers=headers, timeout=10)
    assert resp_me.status_code == 200
    me_data = resp_me.json()
    assert me_data.get("rol") in ("admin", "Administrador")
