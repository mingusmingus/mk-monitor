"""
Módulo de Configuración Central.

Este módulo gestiona la carga y validación de variables de entorno para la configuración
del backend. Maneja conexiones a base de datos, seguridad (JWT, cifrado), integración
con IA y parámetros de conexión a dispositivos Mikrotik.

Soporta carga desde archivo .env para entornos de desarrollo.
"""
import os
import base64
from pathlib import Path

# Carga opcional de variables desde .env en la RAÍZ
try:
    from dotenv import load_dotenv

    # basedir = backend/app/config.py -> backend/app
    basedir = Path(__file__).resolve().parent
    # root = backend/app/../../.env -> .env (Raíz del proyecto)
    env_path = basedir.parent.parent / '.env'

    if env_path.exists():
        load_dotenv(env_path, encoding='utf-8')
    else:
        # Fallback a carga genérica
        load_dotenv()
except Exception as e:
    import warnings
    warnings.warn(f"No se pudo cargar el archivo .env desde {env_path}: {e}", RuntimeWarning)

class Config:
    """
    Clase que encapsula todas las variables de configuración del sistema.
    """
    # Entorno
    APP_ENV = os.getenv("APP_ENV", "dev")

    # Base de datos
    DB_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "mkmonitor"))
    DB_USER = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "mkmonitor"))
    DB_PASS = os.getenv("DB_PASS", os.getenv("POSTGRES_PASSWORD", "mkmonitor"))

    _fallback_uri = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _fallback_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Seguridad: JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    TOKEN_EXP_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", os.getenv("TOKEN_EXP_MINUTES", "60")))
 
    # Seguridad: Cifrado Simétrico (Fernet)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    DEBUG = os.getenv("DEBUG", "1") == "1"

    # Integración IA
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    AI_ANALYSIS_PROVIDER = os.getenv("AI_ANALYSIS_PROVIDER", "auto")
    AI_PROVIDER = os.getenv("AI_PROVIDER", AI_ANALYSIS_PROVIDER) # Unified provider config
    AI_TIMEOUT_SEC = int(os.getenv("AI_TIMEOUT_SEC", "20"))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "800"))

    # Conexión Mikrotik
    ROS_PROVIDER = os.getenv("ROS_PROVIDER", "auto")
    ROS_API_PORT = int(os.getenv("ROS_API_PORT", "8728"))
    ROS_SSH_PORT = int(os.getenv("ROS_SSH_PORT", "22"))
    ROS_CONNECT_TIMEOUT_SEC = int(os.getenv("ROS_CONNECT_TIMEOUT_SEC", "5"))
    ROS_COMMAND_TIMEOUT_SEC = int(os.getenv("ROS_COMMAND_TIMEOUT_SEC", "10"))
    ROS_BACKOFF_BASE_MS = int(os.getenv("ROS_BACKOFF_BASE_MS", "200"))
    ROS_MAX_RETRIES = int(os.getenv("ROS_MAX_RETRIES", "3"))
    ROS_USE_SSL = os.getenv("ROS_USE_SSL", "false").lower() == "true"

    # Monitoreo
    MONITORING_LOG_LIMIT = int(os.getenv("MONITORING_LOG_LIMIT", "200"))

    # Seguridad: Anti Fuerza Bruta
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    LOCKOUT_SECONDS = int(os.getenv("LOCKOUT_SECONDS", "300"))

    # Rate Limiting (Redis)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _raw_rate_limits = os.getenv("RATE_LIMITS_DEFAULT", "100/minute,1000/hour")
    RATE_LIMITS_DEFAULT = [
        entry.strip()
        for entry in _raw_rate_limits.replace(";", ",").split(",")
        if entry.strip()
    ]

# Helpers
DEV_ENVS = {"dev", "development"}

def is_dev() -> bool:
    """
    Verifica si la aplicación se está ejecutando en entorno de desarrollo.

    Returns:
        bool: True si el entorno es de desarrollo, False en caso contrario.
    """
    return str(Config.APP_ENV).lower() in DEV_ENVS

def validate_encryption_key(key: str) -> bool:
    """
    Valida que la clave de cifrado cumpla con los requisitos de Fernet.

    Args:
        key (str): La clave de cifrado a validar.

    Returns:
        bool: True si la clave es válida (base64 urlsafe, 32 bytes decodificados), False si no.
    """
    if not key or not isinstance(key, str):
        return False
    try:
        raw = base64.urlsafe_b64decode(key.encode("utf-8"))
        return len(raw) == 32
    except Exception:
        return False

# Validación de configuración crítica
if not is_dev():
    if not Config.JWT_SECRET_KEY:
        raise RuntimeError("[ERROR] Config: JWT_SECRET_KEY inválido en producción (vacío).")
    if str(Config.JWT_SECRET_KEY).lower().startswith("changeme"):
         raise RuntimeError("[ERROR] Config: JWT_SECRET_KEY inválido en producción (placeholder detectado).")
    if not validate_encryption_key(Config.ENCRYPTION_KEY):
        raise RuntimeError("[ERROR] Config: ENCRYPTION_KEY inválida; se requiere Fernet base64 urlsafe de 32 bytes.")
    if Config.AI_ANALYSIS_PROVIDER in ("deepseek", "auto") and not Config.DEEPSEEK_API_KEY:
        import warnings
        warnings.warn(
            "[WARNING] Config: AI_ANALYSIS_PROVIDER configurado para DeepSeek pero DEEPSEEK_API_KEY ausente. Fallback a heurísticas.",
            RuntimeWarning
        )
    if getattr(Config, 'AI_PROVIDER', None) == "gemini" and not Config.GEMINI_API_KEY:
         raise RuntimeError("[ERROR] AI_PROVIDER configured to 'gemini' but GEMINI_API_KEY is missing.")
