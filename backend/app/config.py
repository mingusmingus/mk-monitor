"""
Configuración central del backend.

- Lee variables desde el entorno (.env en desarrollo con python-dotenv).
- Define parámetros de conexión a PostgreSQL, JWT y cifrado simétrico.
- Ajustes de seguridad y multi-tenant.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "mkmonitor")
    DB_USER = os.getenv("DB_USER", "mkmonitor")
    DB_PASS = os.getenv("DB_PASS", "mkmonitor")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "changeme-insecure")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=JWT_EXPIRES_MINUTES)

    # Cifrado de credenciales en reposo
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "32bytes_key_base64_o_hex_dummy")

    # Seguridad app
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "flask-secret-dev")
    ENV = os.getenv("FLASK_ENV", "development")

    # Multi-tenant
    # Todas las tablas deberán incluir tenant_id para aislamiento por cliente
    TENANT_ISOLATION = True

    # Otros
    DEBUG = os.getenv("DEBUG", "1") == "1"