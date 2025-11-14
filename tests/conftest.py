# Instrucciones rápidas:
# - pip install -r backend/requirements.txt pytest
# - pytest -q
#
# Notas:
# - Usa TEST_DATABASE_URL si está definida; si no, cae en SQLite (archivo temporal).
# - Desactiva rate limiting y usa Redis en memoria para las pruebas.
# - En SQLite se omiten tests que requieran índices parciales de PostgreSQL.

import os
import sys
from pathlib import Path
import tempfile
import pytest
from cryptography.fernet import Fernet

# Asegurar que "backend/" esté en sys.path para importar app.*
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# Variables de entorno para pruebas (antes de importar la app)
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("RATELIMIT_ENABLED", "0")  # desactiva rate limiting
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("JWT_SECRET", "pytest-secret")
# Clave Fernet válida para cifrado de credenciales (en dev)
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())

# DB de pruebas
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    # SQLite file-based para evitar problemas de :memory: entre conexiones
    tmpdb = Path(tempfile.gettempdir()) / "mkmonitor_pytest.sqlite"
    TEST_DB_URL = f"sqlite:///{tmpdb.as_posix()}"
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.__init__ import create_app  # noqa: E402
from app.db import db  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.auth.password import hash_password  # noqa: E402


def is_postgres() -> bool:
    return TEST_DB_URL.startswith("postgresql")


def pytest_configure(config):
    config.addinivalue_line("markers", "postgres: requiere PostgreSQL (índices parciales, etc.)")


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    # En caso de que el Limiter leyera el flag
    app.config["RATELIMIT_ENABLED"] = False
    return app


@pytest.fixture(autouse=True)
def _db_clean(app):
    # Limpiar DB antes de cada test (drop/create) para aislamiento simple
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def tenant(app):
    with app.app_context():
        t = Tenant(name="Acme Corp", plan="BASICMAAT", status_pago="activo")
        db.session.add(t)
        db.session.commit()
        return t


@pytest.fixture
def admin_user(app, tenant):
    with app.app_context():
        u = User(
            tenant_id=tenant.id,
            email="admin@example.com",
            password_hash=hash_password("secret123"),
            role="admin",
        )
        db.session.add(u)
        db.session.commit()
        return u


@pytest.fixture
def noc_user(app, tenant):
    with app.app_context():
        u = User(
            tenant_id=tenant.id,
            email="noc@example.com",
            password_hash=hash_password("secret123"),
            role="noc",
        )
        db.session.add(u)
        db.session.commit()
        return u


@pytest.fixture
def auth_token(client, admin_user):
    # Login para obtener token
    res = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    assert res.status_code == 200, res.get_data(as_text=True)
    return res.get_json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}