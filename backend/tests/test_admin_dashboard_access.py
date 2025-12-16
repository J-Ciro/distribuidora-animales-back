import os
import requests
from helpers import login_admin

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.local")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Passw0rd!")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def test_admin_dashboard_access():
    js = login_admin(ADMIN_EMAIL, ADMIN_PASS)
    token = js.get("token")
    assert token
    headers = {"Authorization": f"Bearer {token}"}

    # Example admin endpoints; adjust to actual routes
    resp1 = requests.get(f"{BACKEND_BASE_URL}/api/admin/inventory", headers=headers, timeout=10)
    assert resp1.status_code in (200, 204)

    # Optional write operation if allowed
    # resp2 = requests.put(f"{BACKEND_BASE_URL}/api/admin/catalog/some-id", json={"active": True}, headers=headers, timeout=10)
    # assert resp2.status_code in (200, 204)
