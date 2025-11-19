"""
Inicialización de la aplicación Flask (App Factory).

- Carga configuración desde config.py (variables de entorno).
- Inicializa CORS, DB y registro de Blueprints (rutas) de forma desacoplada.
- Punto de entrada para WSGI (ver wsgi.py) y para tests.
"""
from flask import Flask, g, jsonify
from flask_cors import CORS
from .config import Config
from .db import init_db
# Rate limiting (Flask-Limiter + Redis)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import logging

def _rate_limit_key():
    """
    Clave de rate limit:
    - Si hay autenticación, usar tenant:<tenant_id>
    - Si no, usar IP remota.
    """
    tid = getattr(g, "tenant_id", None)
    return f"tenant:{tid}" if tid else get_remote_address()

# Instancia global para usar en decoradores de rutas
limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=Config.REDIS_URL,
    default_limits=Config.RATE_LIMITS_DEFAULT,
    headers_enabled=True,
)

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS: permitir frontend (por ahora orígenes *)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}}, supports_credentials=False)

    # IMPORTANTE: importar modelos ANTES de crear tablas en dev.
    # Esto asegura que db.create_all() conozca todas las entidades.
    # (En producción se usa Alembic y no depende de esto.)
    from .models import (  # noqa: F401
        tenant,
        user,
        device,
        subscription,
        alert,
        log_entry,
        alert_status_history,
    )

    # Inicializar DB (en dev puede crear tablas si no existen)
    init_db(app)

    # Inicializar limiter sobre la app
    limiter.init_app(app)

    # Respuesta JSON y logging cuando se excede el límite
    @app.errorhandler(RateLimitExceeded)
    def _handle_ratelimit(e: RateLimitExceeded):
        key = _rate_limit_key()
        logging.warning(f"rate_limit_exceeded key={key} limit={e.limit}")
        return jsonify({
            "error": "rate_limit_exceeded",
            "message": "Demasiadas solicitudes. Intenta nuevamente más tarde.",
            "limit": str(e.limit),
        }), 429

    # Registro de Blueprints (todas bajo /api)
    from .routes.auth_routes import auth_bp
    from .routes.device_routes import device_bp
    from .routes.alert_routes import alert_bp
    from .routes.log_routes import log_bp
    from .routes.noc_routes import noc_bp
    from .routes.subscription_routes import sub_bp
    from .routes.health_routes import health_bp
    from .routes.sla_routes import sla_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(device_bp, url_prefix="/api")
    app.register_blueprint(alert_bp, url_prefix="/api")
    app.register_blueprint(log_bp, url_prefix="/api")
    app.register_blueprint(noc_bp, url_prefix="/api")
    app.register_blueprint(sub_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(sla_bp, url_prefix="/api")

    # Excluir rutas de métricas y estáticos del rate limit
    # (ajusta si tienes /metrics real; aquí exime todo el blueprint SLA por ejemplo)
    limiter.exempt(sla_bp)
    if app.view_functions.get("static"):
        limiter.exempt(app.view_functions["static"])

    return app