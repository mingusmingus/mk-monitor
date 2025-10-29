# Backend mk-monitor

Base Flask + SQLAlchemy para plataforma SaaS multi-tenant de monitoreo MikroTik.

- Autenticación JWT con expiración.
- Aislamiento por tenant_id.
- Cifrado simétrico de credenciales de routers en reposo.
- Migraciones con Alembic (TODO).
- Servicios desacoplados (monitoreo, alertas, suscripciones, IA).

## Requisitos
- Python 3.10+
- PostgreSQL accesible (ver variables en infra/.env.example)
- Variables de entorno (.env opcional) compatibles con `app/config.py`

## Instalación local
1. Crear y activar virtualenv:
   - Windows:
     - `python -m venv .venv`
     - `.venv\Scripts\activate`
   - Unix/Mac:
     - `python -m venv .venv`
     - `source .venv/bin/activate`

2. Instalar dependencias:
   - `pip install -r requirements.txt`

3. Exportar variables de entorno (o usar archivo `.env` con docker-compose):
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` (o `DATABASE_URL`)
   - `JWT_SECRET`, `JWT_EXPIRES_MINUTES`
   - `ENCRYPTION_KEY`

4. Ejecutar la app:
   - `python wsgi.py`
   - Por defecto en `http://localhost:5000`

5. Migraciones (pendiente):
   - TODO: configurar Alembic y crear versiones iniciales.

Notas:
- El servidor registra Blueprints bajo `/api/*`.
- Modelos listos para multi-tenant (todas las tablas relevantes incluyen `tenant_id`).