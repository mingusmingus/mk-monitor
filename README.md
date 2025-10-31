# mk-monitor

Plataforma SaaS multi-tenant para monitoreo y análisis inteligente de routers MikroTik con IA.

- Aislamiento por tenant_id en todas las consultas.
- Backend Flask + SQLAlchemy con JWT y cifrado en reposo.
- Frontend React (Vite) con dashboard, alertas y flujo NOC.

## Arquitectura (diagrama textual)

Frontend (React/Vite)
  └── solicitudes HTTP a /api/*
      └── Backend Flask (Blueprints: auth, devices, alerts, logs, noc, subscriptions, health, sla)
          └── PostgreSQL (SQLAlchemy)

Resumen:
- Frontend consume la API vía Axios [frontend/src/api/client.js](mk-monitor/frontend/src/api/client.js).
- Backend expone Blueprints bajo /api: ver [backend/app/__init__.py](mk-monitor/backend/app/__init__.py).
- Persistencia en Postgres: modelos en [backend/app/models](mk-monitor/backend/app/models).

## Flujo principal de valor

1) Cliente inicia sesión.
   - Endpoint: [`auth_routes.login`](mk-monitor/backend/app/routes/auth_routes.py) emite JWT con expiración usando [`jwt_utils.create_jwt`](mk-monitor/backend/app/auth/jwt_utils.py).

2) Ve estado de sus equipos y alertas.
   - Equipos: [`device_routes.list_devices`](mk-monitor/backend/app/routes/device_routes.py) calcula salud usando [`alert_service.compute_device_health`](mk-monitor/backend/app/services/alert_service.py).
   - Alertas: [`alert_routes.list_alerts`](mk-monitor/backend/app/routes/alert_routes.py).

3) NOC gestiona incidentes y resuelve tickets.
   - Cambios de estado: [`noc_routes.update_alert_status`](mk-monitor/backend/app/routes/noc_routes.py) persiste histórico [`AlertStatusHistory`](mk-monitor/backend/app/models/alert_status_history.py) vía [`alert_service.update_alert_status`](mk-monitor/backend/app/services/alert_service.py).

4) El sistema mide SLA.
   - Cálculo de métricas: [`sla_service.get_sla_metrics`](mk-monitor/backend/app/services/sla_service.py).

## Análisis con IA

El backend genera alertas a partir de logs con un servicio de IA (placeholder) en [`ai_analysis_service.analyze_logs`](mk-monitor/backend/app/services/ai_analysis_service.py). El pipeline de monitoreo está en [`monitoring_service.analyze_and_generate_alerts`](mk-monitor/backend/app/services/monitoring_service.py).

## Enforcement del plan (límite de equipos + upsell)

- El plan efectivo y límites se resuelven en [`subscription_service.get_current_subscription`](mk-monitor/backend/app/services/subscription_service.py).
- Validación al crear equipos: [`device_service.create_device`](mk-monitor/backend/app/services/device_service.py) llama a [`subscription_service.can_add_device`](mk-monitor/backend/app/services/subscription_service.py) y puede lanzar `DeviceLimitReached` (upsell). Expuesto por [`device_routes.create_device`](mk-monitor/backend/app/routes/device_routes.py) con HTTP 402.

## Aislamiento por tenant

- Todos los endpoints protegen con [`auth.decorators.require_auth`](mk-monitor/backend/app/auth/decorators.py), adjuntando `g.tenant_id`.
- Las consultas filtran por `tenant_id` (ej.: [`alert_routes.list_alerts`](mk-monitor/backend/app/routes/alert_routes.py), [`device_routes.list_devices`](mk-monitor/backend/app/routes/device_routes.py), [`log_routes.device_logs`](mk-monitor/backend/app/routes/log_routes.py)).
- Modelos multi-tenant en [backend/app/models](mk-monitor/backend/app/models).