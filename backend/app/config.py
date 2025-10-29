"""
Configuración central del backend.

- Lee variables desde el entorno (.env en desarrollo con python-dotenv).
- Define parámetros de conexión a PostgreSQL, JWT y cifrado simétrico.
- Ajustes de seguridad y multi-tenant.
"""
import os
from datetime import timedelta

class Config:
    # Entorno
    APP_ENV = os.getenv("APP_ENV", "dev")

    # Base de datos (compatibles con docker-compose de infra)
    DB_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "mkmonitor"))
    DB_USER = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "mkmonitor"))
    DB_PASS = os.getenv("DB_PASS", os.getenv("POSTGRES_PASSWORD", "mkmonitor"))

    # Si viene DATABASE_URL, úsala; si no, construimos la URI
    _fallback_uri = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _fallback_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT y expiración
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "changeme-insecure")
    TOKEN_EXP_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", os.getenv("TOKEN_EXP_MINUTES", "60")))

    # Cifrado simétrico para credenciales de routers (usar Fernet)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "32bytes_key_base64_o_hex_dummy")

    # Otros
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    DEBUG = os.getenv("DEBUG", "1") == "1"