"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify, g, Response
from ..auth.decorators import require_auth
from ..models.log_entry import LogEntry
from datetime import datetime
import io, csv

log_bp = Blueprint("logs", __name__)

@log_bp.get("/devices/<int:device_id>/logs")
@require_auth()
def device_logs(device_id: int):
    """
    Query params:
      - limit (1..50)
      - fecha_inicio, fecha_fin (ISO 8601)
      - export: csv | pdf
    Devuelve logs del dispositivo dentro del tenant.
    """
    limit = request.args.get("limit", default=10, type=int)
    limit = min(max(limit, 1), 50)

    # Filtros por rango de tiempo (opcional)
    fecha_inicio_raw = request.args.get("fecha_inicio")
    fecha_fin_raw = request.args.get("fecha_fin")
    fecha_inicio = None
    fecha_fin = None
    try:
        if fecha_inicio_raw:
            fecha_inicio = datetime.fromisoformat(fecha_inicio_raw)
        if fecha_fin_raw:
            fecha_fin = datetime.fromisoformat(fecha_fin_raw)
    except Exception:
        # Ignorar formatos inválidos; en producción validar y devolver 400
        fecha_inicio = None
        fecha_fin = None

    q = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
    if fecha_inicio:
        q = q.filter(LogEntry.timestamp_equipo >= fecha_inicio)
    if fecha_fin:
        q = q.filter(LogEntry.timestamp_equipo <= fecha_fin)

    q = q.order_by(LogEntry.timestamp_equipo.desc())
    logs = q.limit(limit).all()

    export = request.args.get("export", "").lower().strip()
    if export == "csv":
        # TODO(security): Mitigar CSV injection prefijando comilla simple si el valor inicia con =, +, - o @
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