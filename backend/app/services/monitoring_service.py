"""
Servicio de Monitoreo Forense.

Este servicio orquesta el ciclo completo de inteligencia de amenazas:
1. Conecta con routers Mikrotik para extraer datos forenses profundos (Device Mining).
2. Normaliza y persiste los logs en la base de datos.
3. Invoca el análisis de Inteligencia Artificial (DeepSeek) sobre el contexto extraído.
4. Genera alertas operativas ("Reportes Forenses") basadas en los hallazgos.

Maneja la deduplicación de logs y alertas para evitar ruido.
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
from .ai_analysis_service import analyze_device_context
from .device_mining import DeviceMiner

def _safe_decode(value: Any) -> Any:
    """
    Decodifica bytes a texto UTF-8 de forma segura.

    Args:
        value (Any): Valor a decodificar.

    Returns:
        str: Cadena decodificada.
    """
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="ignore")
    return value

def _entry_timestamp_to_iso(entry: Dict[str, Any]) -> str:
    """
    Normaliza marcas temporales de RouterOS a formato ISO8601.

    RouterOS puede entregar timestamps en múltiples formatos inconsistentes.
    Esta función aplica heurísticas para unificar el formato.

    Args:
        entry (Dict[str, Any]): Entrada de log cruda desde la API.

    Returns:
        str: Timestamp en formato ISO8601.
    """
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
    """
    Convierte cadenas ISO8601 a objetos datetime de forma robusta.

    Args:
        value (Optional[str]): Cadena de fecha/hora.

    Returns:
        Optional[datetime]: Objeto datetime o None si falla.
    """
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

def analyze_and_generate_alerts(device: Device) -> None:
    """
    Ejecuta el pipeline completo de monitoreo Forense para un dispositivo.
    
    Fases:
    1) Minería de Datos (DeviceMiner): Extracción profunda de estado y logs.
    2) Persistencia: Almacenamiento de nuevos logs con deduplicación.
    3) Análisis IA: Procesamiento del contexto extraído mediante DeepSeek.
    4) Generación de Alertas: Creación de incidentes operativos basados en hallazgos.

    Args:
        device (Device): Dispositivo objetivo.
    """
    try:
        # Paso 1: Minería de Datos
        miner = DeviceMiner(device)
        data = miner.mine()
        
        if "error" in data:
            logging.error(f"[ERROR] monitoring: Error minando datos device_id={device.id}: {data['error']}")
            return

        now = datetime.utcnow()
        
        # Paso 2: Persistencia de Logs (bulk)
        logs_raw = data.get("logs", [])

        # Obtener el último timestamp de log de este device para deduplicar
        last_log = (LogEntry.query
                    .filter_by(device_id=device.id)
                    .order_by(LogEntry.timestamp_equipo.desc())
                    .first())
        last_ts = last_log.timestamp_equipo if last_log else None

        entries: List[LogEntry] = []

        # Normalización de logs
        for log_item in logs_raw:
            msg = log_item.get("message", "")
            topics = log_item.get("topics", "")
            
            ts_iso = _entry_timestamp_to_iso(log_item)
            ts_dt = _safe_parse_iso_datetime(ts_iso) or now
            
            # Deduplicación básica por timestamp
            if last_ts and ts_dt < last_ts:
                 continue

            # Verificación de existencia para evitar duplicados en el mismo segundo
            if last_ts and ts_dt == last_ts:
                 exists = (LogEntry.query
                           .filter_by(device_id=device.id, timestamp_equipo=ts_dt)
                           .filter(LogEntry.raw_log.like(f"%{msg}%")) # coincidencia parcial
                           .first())
                 if exists:
                     continue

            le = LogEntry(
                tenant_id=device.tenant_id,
                device_id=device.id,
                raw_log=f"[{topics}] {msg}" if topics else msg,
                log_level="info", # Default, se podría parsear de topics
                timestamp_equipo=ts_dt
            )
            entries.append(le)
        
        if entries:
            db.session.add_all(entries)
            db.session.flush()
            logging.info(f"[INFO] monitoring: persistidos {len(entries)} logs device_id={device.id}")
        
        # Paso 3: Análisis IA
        analysis_result = analyze_device_context(data)
        
        # Paso 4: Crear Alerta (Reporte)
        analysis_text = analysis_result.get("analysis", "")
        recommendations = analysis_result.get("recommendations", [])
        
        if not analysis_text:
            logging.info("[INFO] monitoring: IA no retornó análisis.")
            return

        # Determinación de severidad
        severity = "Aviso"
        lower_analysis = analysis_text.lower()
        if "critical" in lower_analysis or "failure" in lower_analysis or "attack" in lower_analysis:
            severity = "Alerta Severa"
        if "warning" in lower_analysis or "high" in lower_analysis:
            severity = "Alerta Menor"
        
        # Override por heurística local
        heuristics = data.get("heuristics", [])
        if any("critical" in h.lower() for h in heuristics):
            severity = "Alerta Crítica"

        rec_text = "; ".join(recommendations)
        
        # Evitar spam de alertas idénticas (Ventana de 1 hora)
        window_start = now - timedelta(hours=1)
        exists = (Alert.query
                 .filter_by(tenant_id=device.tenant_id, device_id=device.id)
                 .filter(Alert.titulo == "Reporte Forense IA")
                 .filter(Alert.created_at >= window_start)
                 .first())

        if exists:
             logging.debug(f"[DEBUG] monitoring: Reporte reciente existe, saltando alerta device_id={device.id}")
        else:
            alert = Alert(
                tenant_id=device.tenant_id,
                device_id=device.id,
                estado=severity,
                titulo="Reporte Forense IA",
                descripcion=analysis_text[:512],
                accion_recomendada=rec_text[:255] or "Ver detalles en dashboard",
                status_operativo="Pendiente",
                comentario_ultimo="Generado automáticamente por DeepSeek"
            )
            db.session.add(alert)
            logging.info(f"[INFO] monitoring: Alerta Forense creada device_id={device.id}")

        db.session.commit()
        
    except Exception as ex:
        logging.error(f"[ERROR] monitoring: error general device_id={device.id}: {ex}")
        db.session.rollback()

# Helper legado (mantener compatibilidad)
def get_router_logs(device: Device, since_ts: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Wrapper legado para obtener logs. Utiliza DeviceMiner internamente.

    Args:
        device (Device): Dispositivo.
        since_ts (Optional[datetime]): Timestamp inicial (ignorado en minería actual).

    Returns:
        List[Dict[str, Any]]: Lista de logs normalizados.
    """
    miner = DeviceMiner(device)
    data = miner.mine()

    logs = []
    for l in data.get("logs", []):
         ts = _safe_parse_iso_datetime(_entry_timestamp_to_iso(l)) or datetime.utcnow()
         logs.append({
             "raw_log": l.get("message"),
             "timestamp_equipo": ts,
             "log_level": "info",
             "device_id": device.id,
             "tenant_id": device.tenant_id
         })
    return logs
