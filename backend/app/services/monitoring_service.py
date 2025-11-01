"""
Servicio de monitoreo:

- Conecta a routers MikroTik (SSH/API) para obtener logs.
- Persiste LogEntry y dispara análisis por IA.
- Respeta límites de plan (número de equipos por tenant).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..models.device import Device
from ..models.log_entry import LogEntry
from ..models.alert import Alert
from ..db import db
from ..config import Config
from .ai_analysis_service import analyze_logs
from .device_service import decrypt_secret

def get_router_logs(device: Device) -> List[Dict[str, Any]]:
    """
    Obtiene logs del router (best-effort).
    - Intenta RouterOS API (routeros_api). Si no está disponible o falla, intenta SSH (paramiko).
    - Nunca expone secretos en logs.
    - Limita resultados a Config.MONITORING_LOG_LIMIT.
    - Devuelve lista normalizada:
      { "raw_log": str, "timestamp_equipo": datetime|None, "log_level": str|None }

    TODO:
    - Integración real con RouterOS API (paginar y limitar desde el dispositivo).
    - Parsear timestamp 'time' de RouterOS (cuando viene sin fecha) con zona horaria del equipo.
    - Alternativa futura: ingesta por push vía syslog.
    """
    limit = int(getattr(Config, "MONITORING_LOG_LIMIT", 200))
    connect_timeout = int(getattr(Config, "MIKROTIK_CONNECT_TIMEOUT", 5))
    read_timeout = int(getattr(Config, "MIKROTIK_READ_TIMEOUT", 10))

    # Credenciales (descifradas) — NO loguear
    username = decrypt_secret(device.username_encrypted)
    password = decrypt_secret(device.password_encrypted)
    ip = device.ip_address
    port = device.port or 8728  # Nota: RouterOS API usa 8728/8729; aquí reutilizamos el puerto del modelo.

    collected: List[Dict[str, Any]] = []

    # Intento 1: RouterOS API (routeros_api)
    pool = None
    try:
        try:
            import routeros_api  # type: ignore
        except Exception:
            routeros_api = None  # type: ignore

        if routeros_api:
            try:
                # plaintext_login=True suele ser necesario si no hay SSL; ajustar según entorno.
                pool = routeros_api.RouterOsApiPool(
                    ip,
                    username=username,
                    password=password,
                    port=port,
                    use_ssl=False,
                    plaintext_login=True,
                    socket_timeout=read_timeout
                )
                api = pool.get_api()
                # Diferentes versiones de lib exponen APIs distintas; probamos ambas.
                entries: List[Any] = []
                try:
                    res = api.get_resource('/log')  # type: ignore
                    entries = res.get()  # type: ignore
                except Exception:
                    try:
                        entries = api.call('/log/print')  # type: ignore
                    except Exception:
                        entries = []

                # Normalización
                for e in entries[-limit:]:
                    if isinstance(e, dict):
                        msg = e.get("message") or e.get("msg") or str(e)
                        topic = e.get("topics") or e.get("topic")
                        ts_raw = e.get("time") or e.get("timestamp")
                        dt = None  # TODO: parsear 'time' cuando trae fecha completa
                        collected.append({
                            "raw_log": str(msg),
                            "timestamp_equipo": dt,
                            "log_level": str(topic) if topic else None
                        })
                    else:
                        collected.append({
                            "raw_log": str(e),
                            "timestamp_equipo": None,
                            "log_level": None
                        })
            except Exception as ex:
                logging.warning("monitoring: fallo RouterOS API device_id=%s: %s", device.id, ex)
            finally:
                try:
                    if pool:
                        pool.disconnect()
                except Exception:
                    pass
        else:
            logging.info("monitoring: routeros_api no instalado; saltando API device_id=%s", device.id)
    except Exception as ex:
        logging.warning("monitoring: error general RouterOS API device_id=%s: %s", device.id, ex)

    # Si no obtuvimos nada, Intento 2: SSH (paramiko)
    if not collected:
        try:
            try:
                import paramiko  # type: ignore
            except Exception:
                paramiko = None  # type: ignore

            if paramiko:
                ssh = None
                try:
                    ssh = paramiko.SSHClient()  # type: ignore
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # type: ignore
                    ssh.connect(
                        ip, port=port or 22,
                        username=username, password=password,
                        timeout=connect_timeout,
                        banner_timeout=connect_timeout,
                        auth_timeout=connect_timeout
                    )
                    cmd = "/log/print without-paging"
                    _, stdout, _ = ssh.exec_command(cmd, timeout=read_timeout)
                    out = stdout.read().decode(errors="ignore").splitlines()
                    for line in out[-limit:]:
                        collected.append({
                            "raw_log": line,
                            "timestamp_equipo": None,  # TODO: intentar inferir del prefijo del log
                            "log_level": None
                        })
                except Exception as ex:
                    logging.warning("monitoring: fallo SSH device_id=%s: %s", device.id, ex)
                finally:
                    try:
                        if ssh:
                            ssh.close()
                    except Exception:
                        pass
            else:
                logging.info("monitoring: paramiko no instalado; sin fallback SSH device_id=%s", device.id)
        except Exception as ex:
            logging.warning("monitoring: error general SSH device_id=%s: %s", device.id, ex)

    # Tope final
    if len(collected) > limit:
        collected = collected[-limit:]

    return collected

def analyze_and_generate_alerts(device: Device) -> None:
    """
    1) Trae logs del router.
    2) Inserta LogEntry (bulk).
    3) Analiza con IA (heurística por defecto).
    4) Crea Alert(s) evitando duplicados obvios en ventana corta.
    """
    try:
        items = get_router_logs(device)
        if not items:
            return

        now = datetime.utcnow()

        # Paso 2: persistencia en bulk
        entries: List[LogEntry] = []
        for itm in items[: int(getattr(Config, "MONITORING_LOG_LIMIT", 200))]:
            # Tolerar formato string antiguo (compat)
            if isinstance(itm, dict):
                raw = str(itm.get("raw_log", ""))
                ts = itm.get("timestamp_equipo") or now
                level = itm.get("log_level")
            else:
                raw = str(itm)
                ts = now
                level = None

            if not raw:
                continue

            le = LogEntry(
                tenant_id=device.tenant_id,
                device_id=device.id,
                raw_log=raw,
                log_level=level,
                timestamp_equipo=ts
            )
            # Forzar created_at en app (aunque hay server_default)
            le.created_at = now
            entries.append(le)

        if entries:
            db.session.add_all(entries)
            db.session.flush()  # asegura IDs/consistencia antes del análisis (si hiciera falta)

        # Paso 3: análisis IA (heurístico actual)
        log_list = [e.raw_log for e in entries]
        provider = str(getattr(Config, "AI_ANALYSIS_PROVIDER", "heuristic")).lower()

        suggestions: List[Dict[str, Any]] = []
        try:
            # Contrato existente: analyze_logs(log_list) sin contexto obligatorio
            suggestions = analyze_logs(log_list)
            # TODO: si provider == "deepseek" o "auto", integrar llamada real a DeepSeek usando:
            #   - Config.DEEPSEEK_API_URL, Config.DEEPSEEK_MODEL, DEEPSEEK_API_KEY (desde entorno),
            #   - Config.AI_TIMEOUT_SEC, Config.AI_MAX_TOKENS
        except Exception as ex:
            logging.warning("monitoring: analyze_logs falló device_id=%s: %s", device.id, ex)
            suggestions = []

        # Paso 4/5: crear alertas (dedupe simple en ventana corta)
        created_alerts = 0
        window_start = now - timedelta(minutes=10)  # TODO: parametrizar ventana
        for sug in suggestions:
            try:
                estado = sug.get("estado")
                titulo = sug.get("titulo")
                descripcion = sug.get("descripcion")
                accion = sug.get("accion_recomendada")

                if not (estado and titulo and descripcion and accion):
                    continue

                # Dedupe: mismo device + estado + titulo en ventana
                exists = (Alert.query
                          .filter_by(tenant_id=device.tenant_id, device_id=device.id, estado=estado, titulo=titulo)
                          .filter(Alert.created_at >= window_start)
                          .first())
                if exists:
                    continue

                alert = Alert(
                    tenant_id=device.tenant_id,
                    device_id=device.id,
                    estado=estado,
                    titulo=titulo,
                    descripcion=descripcion,
                    accion_recomendada=accion,
                    status_operativo="Pendiente",
                    comentario_ultimo=None,
                    created_at=now,
                    updated_at=now
                )
                db.session.add(alert)
                created_alerts += 1
            except Exception as ex:
                logging.warning("monitoring: error creando alerta device_id=%s: %s", device.id, ex)

        db.session.commit()
        if created_alerts:
            logging.info("monitoring: %s alertas nuevas device_id=%s", created_alerts, device.id)
        # TODO: métrica/telemetría (contadores por severidad)
    except Exception as ex:
        logging.warning("monitoring: error general analyze_and_generate_alerts device_id=%s: %s", device.id, ex)
        try:
            db.session.rollback()
        except Exception:
            pass