"""
Servicio de monitoreo:

- Conecta a routers MikroTik (RouterOS API) para minería de datos forense.
- Persiste LogEntry y dispara análisis por IA (DeepSeek).
- Respeta límites de plan.
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
    """Decodifica bytes a texto UTF-8 sin lanzar excepción."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="ignore")
    return value

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

def analyze_and_generate_alerts(device: Device) -> None:
    """
    Pipeline completo de monitoreo Forense:
    
    1) Minería de datos profunda (DeviceMiner).
    2) Persistencia de Logs en LogEntry.
    3) Análisis Forense IA (DeepSeek via AIProvider).
    4) Generación de Alerta unificada (Reporte Forense).
    """
    try:
        # Paso 1: Minería de Datos
        miner = DeviceMiner(device)
        data = miner.mine()
        
        if "error" in data:
            logging.error(f"monitoring: Error minando datos device_id={device.id}: {data['error']}")
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

        # The miner returns raw logs from API. We need to normalize them for DB.
        # miner._get_logs returns dicts from routeros_api.
        for log_item in logs_raw:
            # We assume log_item is a dict from routeros_api
            msg = log_item.get("message", "")
            topics = log_item.get("topics", "")
            
            # Parse timestamp using the robust helper
            ts_iso = _entry_timestamp_to_iso(log_item)
            ts_dt = _safe_parse_iso_datetime(ts_iso) or now
            
            # Deduplication: Skip if older or equal to last known log timestamp
            if last_ts and ts_dt <= last_ts:
                # To be safer against exact timestamp collisions of different logs,
                # we could also check content hash, but timestamp > last_ts is a standard simple approach.
                # However, within the same second, we might lose logs.
                # Ideally, we should check existence of (device_id, timestamp_equipo, raw_log).
                # For performance, we'll stick to strict > if last_ts is recent.
                # Or we can do a quick existence check in memory if bulk is small.
                pass

            # Since strict > might miss logs in same second, let's allow >= but check message.
            # Efficient dedupe for small batches:
            if last_ts and ts_dt < last_ts:
                 continue

            # If equal, check if exists in DB (expensive? typically 50 logs max)
            if last_ts and ts_dt == last_ts:
                 exists = (LogEntry.query
                           .filter_by(device_id=device.id, timestamp_equipo=ts_dt)
                           .filter(LogEntry.raw_log.like(f"%{msg}%")) # partial match
                           .first())
                 if exists:
                     continue

            le = LogEntry(
                tenant_id=device.tenant_id,
                device_id=device.id,
                raw_log=f"[{topics}] {msg}" if topics else msg,
                log_level="info", # Default, can parse from topics
                timestamp_equipo=ts_dt
            )
            entries.append(le)
        
        if entries:
            db.session.add_all(entries)
            db.session.flush()
            logging.info(f"monitoring: persistidos {len(entries)} logs device_id={device.id}")
        
        # Paso 3: Análisis IA
        analysis_result = analyze_device_context(data)
        
        # Paso 4: Crear Alerta (Reporte)
        # We create a single alert summarizing the findings
        analysis_text = analysis_result.get("analysis", "")
        recommendations = analysis_result.get("recommendations", [])
        
        if not analysis_text:
            logging.info("monitoring: IA no retornó análisis.")
            return

        # Determine severity based on content or heuristics
        # Simple keyword matching for severity
        severity = "Aviso"
        lower_analysis = analysis_text.lower()
        if "critical" in lower_analysis or "failure" in lower_analysis or "attack" in lower_analysis:
            severity = "Alerta Severa"
        if "warning" in lower_analysis or "high" in lower_analysis:
            severity = "Alerta Menor"
        
        # Check heuristics from data for override
        heuristics = data.get("heuristics", [])
        if any("critical" in h.lower() for h in heuristics):
            severity = "Alerta Crítica"

        rec_text = "; ".join(recommendations)
        
        # Dedupe check: don't spam if identical report recently
        window_start = now - timedelta(hours=1)
        exists = (Alert.query
                 .filter_by(tenant_id=device.tenant_id, device_id=device.id)
                 .filter(Alert.titulo == "Reporte Forense IA")
                 .filter(Alert.created_at >= window_start)
                 .first())

        if exists:
             # Update existing? Or just skip.
             # If severity changed, maybe update.
             logging.debug(f"monitoring: Reporte reciente existe, saltando alerta device_id={device.id}")
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
            logging.info(f"monitoring: Alerta Forense creada device_id={device.id}")

        db.session.commit()
        
    except Exception as ex:
        logging.error(f"monitoring: error general device_id={device.id}: {ex}")
        db.session.rollback()

# Helper for manual log fetching if needed by other services (retained for compatibility)
def get_router_logs(device: Device, since_ts: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Legacy wrapper using DeviceMiner to fetch logs.
    """
    miner = DeviceMiner(device)
    data = miner.mine()
    # Normalize back to old structure if needed
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
