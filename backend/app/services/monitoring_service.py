"""
Servicio de monitoreo:

- Conecta a routers MikroTik (RouterOS API/SSH) para obtener logs.
- Persiste LogEntry y dispara análisis por IA.
- Respeta límites de plan (número de equipos por tenant).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
import time

from ..models.device import Device
from ..models.log_entry import LogEntry
from ..models.alert import Alert
from ..db import db
from ..config import Config
from .ai_analysis_service import analyze_logs
from .device_service import decrypt_secret


_ROUTEROS_MAX_ATTEMPTS = 2
_ROUTEROS_RETRY_DELAY_SEC = 0.5
_DEFAULT_ROUTEROS_PORT = 8728


def _safe_decode(value: Any) -> Any:
    """Decodifica bytes a texto UTF-8 sin lanzar excepción."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="ignore")
    return value


def _normalize_entry_dict(entry: Any) -> Dict[str, Any]:
    """Asegura que la entrada del API sea un dict con claves/valores str."""
    if isinstance(entry, dict):
        normalized: Dict[str, Any] = {}
        for key, val in entry.items():
            key_str = str(_safe_decode(key))
            normalized[key_str] = _safe_decode(val)
        return normalized
    return {"raw": _safe_decode(entry)}


def _entry_timestamp_to_iso(entry: Dict[str, Any]) -> str:
    """Convierte marcas temporales de RouterOS a ISO8601 (UTC naive)."""
    now = datetime.utcnow()
    timestamp_candidates = [
        str(entry.get(field)).strip()
        for field in ("timestamp", "time", "ts")
        if entry.get(field)
    ]
    date_value = str(entry.get("date", "")).strip()

    for candidate in timestamp_candidates:
        cleaned = candidate.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned)
            return parsed.isoformat()
        except ValueError:
            continue

    if date_value and timestamp_candidates:
        for candidate in timestamp_candidates:
            for fmt in ("%b/%d/%Y %H:%M:%S", "%b/%d/%Y %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    parsed = datetime.strptime(f"{date_value} {candidate}", fmt)
                    return parsed.isoformat()
                except ValueError:
                    continue

    if not date_value and timestamp_candidates:
        candidate = timestamp_candidates[0]
        for fmt in ("%b/%d %H:%M:%S", "%H:%M:%S", "%H:%M:%S.%f"):
            try:
                parsed = datetime.strptime(candidate, fmt)
                parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
                return parsed.isoformat()
            except ValueError:
                continue

    if date_value:
        for fmt in ("%b/%d/%Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(date_value, fmt)
                return parsed.isoformat()
            except ValueError:
                continue

    return now.isoformat()


def _safe_parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Convierte cadenas ISO8601 en datetime o retorna None si falla."""
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    candidate = candidate.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def _topic_to_log_level(topic: str) -> Optional[str]:
    if not topic:
        return None
    topic_lower = topic.lower()
    for level in ("error", "warning", "info", "debug"):
        if level in topic_lower:
            return level
    return None


def _resolve_routeros_port(device: Device) -> int:
    for attr in ("ros_api_port", "api_port", "routeros_port", "port"):
        value = getattr(device, attr, None)
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if isinstance(value, int) and value > 0:
            if attr == "port" and value == getattr(Config, "ROS_SSH_PORT", 22):
                continue
            return value
    return getattr(Config, "ROS_API_PORT", _DEFAULT_ROUTEROS_PORT) or _DEFAULT_ROUTEROS_PORT


def _resolve_socket_timeout() -> int:
    raw = os.getenv("MT_TIMEOUT_SEC")
    if raw:
        try:
            timeout = int(raw)
            return timeout if timeout > 0 else 5
        except ValueError:
            logging.warning("monitoring: MT_TIMEOUT_SEC inválido, usando 5s de timeout")
    return 5


def _fetch_router_logs_via_api(device: Device) -> List[Dict[str, Any]]:
    """Abre una sesión RouterOS API, ejecuta /log/print y transforma la respuesta."""
    host = getattr(device, "ip_address", None) or getattr(device, "host", None)
    if not host:
        logging.warning("monitoring: device_id=%s sin host configurado, omitiendo consulta de logs", device.id)
        return []

    try:
        username = decrypt_secret(device.username_encrypted)
        password = decrypt_secret(device.password_encrypted)
    except Exception as exc:  # noqa: BLE001
        logging.error("monitoring: no se pudieron descifrar credenciales device_id=%s: %s", device.id, exc)
        return []

    try:
        from routeros_api import RouterOsApiPool
        from routeros_api.exceptions import (
            RouterOsApiCommunicationError,
            RouterOsApiConnectionError,
            RouterOsApiError,
        )
    except ImportError:
        logging.warning("monitoring: routeros_api no instalado; instala routeros-api para habilitar logs")
        return []

    port = _resolve_routeros_port(device)
    timeout = _resolve_socket_timeout()

    formatted_entries: List[Dict[str, Any]] = []

    for attempt in range(1, _ROUTEROS_MAX_ATTEMPTS + 1):
        pool = None
        attempt_entries: List[Dict[str, Any]] = []
        try:
            pool = RouterOsApiPool(
                host,
                username=username,
                password=password,
                port=port,
                plaintext_login=True,
                use_ssl=False,
                socket_timeout=timeout,
            )
            api = pool.get_api()
            raw_entries = api.call("/log/print") or []
            if isinstance(raw_entries, dict):
                raw_entries = raw_entries.get("ret", [])

            for raw_entry in raw_entries:
                decoded = _normalize_entry_dict(raw_entry)
                attempt_entries.append(
                    {
                        "timestamp": _entry_timestamp_to_iso(decoded),
                        "message": str(decoded.get("message") or decoded.get("msg") or "").strip(),
                        "topic": str(decoded.get("topics") or decoded.get("topic") or "").strip(),
                        "raw": decoded,
                    }
                )

            formatted_entries = attempt_entries
            logging.debug(
                "monitoring: routeros_api obtuvo %s logs device_id=%s host=%s",
                len(formatted_entries),
                device.id,
                host,
            )
            break
        except (
            RouterOsApiCommunicationError,
            RouterOsApiConnectionError,
            RouterOsApiError,
            OSError,
        ) as exc:  # noqa: PERF203
            logging.warning(
                "monitoring: intento %s/%s routeros_api falló device_id=%s host=%s: %s",
                attempt,
                _ROUTEROS_MAX_ATTEMPTS,
                device.id,
                host,
                exc,
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(
                "monitoring: error inesperado consultando routeros_api device_id=%s host=%s: %s",
                device.id,
                host,
                exc,
            )
        finally:
            if pool:
                try:
                    pool.disconnect()
                except Exception:  # noqa: BLE001
                    logging.debug("monitoring: error cerrando pool RouterOS device_id=%s", device.id)

        if formatted_entries:
            break

        if attempt < _ROUTEROS_MAX_ATTEMPTS:
            time.sleep(_ROUTEROS_RETRY_DELAY_SEC)

    return formatted_entries


def _build_mock_logs(device: Device) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    base_messages = [
        ("Monitoreo simulado activo", "info"),
        ("Tráfico de prueba procesado sin errores", "debug"),
        ("Sin eventos críticos detectados", "info"),
    ]
    return [
        {
            "raw_log": f"[mock] {message}",
            "timestamp_equipo": now,
            "log_level": level,
            "device_id": device.id,
            "tenant_id": device.tenant_id,
        }
        for message, level in base_messages
    ]


def get_router_logs(device: Device, since_ts: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Obtiene logs RouterOS normalizados sin propagar errores.

    Flujo:
    1. Detecta dispositivos de prueba (`is_mock`/`is_test` o host "dummy") y retorna logs simulados.
    2. Para dispositivos reales abre una sesión RouterOS API con `routeros_api.RouterOsApiPool`.
    3. Ejecuta `/log/print`, transforma cada entrada y filtra por `since_ts` cuando es posible.
    4. Cualquier error de conexión/autenticación se registra a nivel WARNING y la función retorna [].

    Args:
        device: Dispositivo con credenciales cifradas.
        since_ts: Timestamp UTC opcional para descartar logs antiguos (si la marca temporal se puede parsear).

    Returns:
        Lista de dicts listos para persistir en `LogEntry`. Nunca lanza excepciones.
    """
    try:
        if device is None:
            logging.warning("monitoring: se solicitó get_router_logs con device=None")
            return []

        host_value = getattr(device, "ip_address", None) or getattr(device, "host", None) or ""
        mock_flag = bool(getattr(device, "is_mock", False) or getattr(device, "is_test", False))
        if isinstance(host_value, str) and host_value.lower() == "dummy":
            mock_flag = True

        if mock_flag:
            logging.debug("monitoring: devolviendo logs simulados para device_id=%s", device.id)
            return _build_mock_logs(device)

        raw_entries = _fetch_router_logs_via_api(device)
        if not raw_entries:
            return []

        limit = getattr(Config, "MONITORING_LOG_LIMIT", 200) or 200
        normalized: List[Dict[str, Any]] = []

        for entry in raw_entries:
            message = entry.get("message") or ""
            topic = entry.get("topic") or ""
            raw_data = entry.get("raw")

            raw_text = message.strip()
            if topic:
                if raw_text:
                    raw_text = f"[{topic}] {raw_text}".strip()
                else:
                    raw_text = topic.strip()

            if not raw_text:
                if isinstance(raw_data, dict):
                    raw_text = str(raw_data).strip()
                elif raw_data is not None:
                    raw_text = str(raw_data).strip()

            if not raw_text:
                continue

            timestamp_iso = entry.get("timestamp")
            timestamp_dt = _safe_parse_iso_datetime(timestamp_iso)

            include_due_since = True
            if since_ts and timestamp_dt:
                include_due_since = timestamp_dt >= since_ts

            if not include_due_since:
                continue

            normalized.append(
                {
                    "raw_log": raw_text,
                    "timestamp_equipo": timestamp_dt,
                    "log_level": _topic_to_log_level(topic),
                    "device_id": device.id,
                    "tenant_id": device.tenant_id,
                }
            )

        if len(normalized) > limit:
            normalized = normalized[-limit:]

        if normalized:
            logging.info(
                "monitoring: routeros_api obtuvo %s logs device_id=%s",
                len(normalized),
                device.id,
            )
        else:
            logging.info(
                "monitoring: routeros_api retornó entradas sin contenido utilizable device_id=%s",
                device.id,
            )

        return normalized

    except Exception as exc:  # noqa: BLE001
        logging.error("monitoring: error inesperado en get_router_logs device_id=%s: %s", getattr(device, "id", "?"), exc)
        return []


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
        # Preparamos lista estructurada para la IA (mejor contexto)
        # items ya tiene {raw_log, timestamp_equipo, log_level, ...}
        log_list = []
        for itm in items:
            log_list.append({
                "timestamp": itm.get("timestamp_equipo"),
                "log_message": itm.get("raw_log"),
                "log_level": itm.get("log_level"),
                "equipment_name": device.name
            })
        
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