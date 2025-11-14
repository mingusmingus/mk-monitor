"""
Servicio de monitoreo:

- Conecta a routers MikroTik (RouterOS API/SSH) para obtener logs.
- Persiste LogEntry y dispara análisis por IA.
- Respeta límites de plan (número de equipos por tenant).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import time
import socket

from ..models.device import Device
from ..models.log_entry import LogEntry
from ..models.alert import Alert
from ..db import db
from ..config import Config
from .ai_analysis_service import analyze_logs
from .device_service import decrypt_secret


# ============================================================================
# Helpers de Conexión RouterOS
# ============================================================================

def _connect_librouteros(ip: str, username: str, password: str, port: int, timeout: int, use_ssl: bool = False) -> tuple:
    """
    Conecta usando librouteros (recomendado).
    
    Returns:
        (api_connection, error_message)
        Si exitoso: (api, None)
        Si falla: (None, "error description")
    """
    try:
        import librouteros
    except ImportError:
        return None, "librouteros no instalado"
    
    try:
        # librouteros.connect acepta timeout y ssl
        api = librouteros.connect(
            host=ip,
            username=username,
            password=password,
            port=port,
            timeout=timeout,
            ssl_wrapper=use_ssl
        )
        return api, None
    except socket.timeout:
        return None, f"Timeout conectando a {ip}:{port}"
    except librouteros.exceptions.TrapError as e:
        return None, f"Auth failed: {str(e)}"
    except Exception as e:
        return None, f"librouteros error: {str(e)}"


def _connect_routeros_api(ip: str, username: str, password: str, port: int, timeout: int, use_ssl: bool = False) -> tuple:
    """
    Conecta usando routeros-api (legacy).
    
    Returns:
        (api_pool, error_message)
    """
    try:
        import routeros_api
    except ImportError:
        return None, "routeros-api no instalado"
    
    try:
        pool = routeros_api.RouterOsApiPool(
            ip,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            plaintext_login=True,
            socket_timeout=timeout
        )
        api = pool.get_api()
        return (pool, api), None
    except socket.timeout:
        return None, f"Timeout conectando a {ip}:{port}"
    except Exception as e:
        return None, f"routeros-api error: {str(e)}"


def _fetch_logs_via_ssh(ip: str, username: str, password: str, port: int, timeout: int, limit: int) -> tuple:
    """
    Conecta vía SSH usando paramiko y ejecuta /log/print.
    
    Returns:
        (log_lines, error_message)
    """
    try:
        import paramiko
    except ImportError:
        return None, "paramiko no instalado"
    
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            ip, 
            port=port,
            username=username, 
            password=password,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout
        )
        
        # Ejecutar comando RouterOS CLI
        cmd = "/log/print without-paging"
        _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        
        lines = stdout.read().decode(errors="ignore").splitlines()
        # Limitar desde el final (más recientes)
        lines = lines[-limit:] if len(lines) > limit else lines
        
        return lines, None
    except socket.timeout:
        return None, f"SSH timeout a {ip}:{port}"
    except paramiko.AuthenticationException:
        return None, f"SSH auth failed para {username}@{ip}"
    except Exception as e:
        return None, f"SSH error: {str(e)}"
    finally:
        if ssh:
            try:
                ssh.close()
            except:
                pass


def _normalize_log_rows(raw_entries: List[Any], device_id: int, tenant_id: int) -> List[Dict[str, Any]]:
    """
    Normaliza respuestas de RouterOS API o SSH a formato estándar.
    
    Args:
        raw_entries: Lista de dicts (API) o strings (SSH)
        device_id: ID del dispositivo
        tenant_id: ID del tenant
    
    Returns:
        Lista de dicts normalizados:
        {
            "raw_log": str,
            "timestamp_equipo": datetime | None,
            "log_level": str | None,
            "device_id": int,
            "tenant_id": int
        }
    """
    normalized = []
    
    for entry in raw_entries:
        if isinstance(entry, dict):
            # Respuesta de RouterOS API (librouteros o routeros-api)
            msg = entry.get("message") or entry.get("msg") or str(entry)
            topics = entry.get("topics") or entry.get("topic") or ""
            time_raw = entry.get("time") or entry.get("timestamp")
            
            # TODO: Parsear time_raw que viene en formato RouterOS (ej: "jan/02 12:34:56")
            # Por ahora, usamos None y dejamos que created_at capture el momento de ingesta
            timestamp_equipo = None
            
            # Extraer nivel de log si viene en topics
            log_level = None
            if topics:
                topics_lower = str(topics).lower()
                if "error" in topics_lower:
                    log_level = "error"
                elif "warning" in topics_lower:
                    log_level = "warning"
                elif "info" in topics_lower:
                    log_level = "info"
                elif "debug" in topics_lower:
                    log_level = "debug"
            
            raw_log = f"[{topics}] {msg}" if topics else msg
            
        elif isinstance(entry, str):
            # Respuesta de SSH (texto plano)
            raw_log = entry.strip()
            timestamp_equipo = None
            log_level = None
            
            # TODO: Intentar parsear timestamp del prefijo del log
            # Ejemplo: "jan/02 12:34:56 system,info router logged in"
            
        else:
            continue
        
        if not raw_log:
            continue
        
        normalized.append({
            "raw_log": raw_log,
            "timestamp_equipo": timestamp_equipo,
            "log_level": log_level,
            "device_id": device_id,
            "tenant_id": tenant_id
        })
    
    return normalized


def _retry_with_backoff(func, max_retries: int, base_ms: int, *args, **kwargs):
    """
    Ejecuta func con reintentos exponenciales.
    
    Args:
        func: Función a ejecutar que devuelve (result, error_msg)
        max_retries: Número máximo de reintentos
        base_ms: Backoff base en milisegundos
    
    Returns:
        (result, error_msg) del último intento
    """
    for attempt in range(max_retries):
        result, error = func(*args, **kwargs)
        
        if result is not None:
            return result, None
        
        if attempt < max_retries - 1:
            wait_ms = base_ms * (2 ** attempt)
            logging.debug(f"Retry {attempt + 1}/{max_retries} después de {wait_ms}ms: {error}")
            time.sleep(wait_ms / 1000.0)
    
    return None, error


# ============================================================================
# Funciones Principales
# ============================================================================

def get_router_logs(device: Device, since_ts: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Obtiene logs del router MikroTik con reintentos y múltiples proveedores.
    
    Args:
        device: Modelo Device con credenciales cifradas
        since_ts: Opcional, timestamp desde el cual obtener logs (UTC)
    
    Returns:
        Lista normalizada de dicts:
        {
            "raw_log": str,
            "timestamp_equipo": datetime | None,
            "log_level": str | None,
            "device_id": int,
            "tenant_id": int
        }
    
    Lógica de fallback según ROS_PROVIDER:
    - "librouteros": Solo intenta librouteros
    - "routeros_api": Solo intenta routeros-api
    - "ssh": Solo intenta SSH
    - "auto" (default): Intenta librouteros → routeros-api → SSH
    
    Implementa:
    - Reintentos exponenciales con backoff
    - Timeouts configurables
    - Logging estructurado (NO imprime credenciales)
    - Manejo de errores de red/auth
    """
    limit = Config.MONITORING_LOG_LIMIT
    provider = Config.ROS_PROVIDER.lower()
    
    # Descifrar credenciales (NUNCA loguear)
    username = decrypt_secret(device.username_encrypted)
    password = decrypt_secret(device.password_encrypted)
    ip = device.ip_address
    
    # Determinar puerto según proveedor
    # Nota: El modelo Device.port puede usarse para SSH; para API usamos Config.ROS_API_PORT
    api_port = Config.ROS_API_PORT
    ssh_port = device.port or Config.ROS_SSH_PORT
    
    connect_timeout = Config.ROS_CONNECT_TIMEOUT_SEC
    command_timeout = Config.ROS_COMMAND_TIMEOUT_SEC
    use_ssl = Config.ROS_USE_SSL
    max_retries = Config.ROS_MAX_RETRIES
    backoff_base = Config.ROS_BACKOFF_BASE_MS
    
    collected: List[Dict[str, Any]] = []
    
    # ========================================================================
    # Estrategia de conexión según provider
    # ========================================================================
    
    if provider == "librouteros":
        # Solo librouteros
        result, error = _retry_with_backoff(
            _connect_librouteros,
            max_retries,
            backoff_base,
            ip, username, password, api_port, connect_timeout, use_ssl
        )
        
        if result:
            api = result
            try:
                # Ejecutar /log/print
                # librouteros usa api.path('/log').select()
                log_path = api.path('/log')
                
                # TODO: Filtrar por since_ts si se proporciona
                # Ejemplo: log_path.select().where('time', '>', since_ts_formatted)
                
                entries = list(log_path.select())
                # Limitar desde el final (más recientes)
                entries = entries[-limit:] if len(entries) > limit else entries
                
                collected = _normalize_log_rows(entries, device.id, device.tenant_id)
                logging.info(f"monitoring: librouteros obtuvo {len(collected)} logs de device_id={device.id}")
            except Exception as e:
                logging.error(f"monitoring: librouteros query failed device_id={device.id}: {e}")
            finally:
                try:
                    api.close()
                except:
                    pass
        else:
            logging.warning(f"monitoring: librouteros failed device_id={device.id}: {error}")
    
    elif provider == "routeros_api":
        # Solo routeros-api
        result, error = _retry_with_backoff(
            _connect_routeros_api,
            max_retries,
            backoff_base,
            ip, username, password, api_port, connect_timeout, use_ssl
        )
        
        if result:
            pool, api = result
            try:
                # routeros-api usa api.get_resource('/log').get()
                log_resource = api.get_resource('/log')
                entries = log_resource.get()
                
                # Limitar desde el final
                entries = entries[-limit:] if len(entries) > limit else entries
                
                collected = _normalize_log_rows(entries, device.id, device.tenant_id)
                logging.info(f"monitoring: routeros-api obtuvo {len(collected)} logs de device_id={device.id}")
            except Exception as e:
                logging.error(f"monitoring: routeros-api query failed device_id={device.id}: {e}")
            finally:
                try:
                    pool.disconnect()
                except:
                    pass
        else:
            logging.warning(f"monitoring: routeros-api failed device_id={device.id}: {error}")
    
    elif provider == "ssh":
        # Solo SSH
        result, error = _retry_with_backoff(
            _fetch_logs_via_ssh,
            max_retries,
            backoff_base,
            ip, username, password, ssh_port, command_timeout, limit
        )
        
        if result:
            lines = result
            collected = _normalize_log_rows(lines, device.id, device.tenant_id)
            logging.info(f"monitoring: SSH obtuvo {len(collected)} logs de device_id={device.id}")
        else:
            logging.warning(f"monitoring: SSH failed device_id={device.id}: {error}")
    
    elif provider == "auto":
        # Fallback en cascada: librouteros → routeros-api → SSH
        
        # Intento 1: librouteros
        result, error = _retry_with_backoff(
            _connect_librouteros,
            max_retries,
            backoff_base,
            ip, username, password, api_port, connect_timeout, use_ssl
        )
        
        if result:
            api = result
            try:
                log_path = api.path('/log')
                entries = list(log_path.select())
                entries = entries[-limit:] if len(entries) > limit else entries
                collected = _normalize_log_rows(entries, device.id, device.tenant_id)
                logging.info(f"monitoring: librouteros (auto) obtuvo {len(collected)} logs de device_id={device.id}")
            except Exception as e:
                logging.warning(f"monitoring: librouteros query failed device_id={device.id}: {e}")
            finally:
                try:
                    api.close()
                except:
                    pass
        else:
            logging.debug(f"monitoring: librouteros (auto) failed device_id={device.id}: {error}, intentando routeros-api")
        
        # Intento 2: routeros-api (si librouteros falló)
        if not collected:
            result, error = _retry_with_backoff(
                _connect_routeros_api,
                max_retries,
                backoff_base,
                ip, username, password, api_port, connect_timeout, use_ssl
            )
            
            if result:
                pool, api = result
                try:
                    log_resource = api.get_resource('/log')
                    entries = log_resource.get()
                    entries = entries[-limit:] if len(entries) > limit else entries
                    collected = _normalize_log_rows(entries, device.id, device.tenant_id)
                    logging.info(f"monitoring: routeros-api (auto) obtuvo {len(collected)} logs de device_id={device.id}")
                except Exception as e:
                    logging.warning(f"monitoring: routeros-api query failed device_id={device.id}: {e}")
                finally:
                    try:
                        pool.disconnect()
                    except:
                        pass
            else:
                logging.debug(f"monitoring: routeros-api (auto) failed device_id={device.id}: {error}, intentando SSH")
        
        # Intento 3: SSH (si ambos API fallaron)
        if not collected:
            result, error = _retry_with_backoff(
                _fetch_logs_via_ssh,
                max_retries,
                backoff_base,
                ip, username, password, ssh_port, command_timeout, limit
            )
            
            if result:
                lines = result
                collected = _normalize_log_rows(lines, device.id, device.tenant_id)
                logging.info(f"monitoring: SSH (auto) obtuvo {len(collected)} logs de device_id={device.id}")
            else:
                logging.error(f"monitoring: todos los métodos fallaron device_id={device.id}: {error}")
    
    else:
        logging.error(f"monitoring: ROS_PROVIDER desconocido '{provider}', sin conexión device_id={device.id}")
    
    return collected


