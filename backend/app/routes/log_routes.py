"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
"""
from flask import Blueprint, request, jsonify, g, Response
from ..auth.decorators import require_auth
from ..models.log_entry import LogEntry
from ..models.device import Device
from ..models.tenant import Tenant
from ..utils.export_pdf import generate_logs_pdf
from datetime import datetime
import io, csv, os
from ..__init__ import limiter

log_bp = Blueprint("logs", __name__)

@log_bp.get("/devices/<int:device_id>/logs")
@require_auth()
@limiter.limit("30/minute; 200/hour", override_defaults=False)
def device_logs(device_id: int):
    """
    Devuelve logs del dispositivo dentro del tenant.

    Query params:
      - limit (5|10|20; default 10) para JSON/CSV
      - fecha_inicio (ISO 8601 UTC)
      - fecha_fin (ISO 8601 UTC)
      - format: csv | pdf (preferido)
      - export: csv | pdf (compatibilidad legado)

    Nota importante (timezone - prioridad BAJA):
      Las fechas recibidas (fecha_inicio, fecha_fin) se interpretan en UTC.
      El campo timestamp_equipo se almacena y consulta como timezone-aware (UTC).

    Seguridad:
      - Valida propiedad del dispositivo por tenant.
      - Mitigación CSV injection en export.
    """
    # Validar propiedad del dispositivo (tenant)
    owner = Device.query.filter_by(id=device_id, tenant_id=g.tenant_id).first()
    if not owner:
        return jsonify({"error": "Dispositivo no encontrado"}), 404

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

    # Selección de formato (nuevo: format=csv|pdf; legacy: export=csv|pdf)
    fmt = (request.args.get("format") or request.args.get("export") or "").lower().strip()

    # Ruta PDF (permite mayor límite configurable)
    if fmt == "pdf":
        # Límite máximo PDF configurable (default 5000)
        max_rows = int(os.getenv("LOG_PDF_MAX_ROWS", "5000"))
        pdf_limit = request.args.get("limit", default=max_rows, type=int)
        if not isinstance(pdf_limit, int) or pdf_limit <= 0:
            pdf_limit = max_rows
        pdf_limit = min(pdf_limit, max_rows)

        q_pdf = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
        if fecha_inicio:
            q_pdf = q_pdf.filter(LogEntry.timestamp_equipo >= fecha_inicio)
        if fecha_fin:
            q_pdf = q_pdf.filter(LogEntry.timestamp_equipo <= fecha_fin)
        q_pdf = q_pdf.order_by(LogEntry.timestamp_equipo.desc())
        logs_pdf = q_pdf.limit(pdf_limit).all()

        # Tenant name para encabezado
        tenant = Tenant.query.filter_by(id=g.tenant_id).first()
        tenant_name = tenant.name if tenant else f"tenant#{g.tenant_id}"

        # Generar PDF
        pdf_bytes = generate_logs_pdf(
            tenant_name=tenant_name,
            device=owner,
            logs=logs_pdf,
            fecha_inicio=fecha_inicio.isoformat() if fecha_inicio else None,
            fecha_fin=fecha_fin.isoformat() if fecha_fin else None,
        )

        filename = f"logs_{datetime.utcnow().date().isoformat()}_device_{device_id}.pdf"
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # --- CSV y JSON (comportamiento existente) ---
    # limit en {5,10,20}
    allowed_limits = {5, 10, 20}
    limit = request.args.get("limit", default=10, type=int)
    if limit not in allowed_limits:
        limit = 10

    # Query aislada por tenant y device
    q = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
    if fecha_inicio:
        q = q.filter(LogEntry.timestamp_equipo >= fecha_inicio)
    if fecha_fin:
        q = q.filter(LogEntry.timestamp_equipo <= fecha_fin)

    q = q.order_by(LogEntry.timestamp_equipo.desc())
    logs = q.limit(limit).all()

    # CSV export (mantener comportamiento actual y compatibilidad con format=csv)
    export = request.args.get("export", "").lower().strip()
    if fmt == "csv":
        export = "csv"
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
            writer.writerow(
                [
                    l.timestamp_equipo.isoformat() if l.timestamp_equipo else "",
                    l.device_id,
                    _csv_safe(l.raw_log),
                ]
            )
        csv_data = buf.getvalue()
        buf.close()
        filename = f"logs_device_{device_id}.csv"
        return Response(
            csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    # Respuesta JSON
    result = [
        {
            "id": l.id,
            "raw_log": l.raw_log,
            "log_level": l.log_level,
            "timestamp_equipo": l.timestamp_equipo.isoformat() if l.timestamp_equipo else None,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
    return jsonify(result), 200