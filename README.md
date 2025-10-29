# mk-monitor

Plataforma SaaS multi-tenant para monitoreo y análisis inteligente de routers MikroTik.

Objetivo:
- Multi-cliente con aislamiento por tenant_id.
- Control de suscripción/pagos y límites por plan (BASICMAAT, INTERMAAT, PROMAAT).
- Backend Flask con PostgreSQL (SQLAlchemy/Alembic), JWT y cifrado en reposo.
- Frontend React (Vite) con dashboard de alertas, salud por equipo y gestión.
- Servicio interno de IA para analizar logs y generar alertas con acciones recomendadas.