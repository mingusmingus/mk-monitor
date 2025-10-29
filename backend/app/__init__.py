"""
Inicialización de la aplicación Flask (App Factory).

- Carga configuración desde config.py (variables de entorno).
- Inicializa CORS, DB y registro de Blueprints (rutas) de forma desacoplada.
- Punto de entrada para WSGI (ver wsgi.py) y para tests.
"""
from flask import Flask
from flask_cors import CORS
from .config import Config

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Habilitar CORS (ajustar orígenes en producción)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Inicializar DB/configuración (placeholder)
    # from .db import init_db
    # init_db(app)

    # Registro de Blueprints (rutas) – sin endpoints aún
    # from .routes.auth_routes import auth_bp
    # from .routes.device_routes import device_bp
    # from .routes.alert_routes import alert_bp
    # from .routes.log_routes import log_bp
    # from .routes.noc_routes import noc_bp
    # from .routes.subscription_routes import subscription_bp
    # from .routes.health_routes import health_bp
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(device_bp)
    # app.register_blueprint(alert_bp)
    # app.register_blueprint(log_bp)
    # app.register_blueprint(noc_bp)
    # app.register_blueprint(subscription_bp)
    # app.register_blueprint(health_bp)

    return app