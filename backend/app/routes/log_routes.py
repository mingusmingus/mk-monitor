"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
"""
from flask import Blueprint, request, jsonify, g, Response
from ..auth.decorators import require_auth
from ..models.log_entry import LogEntry
from ..models.device import Device
from ..models.tenant import Tenant
from ..utils.export_pdf import generate_logs_pdf  # Ruta legacy (format/export)
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import logging
from datetime import datetime
import io, csv, os
from ..__init__ import limiter

log_bp = Blueprint("logs", __name__)
logger = logging.getLogger(__name__)

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

    # NUEVO: soporte formato=formato (pdf) y filtros 'query', 'from', 'to'
    formato = (request.args.get("formato") or "").lower().strip()
    search = request.args.get("query", default="", type=str).strip()

    def _parse_range_param(v: str):
        if not v:
            return None
        v = v.strip().replace("Z", "+00:00")
        for fmt_try in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(v, fmt_try)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None

    rango_inicio = _parse_range_param(request.args.get("from"))
    rango_fin = _parse_range_param(request.args.get("to"))

    # Selección de formato legacy existente (format/export)
    fmt = (request.args.get("format") or request.args.get("export") or "").lower().strip()

    # --- NUEVA RUTA PDF (prioridad sobre legacy) ---
    if formato == "pdf":
        q_new = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
        if rango_inicio:
            q_new = q_new.filter(LogEntry.timestamp_equipo >= rango_inicio)
        if rango_fin:
            q_new = q_new.filter(LogEntry.timestamp_equipo <= rango_fin)
        if search:
            q_new = q_new.filter(LogEntry.raw_log.ilike(f"%{search}%"))
        q_new = q_new.order_by(LogEntry.timestamp_equipo.desc())
        logs_new = q_new.all()

        pdf_bytes = _build_logs_pdf(logs_new, device_id)
        # Logging de auditoría (sin contenido del PDF)
        logger.info(
            "export_pdf form=formato tenant_id=%s device_id=%s count=%s", g.tenant_id, device_id, len(logs_new)
        )
        filename = f"device_{device_id}_logs_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

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
        logger.info(
            "export_pdf form=legacy tenant_id=%s device_id=%s count=%s", g.tenant_id, device_id, len(logs_pdf)
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


def _build_logs_pdf(logs, device_id: int) -> bytes:
    """Helper privado para construir PDF de logs.

    Requisitos:
      - Título: "Logs Dispositivo <device_id>" y fecha actual.
      - Tabla (timestamp_equipo | log_level | raw_log truncado a 120 chars).
      - Máx 45 filas por página (paginación manual).
      - Mensaje si lista vacía.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def _header(page_num: int):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, height - 25 * mm, f"Logs Dispositivo {device_id}")
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 20 * mm, height - 25 * mm, datetime.utcnow().strftime("UTC %Y-%m-%d %H:%M:%S"))
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, height - 30 * mm, f"Página {page_num}")
        # Encabezado de tabla
        c.setFont("Helvetica-Bold", 9)
        y_head = height - 40 * mm
        c.drawString(20 * mm, y_head, "Timestamp")
        c.drawString(60 * mm, y_head, "Nivel")
        c.drawString(85 * mm, y_head, "Mensaje")
        c.line(20 * mm, y_head - 2, width - 20 * mm, y_head - 2)
        return y_head - 6

    # Preparar datos
    rows_per_page = 45
    page = 1
    y = _header(page)
    c.setFont("Helvetica", 8)

    if not logs:
        c.drawString(20 * mm, y, "Sin datos para criterios especificados")
        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    for idx, l in enumerate(logs, 1):
        # Nueva página si se excede
        if (idx - 1) % rows_per_page == 0 and idx != 1:
            c.showPage()
            page += 1
            y = _header(page)
            c.setFont("Helvetica", 8)

        # Truncar mensaje
        raw = l.raw_log or ""
        if len(raw) > 120:
            raw = raw[:117] + "..."

        ts = l.timestamp_equipo.isoformat() if getattr(l, "timestamp_equipo", None) else ""
        lvl = l.log_level or "-"
        # Dibujar fila
        c.drawString(20 * mm, y, ts)
        c.drawString(60 * mm, y, lvl)
        c.drawString(85 * mm, y, raw)
        y -= 5 * mm
        if y < 20 * mm:  # margen inferior
            c.showPage()
            page += 1
            y = _header(page)
            c.setFont("Helvetica", 8)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf