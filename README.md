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

## Migraciones de Base de Datos

Sistema gestionado con **Alembic** para cambios versionados del esquema.

**Guía rápida** (Windows PowerShell):
```powershell
# Ver estado actual
.\migration-status.ps1

# Crear migración tras modificar modelos
.\new-migration.ps1 "descripción del cambio"

# Aplicar migraciones pendientes
.\migrate.ps1
```

📖 **Documentación completa**: Ver [MIGRATIONS.md](MIGRATIONS.md)  
📂 **Archivos de migración**: `backend/migrations/versions/`  
⚙️ **Configuración**: `backend/alembic.ini`

## Arranque rápido hoy

Ponlo a correr en minutos con Docker Compose.

### Requisitos

- Docker Desktop (o Docker Engine) instalado y corriendo
- Docker Compose v2 (comando `docker compose`)
- Opcional: variable `DEEPSEEK_API_KEY` para análisis con IA (si no la defines, el sistema cae en heurísticas locales)

### Arranque rápido (UI renovada)

1.  **Configura el entorno**:
    Copia el archivo de ejemplo y ajusta si es necesario (por defecto funciona en local).
    ```bash
    cp infra/.env.example infra/.env
    ```
    *Opcional*: Si quieres probar el registro público, asegúrate de que tu frontend permita el registro (por defecto habilitado en dev).

2.  **Levanta la infraestructura**:
    Desde la raíz del proyecto:
    ```bash
    docker compose -f infra/docker-compose.yml up -d --build
    ```

3.  **Accede a la plataforma**:
    - **Frontend**: Abre [http://localhost:8080](http://localhost:8080) (o el puerto configurado en docker-compose).
    - **Backend API**: [http://localhost:5000/api/health](http://localhost:5000/api/health).

4.  **Flujo de prueba**:
    1.  Ve a `/signup` (o usa el link "Regístrate" en el login) y crea un usuario para tu tenant.
    2.  Inicia sesión con tus nuevas credenciales.
    3.  Verás el **Dashboard** vacío.
    4.  Ve a **Equipos** y usa el botón **"+ Agregar"** (ahora con validación visual) para añadir un router (IP dummy si no tienes uno real).
    5.  El sistema empezará a generar logs simulados (si está en modo demo) o reales, y verás las alertas en el Dashboard.

### Pasos (Legacy / Manual)

 a. Copia variables de ejemplo y ajústalas

    ```powershell
    cp infra/.env.example infra/.env
    # Edita infra/.env y ajusta claves/secretos mínimos (JWT_SECRET, ENCRYPTION_KEY, credenciales Postgres, etc.)
    ```

 b. Levanta toda la pila con build fresco

    ```powershell
    docker compose -f infra/docker-compose.yml up -d --build
    ```

 c. Verifica el backend (salud)

    - http://localhost:5000/api/health debería responder `{ "status": "ok" }`.

 d. Verifica el frontend

    - Si usas los contenedores (Nginx): http://localhost:8080
    - Si corres el frontend en modo dev (Vite): http://localhost:5173

 e. Añade un dispositivo real y observa los logs/alertas

    - Crea el dispositivo desde la UI y espera a que el servicio de monitoreo ingiera logs; verás alertas y estado de salud.

### Nota sobre IA (fallback)

- Si no configuras `DEEPSEEK_API_KEY`, el proveedor `auto` usa heurísticas locales como fallback para generar alertas básicas a partir de los logs (sin llamadas a LLM). Cuando añadas la clave, el análisis se enriquecerá automáticamente.