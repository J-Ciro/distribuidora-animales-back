import os
import time
import requests
import pytest

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
HEALTH_ENDPOINT = os.getenv("HEALTH_ENDPOINT", f"{BACKEND_BASE_URL}/health")
LOG_FILE_PATH = os.getenv("BACKEND_LOG_FILE", os.path.join(os.getcwd(), "logs", "backend", "app.log"))

WAIT_SECONDS = int(os.getenv("BACKEND_WAIT_SECONDS", "30"))
POLL_INTERVAL = 1


def wait_for_health(timeout_seconds=WAIT_SECONDS):
    deadline = time.time() + timeout_seconds
    last_err = None
    while time.time() < deadline:
        try:
            r = requests.get(HEALTH_ENDPOINT, timeout=3)
            if r.status_code == 200:
                return True
        except Exception as e:
            last_err = e
        time.sleep(POLL_INTERVAL)
    if last_err:
        raise RuntimeError(f"Backend health check failed: {last_err}")
    raise RuntimeError("Backend health check timed out")


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_ready():
    wait_for_health()
    yield


@pytest.fixture(scope="session")
def backend_base_url():
    return BACKEND_BASE_URL


@pytest.fixture(scope="session")
def read_backend_logs():
    def _read_logs():
        if LOG_FILE_PATH and os.path.exists(LOG_FILE_PATH):
            try:
                with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                return ""
        return ""
    return _read_logs
