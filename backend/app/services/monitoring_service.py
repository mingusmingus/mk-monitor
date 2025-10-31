"""
Servicio de monitoreo:

- Conecta a routers MikroTik (SSH/API) para obtener logs.
- Persiste LogEntry y dispara análisis por IA.
- Respeta límites de plan (número de equipos por tenant).
"""
from typing import List
from datetime import datetime
from ..models.device import Device
from ..models.log_entry import LogEntry
from ..models.alert import Alert
from ..db import db
from .ai_analysis_service import analyze_logs

def get_router_logs(device: Device) -> List[str]:
    """
    Devuelve lista de logs crudos desde el MikroTik.
    TODO: Implementar conexión real (API/SSH) al router (ros_api).
    """
    # Placeholder de ejemplo
    return [
        "interface pppoe reconnect",
        "login failed for user admin from 10.0.0.5",
    ]

def analyze_and_generate_alerts(device: Device) -> None:
    """
    1) Trae logs del router
    2) Inserta LogEntry con timestamp del equipo (aprox now)
    3) Analiza con IA y crea Alert si corresponde
    TODO: Integrar con motor IA real (LLM / DeepSeek) y normalización de logs.
    """
    logs = get_router_logs(device)

    # Persistir logs crudos
    now = datetime.utcnow()
    for line in logs:
        le = LogEntry(
            tenant_id=device.tenant_id,
            device_id=device.id,
            raw_log=line,
            log_level=None,
            timestamp_equipo=now,
        )
        db.session.add(le)

    # Análisis IA
    sugeridas = analyze_logs(logs)  # lista de dicts normalizados
    for sug in sugeridas:
        alert = Alert(
            tenant_id=device.tenant_id,
            device_id=device.id,
            estado=sug["estado"],
            titulo=sug["titulo"],
            descripcion=sug["descripcion"],
            accion_recomendada=sug["accion_recomendada"],
            status_operativo="Pendiente",
        )
        db.session.add(alert)

    db.session.commit()