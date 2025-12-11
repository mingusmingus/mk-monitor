import os
import time
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.__init__ import create_app
from app.db import db
from app.models.tenant import Tenant
from app.models.user import User
from app.auth.password import hash_password
from app.auth.jwt_utils import create_jwt, decode_jwt


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    os.environ.setdefault("APP_ENV", "test")
    # These might be ignored if Config is already imported, so we set them in app.config below too
    os.environ.setdefault("JWT_SECRET", "auth-flow-secret")
    os.environ.setdefault("REDIS_URL", "memory://")
    encryption_key = Fernet.generate_key().decode()
    os.environ.setdefault("ENCRYPTION_KEY", encryption_key)

    db_path = tmp_path_factory.mktemp("authflow") / "authflow.sqlite"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    application = create_app()
    # Explicitly set config to ensure it is present regardless of import order
    application.config["JWT_SECRET_KEY"] = "auth-flow-secret"
    application.config["ENCRYPTION_KEY"] = encryption_key
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_credentials(app):
    with app.app_context():
        tenant = Tenant(
            name=f"tenant_{uuid4().hex[:6]}",
            plan="BASICMAAT",
            status_pago="activo",
        )
        db.session.add(tenant)
        db.session.flush()

        email = f"admin_{uuid4().hex[:6]}@example.com"
        password = "secret123"
        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            full_name="Auth Flow Admin",
        )
        db.session.add(user)
        db.session.commit()

        yield {
            "email": email,
            "password": password,
            "user_id": user.id,
            "tenant_id": tenant.id,
            "role": user.role,
        }

        db.session.query(User).filter_by(id=user.id).delete()
        db.session.query(Tenant).filter_by(id=tenant.id).delete()
        db.session.commit()


def test_login_token_sub_is_string(client, admin_credentials):
    res = client.post("/api/auth/login", json={
        "email": admin_credentials["email"],
        "password": admin_credentials["password"],
    })
    assert res.status_code == 200, res.get_data(as_text=True)
    token = res.get_json()["token"]
    claims = decode_jwt(token)
    assert isinstance(claims["sub"], str)
    assert claims["sub"] == str(admin_credentials["user_id"])


def test_protected_endpoint_with_valid_token(client, admin_credentials):
    res = client.post("/api/auth/login", json={
        "email": admin_credentials["email"],
        "password": admin_credentials["password"],
    })
    assert res.status_code == 200
    token = res.get_json()["token"]
    protected = client.get(
        "/api/health/devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected.status_code == 200
    assert protected.get_json() == []


def test_protected_endpoint_with_expired_token(client, app, admin_credentials):
    with app.app_context():
        token = create_jwt(
            admin_credentials["user_id"],
            admin_credentials["tenant_id"],
            admin_credentials["role"],
            expires_minutes=0,
        )
    time.sleep(2)
    res = client.get(
        "/api/health/devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
    payload = res.get_json()
    assert payload["reason"] == "expired"
    assert "Token expirado" in payload["message"]
