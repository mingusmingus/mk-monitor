# Backend mk-monitor

Base Flask + SQLAlchemy para plataforma SaaS multi-tenant de monitoreo MikroTik.

## Levantar en local (venv)

- Windows:
  - python -m venv .venv
  - .venv\Scripts\activate
- Unix/Mac:
  - python -m venv .venv
  - source .venv/bin/activate

Instalar dependencias:
- pip install -r requirements.txt

Variables de entorno mínimas (ver [app/config.py](mk-monitor/backend/app/config.py)):
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS (o DATABASE_URL completo)
- JWT_SECRET, JWT_EXPIRES_MINUTES
- ENCRYPTION_KEY
- APP_ENV=dev
- CORS_ORIGINS=*

Ejecutar:
- python wsgi.py
- API por defecto: http://localhost:5000/api

## Alembic (migraciones)

Aún no hay migraciones reales. Guía mínima:
- alembic init migrations
- Configurar sqlalchemy.url a DATABASE_URL
- alembic revision -m "init"
- alembic upgrade head

En producción usar Alembic con pipeline CI/CD.

## Notas de seguridad

- Hash de contraseñas con bcrypt:
  - [`auth/password.py`](mk-monitor/backend/app/auth/password.py)
- JWT con expiración:
  - [`auth/jwt_utils.create_jwt`](mk-monitor/backend/app/auth/jwt_utils.py), [`auth/jwt_utils.decode_jwt`](mk-monitor/backend/app/auth/jwt_utils.py)
- Cifrado de credenciales de MikroTik (en reposo) con Fernet derivado de ENCRYPTION_KEY:
  - [`device_service.encrypt_secret`](mk-monitor/backend/app/services/device_service.py), [`device_service.decrypt_secret`](mk-monitor/backend/app/services/device_service.py)
- Rate limit rudimentario en login (bloqueo temporal por IP+email):
  - [`auth_routes.login`](mk-monitor/backend/app/routes/auth_routes.py) y helpers `_is_locked`, `_register_failed`
- Validación de tenant en cada request:
  - Decorador [`auth.decorators.require_auth`](mk-monitor/backend/app/auth/decorators.py) fija `g.tenant_id`
  - Endpoints filtran por `tenant_id` (ej. [`alert_routes.list_alerts`](mk-monitor/backend/app/routes/alert_routes.py), [`device_routes.list_devices`](mk-monitor/backend/app/routes/device_routes.py), [`log_routes.device_logs`](mk-monitor/backend/app/routes/log_routes.py))