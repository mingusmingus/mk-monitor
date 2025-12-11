"""
Módulo de inicialización de la aplicación Flask (App Factory).

Este módulo es responsable de crear y configurar la instancia de la aplicación Flask.
Sus responsabilidades incluyen:
- Cargar la configuración desde variables de entorno.
- Inicializar extensiones (CORS, Base de Datos, Rate Limiting).
- Registrar los Blueprints (rutas) de la API.
- Configurar manejadores de errores globales.
"""
from flask import Flask, g, jsonify
from flask_cors import CORS
from .config import Config
from .db import init_db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import logging
import os


def _rate_limit_key():
    """
    Genera una clave única para identificar al cliente en el sistema de Rate Limiting.
    Prioriza el ID del tenant si está disponible, de lo contrario usa la dirección IP.

    Returns:
        str: Clave de identificación para el rate limiter.
    """
    tid = getattr(g, "tenant_id", None)
    return f"tenant:{tid}" if tid else get_remote_address()


# Configuración del almacenamiento para Rate Limiting
# Se prioriza Redis en producción, memoria en desarrollo/test
_APP_ENV = (os.getenv("APP_ENV") or "dev").lower()
_REDIS_URL = (os.getenv("REDIS_URL") or "").strip()
_USE_MEMORY = _APP_ENV in {"dev", "development", "test"} or not _REDIS_URL
_STORAGE_URI = "memory://" if _USE_MEMORY else _REDIS_URL

if _USE_MEMORY:
    logging.warning(
        "[WARNING] RateLimiter: usando almacenamiento en memoria (APP_ENV=%s, REDIS_URL=%s).",
        _APP_ENV,
        _REDIS_URL or "<vacío>",
    )

# Instancia global del Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_STORAGE_URI,
    default_limits=[],
    headers_enabled=True,
)


def create_app() -> Flask:
    """
    Función factoría que crea y configura la instancia de la aplicación Flask.

    Returns:
        Flask: Instancia de la aplicación configurada.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuración CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}}, supports_credentials=False)

    # Importación de modelos para asegurar registro en SQLAlchemy
    from .models import (  # noqa: F401
        tenant,
        user,
        device,
        subscription,
        alert,
        log_entry,
        alert_status_history,
    )

    # Inicialización de la base de datos
    init_db(app)

    # Inicialización del Rate Limiter
    limiter.init_app(app)

    # Manejador de errores para Rate Limit excedido
    @app.errorhandler(RateLimitExceeded)
    def _handle_ratelimit(e: RateLimitExceeded):
        key = _rate_limit_key()
        logging.warning(f"[WARNING] rate_limit_exceeded key={key} limit={e.limit}")
        return jsonify({
            "error": "rate_limit_exceeded",
            "message": "Demasiadas solicitudes. Intente nuevamente más tarde.",
            "limit": str(e.limit),
        }), 429

    # Registro de Blueprints
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

    # Exenciones de Rate Limit
    limiter.exempt(sla_bp)
    if app.view_functions.get("static"):
        limiter.exempt(app.view_functions["static"])

    return app
