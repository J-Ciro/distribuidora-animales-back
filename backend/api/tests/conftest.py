"""
Archivo de configuración para pytest
"""
import pytest
import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuración de pytest
pytest_plugins = []

@pytest.fixture(scope="session")
def test_app():
    """Fixture para la aplicación de prueba"""
    from app.main import app
    return app

def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
