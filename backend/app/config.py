"""
Configuración central del backend.

- Lee variables desde el entorno (.env en desarrollo con python-dotenv).
- Define parámetros de conexión a PostgreSQL, JWT y cifrado simétrico.
- Ajustes de seguridad y multi-tenant.
"""
import os
from datetime import timedelta
import base64
from pathlib import Path

# Carga opcional de variables desde .env en desarrollo (no obligatorio en producción)
try:
    from dotenv import load_dotenv
    # Buscar el archivo .env en la carpeta infra
    backend_dir = Path(__file__).resolve().parent.parent  # directorio backend/
    project_root = backend_dir.parent  # directorio raíz del proyecto
    env_file = project_root / "infra" / ".env"
    
    if env_file.exists():
        load_dotenv(env_file, encoding='utf-8')
    else:
        load_dotenv()  # Intentar cargar desde la ubicación por defecto
except Exception as e:
    import warnings
    warnings.warn(f"No se pudo cargar el archivo .env: {e}", RuntimeWarning)

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
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # sin default inseguro

    # Otros
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    DEBUG = os.getenv("DEBUG", "1") == "1"

    # AI / DeepSeek (no incluir claves en código; leer del entorno)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Sin default inseguro
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    AI_ANALYSIS_PROVIDER = os.getenv("AI_ANALYSIS_PROVIDER", "auto")  # heuristic | deepseek | auto
    AI_TIMEOUT_SEC = int(os.getenv("AI_TIMEOUT_SEC", "20"))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "800"))

    # Conexión MikroTik (nuevas configuraciones)
    ROS_PROVIDER = os.getenv("ROS_PROVIDER", "auto")  # librouteros | routeros_api | ssh | auto
    ROS_API_PORT = int(os.getenv("ROS_API_PORT", "8728"))  # Puerto RouterOS API (8729 para SSL)
    ROS_SSH_PORT = int(os.getenv("ROS_SSH_PORT", "22"))
    ROS_CONNECT_TIMEOUT_SEC = int(os.getenv("ROS_CONNECT_TIMEOUT_SEC", "5"))
    ROS_COMMAND_TIMEOUT_SEC = int(os.getenv("ROS_COMMAND_TIMEOUT_SEC", "10"))
    ROS_BACKOFF_BASE_MS = int(os.getenv("ROS_BACKOFF_BASE_MS", "200"))
    ROS_MAX_RETRIES = int(os.getenv("ROS_MAX_RETRIES", "3"))
    ROS_USE_SSL = os.getenv("ROS_USE_SSL", "false").lower() == "true"  # SSL para RouterOS API

    # Monitoreo (renombrado para claridad)
    MONITORING_LOG_LIMIT = int(os.getenv("MONITORING_LOG_LIMIT", "200"))

    # Anti fuerza bruta
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    LOCKOUT_SECONDS = int(os.getenv("LOCKOUT_SECONDS", "300"))

    # Rate limiting (Redis)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATE_LIMITS_DEFAULT = os.getenv("RATE_LIMITS_DEFAULT", "100/minute; 1000/hour")

# Helpers de entorno/seguridad
DEV_ENVS = {"dev", "development"}

def is_dev() -> bool:
    """
    True si el entorno es desarrollo.
    """
    return str(Config.APP_ENV).lower() in DEV_ENVS

def validate_encryption_key(key: str) -> bool:
    """
    Valida que la clave sea base64 urlsafe y que decodifique a 32 bytes (requisito Fernet).
    No imprime ni filtra la clave.
    """
    if not key or not isinstance(key, str):
        return False
    try:
        raw = base64.urlsafe_b64decode(key.encode("utf-8"))
        return len(raw) == 32
    except Exception:
        return False

# Validación estricta de secretos en producción
if not is_dev():
    # JWT_SECRET_KEY no debe estar vacío ni ser placeholder
    if not Config.JWT_SECRET_KEY or str(Config.JWT_SECRET_KEY).lower().startswith("changeme"):
        raise RuntimeError("Config: JWT_SECRET_KEY inválido en producción (vacío o placeholder).")
    # ENCRYPTION_KEY debe ser una clave Fernet válida (base64 urlsafe, 32 bytes)
    if not validate_encryption_key(Config.ENCRYPTION_KEY):
        raise RuntimeError("Config: ENCRYPTION_KEY inválida; se requiere Fernet base64 urlsafe de 32 bytes.")
    # Advertencia si DEEPSEEK_API_KEY ausente y provider requiere DeepSeek
    if Config.AI_ANALYSIS_PROVIDER in ("deepseek", "auto") and not Config.DEEPSEEK_API_KEY:
        import warnings
        warnings.warn(
            "Config: AI_ANALYSIS_PROVIDER configurado para DeepSeek pero DEEPSEEK_API_KEY ausente. "
            "Fallback a heurísticas. Para análisis IA, configura DEEPSEEK_API_KEY en el entorno.",
            RuntimeWarning
        )