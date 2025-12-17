import os
import requests

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


def backend_health_ok():
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def admin_exists(email: str):
    r = requests.get(f"{BACKEND_BASE_URL}/api/admin/exists", params={"email": email}, timeout=5)
    r.raise_for_status()
    js = r.json()
    return bool(js.get("exists"))


def admin_count():
    r = requests.get(f"{BACKEND_BASE_URL}/api/admin/count", timeout=5)
    r.raise_for_status()
    js = r.json()
    return int(js.get("count", 0))


def login_admin(email: str, password: str):
    r = requests.post(f"{BACKEND_BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=10)
    r.raise_for_status()
    js = r.json()
    return js
