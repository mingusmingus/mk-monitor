# Backend mk-monitor

Base Flask + SQLAlchemy para plataforma SaaS multi-tenant de monitoreo MikroTik.

- Autenticación JWT con expiración.
- Aislamiento por tenant_id.
- Cifrado simétrico de credenciales de routers en reposo.
- Migraciones con Alembic (pendiente).
- Servicios desacoplados (monitoreo, alertas, suscripciones, IA).