def analyze_and_generate_alerts(device: Device) -> None:
    """
    Pipeline completo de monitoreo:
    
    1) Obtiene logs del router (get_router_logs)
    2) Persiste en LogEntry (bulk insert)
    3) Analiza con IA (analyze_logs: heuristic/deepseek según config)
    4) Crea Alerts evitando duplicados en ventana corta
    
    Maneja errores de red/IA sin romper el flujo.
    """
    try:
        # Paso 1: Obtener logs del router
        items = get_router_logs(device)
        
        if not items:
            logging.info(f"monitoring: sin logs nuevos device_id={device.id}")
            return
        
        now = datetime.utcnow()
        
        # Paso 2: Persistencia en bulk
        entries: List[LogEntry] = []
        for itm in items:
            raw = itm.get("raw_log", "")
            ts = itm.get("timestamp_equipo") or now
            level = itm.get("log_level")
            
            if not raw:
                continue
            
            le = LogEntry(
                tenant_id=device.tenant_id,
                device_id=device.id,
                raw_log=raw,
                log_level=level,
                timestamp_equipo=ts
            )
            # Forzar created_at explícito (aunque hay server_default)
            le.created_at = now
            entries.append(le)
        
        if entries:
            db.session.add_all(entries)
            db.session.flush()  # Asegura IDs antes del análisis
            logging.info(f"monitoring: persistidos {len(entries)} logs device_id={device.id}")
        
        # Paso 3: Análisis IA
        log_list = [e.raw_log for e in entries]
        
        # Preparar contexto del dispositivo para DeepSeek
        device_context = {
            "name": device.name,
            "ip": device.ip_address
        }
        
        suggestions: List[Dict[str, Any]] = []
        try:
            # analyze_logs maneja provider automáticamente (heuristic/deepseek/auto)
            suggestions = analyze_logs(log_list, device_context=device_context)
            logging.info(f"monitoring: IA generó {len(suggestions)} sugerencias device_id={device.id}")
        except Exception as ex:
            logging.warning(f"monitoring: analyze_logs falló device_id={device.id}: {ex}")
        
        # Paso 4: Crear alertas (dedupe simple en ventana corta)
        created_alerts = 0
        window_start = now - timedelta(minutes=10)  # TODO: parametrizar ventana
        
        for sug in suggestions:
            try:
                estado = sug.get("estado")
                titulo = sug.get("titulo")
                descripcion = sug.get("descripcion")
                accion = sug.get("accion_recomendada")
                
                if not all([estado, titulo, descripcion, accion]):
                    continue
                
                # Dedupe: mismo device + estado + titulo en ventana
                exists = (Alert.query
                         .filter_by(tenant_id=device.tenant_id, device_id=device.id, estado=estado, titulo=titulo)
                         .filter(Alert.created_at >= window_start)
                         .first())
                
                if exists:
                    logging.debug(f"monitoring: alerta duplicada skip device_id={device.id}: {titulo}")
                    continue
                
                alert = Alert(
                    tenant_id=device.tenant_id,
                    device_id=device.id,
                    estado=estado,
                    titulo=titulo,
                    descripcion=descripcion,
                    accion_recomendada=accion,
                    status_operativo="Pendiente",
                    comentario_ultimo=None
                )
                alert.created_at = now
                alert.updated_at = now
                
                db.session.add(alert)
                created_alerts += 1
            except Exception as ex:
                logging.error(f"monitoring: error creando alerta device_id={device.id}: {ex}")
        
        if created_alerts > 0:
            logging.info(f"monitoring: creadas {created_alerts} alertas device_id={device.id}")
        
        # Commit todo de una vez (logs + alertas)
        db.session.commit()
        
    except Exception as ex:
        logging.error(f"monitoring: error general device_id={device.id}: {ex}")
        db.session.rollback()