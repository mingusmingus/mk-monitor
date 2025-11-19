import json
import sys
import os
from pathlib import Path
from cryptography.fernet import Fernet

# Asegurar que el path de backend esté accesible para import estático (pylance/pytest)
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.models.device import Device  # noqa: E402
from app.db import db  # noqa: E402


def test_health_endpoint_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert "status" in data
    # Acepta "ok" o equivalente (p.ej., "healthy")
    assert str(data["status"]).lower() in {"ok", "healthy"}


def _encrypt(s: str, key: str) -> str:
    f = Fernet(key.encode())
    return f.encrypt(s.encode()).decode()


def test_health_devices_empty(client, auth_headers, tenant):
    # Sin dispositivos todavía -> lista vacía
    res = client.get("/api/health/devices", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert data == []


def test_health_devices_with_one(client, auth_headers, tenant):
    # Crear un device para el tenant
    enc_key = client.application.config.get("ENCRYPTION_KEY")
    # En dev/tests puede ser None si no se leyó; usar fixture env var
    if not enc_key:
        enc_key = os.environ["ENCRYPTION_KEY"]
    d = Device(
        tenant_id=tenant,
        name="Router Principal",
        ip_address="192.0.2.1",
        port=22,
        username_encrypted=_encrypt("admin", enc_key),
        password_encrypted=_encrypt("password123", enc_key),
    )
    db.session.add(d)
    db.session.commit()

    res = client.get("/api/health/devices", headers=auth_headers)
    assert res.status_code == 200
    devices = res.get_json()
    assert len(devices) == 1
    entry = devices[0]
    assert entry["device_id"] == d.id
    assert entry["name"] == "Router Principal"
    assert entry["health_status"] in {"verde", "amarillo", "rojo"}
