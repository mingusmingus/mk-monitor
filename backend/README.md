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

## Rate limiting y Redis (producción)

El contador de intentos fallidos de login actual es en memoria (por IP+email) dentro de [`auth_routes.login`](mk-monitor/backend/app/routes/auth_routes.py) usando helpers locales. En producción, debe migrarse a un backend centralizado (Redis) para:
- Compartir estado entre réplicas del backend.
- Evitar pérdida del contador al reiniciar procesos.
- Permitir ventanas deslizantes y bloqueos temporales configurables.

TODO:
- Proveer `REDIS_URL` vía entorno.
- Implementar un cliente Redis y reemplazar el almacenamiento en `FAILED_LOGINS` por estructuras en Redis (p. ej. claves con TTL).
- Añadir configuración de límites por ruta y por IP en un middleware.

## Integración IA (DeepSeek)

### Configuración

El backend soporta análisis de logs con DeepSeek (LLM) o heurísticas locales según configuración:

**Variables de entorno** (configurar en `infra/.env`):
```env
DEEPSEEK_API_KEY=sk-xxxxx               # API key de DeepSeek (obligatoria si usas DeepSeek)
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
AI_ANALYSIS_PROVIDER=auto               # heuristic | deepseek | auto
AI_TIMEOUT_SEC=20
AI_MAX_TOKENS=800
```

**Modos de operación** (`AI_ANALYSIS_PROVIDER`):
- `heuristic`: Solo heurísticas locales (sin llamadas a LLM)
- `deepseek`: Fuerza uso de DeepSeek; falla si API key ausente o request falla
- `auto` (recomendado): Intenta DeepSeek si hay API key; fallback a heurísticas si falla o key ausente

### Flujo de análisis

1. **Ingesta**: [`monitoring_service.get_router_logs`](mk-monitor/backend/app/services/monitoring_service.py) obtiene logs del router MikroTik (RouterOS API o SSH)
2. **Persistencia**: Logs se almacenan en [`LogEntry`](mk-monitor/backend/app/models/log_entry.py)
3. **Análisis**: [`ai_analysis_service.analyze_logs`](mk-monitor/backend/app/services/ai_analysis_service.py) procesa logs con:
   - **DeepSeek**: Envía logs al LLM con prompt estructurado, recibe alertas en JSON
   - **Heurísticas**: Detecta patrones conocidos ("login failed", "pppoe reconnect")
4. **Generación de alertas**: [`monitoring_service.analyze_and_generate_alerts`](mk-monitor/backend/app/services/monitoring_service.py) crea [`Alert`](mk-monitor/backend/app/models/alert.py) con deduplicación

### Taxonomía de estados

Todas las alertas usan 4 niveles canónicos:
- **Aviso**: Información sin impacto operativo inmediato
- **Alerta Menor**: Problema leve, atención en plazo medio
- **Alerta Severa**: Problema grave, atención urgente
- **Alerta Crítica**: Fallo crítico, atención inmediata

El servicio normaliza automáticamente variantes de DeepSeek a estos valores.

### Seguridad

- **API key**: Nunca commitear `DEEPSEEK_API_KEY` al repo. Usar solo `infra/.env` (gitignored).
- **docker-compose**: La key se inyecta vía `env_file: ./infra/.env` en el servicio backend.
- **Logs**: El sistema NO loguea la API key ni logs crudos sensibles.

### TODOs

- [ ] Backoff/retry automático si DeepSeek devuelve 429 (rate limit)
- [ ] Chunking inteligente de logs largos para respetar límite de tokens
- [ ] Deduplicación avanzada y correlación de alertas entre dispositivos
- [ ] Caché de respuestas para logs idénticos (Redis)