"""
Inicialización de la aplicación Flask (App Factory).

- Carga configuración desde config.py (variables de entorno).
- Inicializa CORS, DB y registro de Blueprints (rutas) de forma desacoplada.
- Punto de entrada para WSGI (ver wsgi.py) y para tests.
"""
from flask import Flask
from flask_cors import CORS
from .config import Config
from .db import init_db

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS: permitir frontend (por ahora orígenes *)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}}, supports_credentials=False)

    # Inicializar DB
    init_db(app)

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

    return app