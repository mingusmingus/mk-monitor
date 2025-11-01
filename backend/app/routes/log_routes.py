"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
"""
from flask import Blueprint, request, jsonify, g, Response
from ..auth.decorators import require_auth
from ..models.log_entry import LogEntry
from ..models.device import Device
from datetime import datetime
import io, csv

log_bp = Blueprint("logs", __name__)

@log_bp.get("/devices/<int:device_id>/logs")
@require_auth()
def device_logs(device_id: int):
    """
    Devuelve logs del dispositivo dentro del tenant.
    
    Query params:
      - limit (5|10|20; default 10)
      - fecha_inicio (ISO 8601 UTC)
      - fecha_fin (ISO 8601 UTC)
      - export: csv | pdf
    
    Nota importante (timezone - prioridad BAJA):
      Las fechas recibidas (fecha_inicio, fecha_fin) se interpretan en UTC.
      El campo timestamp_equipo se almacena y consulta como timezone-aware (UTC).
      Si el cliente envía fechas locales, debe convertirlas a UTC antes de enviar.
    
    Seguridad:
      - Valida propiedad del dispositivo por tenant.
      - Mitigación CSV injection en export.
    """
    # Validar propiedad del dispositivo (tenant)
    owner = Device.query.filter_by(id=device_id, tenant_id=g.tenant_id).first()
    if not owner:
        return jsonify({"error": "Dispositivo no encontrado"}), 404

    # limit en {5,10,20}
    allowed_limits = {5, 10, 20}
    limit = request.args.get("limit", default=10, type=int)
    if limit not in allowed_limits:
        limit = 10

    # Filtros por rango de tiempo (ISO 8601; robusto)
    def _parse_iso(s: str):
        if not s:
            return None
        try:
            s = s.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None

    fecha_inicio = _parse_iso(request.args.get("fecha_inicio"))
    fecha_fin = _parse_iso(request.args.get("fecha_fin"))

    # Query aislada por tenant y device
    q = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
    if fecha_inicio:
        q = q.filter(LogEntry.timestamp_equipo >= fecha_inicio)
    if fecha_fin:
        q = q.filter(LogEntry.timestamp_equipo <= fecha_fin)

    q = q.order_by(LogEntry.timestamp_equipo.desc())
    logs = q.limit(limit).all()

    export = request.args.get("export", "").lower().strip()
    if export == "csv":
        # Mitigación CSV injection: prefijar comilla simple si empieza con =, +, - o @
        def _csv_safe(s: str) -> str:
            if not s:
                return ""
            s = s.replace("\n", " ").strip()
            return "'" + s if s[0] in ("=", "+", "-", "@") else s

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["timestamp_equipo", "device_id", "raw_log"])
        for l in logs:
            writer.writerow([
                l.timestamp_equipo.isoformat() if l.timestamp_equipo else "",
                l.device_id,
                _csv_safe(l.raw_log)
            ])
        csv_data = buf.getvalue()
        buf.close()
        filename = f"logs_device_{device_id}.csv"
        return Response(
            csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    if export == "pdf":
        # TODO: Generar PDF (ReportLab o WeasyPrint) con encabezados y paginación.
        return jsonify({"todo": "PDF export pendiente"}), 501

    result = [{
        "id": l.id,
        "raw_log": l.raw_log,
        "log_level": l.log_level,
        "timestamp_equipo": l.timestamp_equipo.isoformat() if l.timestamp_equipo else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in logs]
    return jsonify(result), 200