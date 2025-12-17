import os
import requests
from helpers import login_admin

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.local")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Passw0rd!")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def test_admin_dashboard_access():
    js = login_admin(ADMIN_EMAIL, ADMIN_PASS)
    token = js.get("access_token")
    assert token
    headers = {"Authorization": f"Bearer {token}"}

    # Verificar el rol del usuario usando /api/auth/me
    resp_me = requests.get(f"{BACKEND_BASE_URL}/api/auth/me", headers=headers, timeout=10)
    assert resp_me.status_code == 200
    me_data = resp_me.json()
    assert me_data.get("rol") in ("admin", "Administrador")

    # Example admin endpoints; ajusta si es necesario
    resp1 = requests.get(f"{BACKEND_BASE_URL}/api/admin/productos", headers=headers, timeout=10)
    assert resp1.status_code in (200, 204)

    # Optional write operation if allowed
    # resp2 = requests.put(f"{BACKEND_BASE_URL}/api/admin/catalog/some-id", json={"active": True}, headers=headers, timeout=10)
    # assert resp2.status_code in (200, 204)
