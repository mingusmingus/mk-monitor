"""
Utilidad de exportación a PDF para logs.

- Genera un PDF con encabezado (tenant, dispositivo, rango de fechas, total registros)
  y tabla paginada (Fecha UTC, Device, Topic, Message truncado).
- Límite máximo de filas configurable vía entorno LOG_PDF_MAX_ROWS (default 5000).

Uso:
  bytes_pdf = generate_logs_pdf(tenant_name, device, logs, fecha_inicio, fecha_fin)

Notas:
- Evita dependencias nativas: usa ReportLab (pure Python).
- La paginación la maneja ReportLab al desbordar contenido.
"""
from __future__ import annotations

import os
from io import BytesIO
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

from ..models.device import Device
from ..models.log_entry import LogEntry


def _split_topic_and_message(raw_log: str) -> Tuple[str, str]:
    """
    Extrae [topic] y el resto del mensaje si viene con ese prefijo.
    Ejemplos:
      "[system,info] router logged in" -> ("system,info", "router logged in")
      "pppoe reconnect" -> ("", "pppoe reconnect")
    """
    raw = (raw_log or "").strip()
    if raw.startswith("["):
        try:
            end = raw.index("]")
            topic = raw[1:end].strip()
            msg = raw[end + 1 :].strip()
            return topic, msg
        except ValueError:
            pass
    return "", raw


def generate_logs_pdf(
    tenant_name: str,
    device: Device,
    logs: List[LogEntry],
    fecha_inicio: Optional[str],
    fecha_fin: Optional[str],
) -> bytes:
    """
    Genera un PDF con encabezado y tabla de logs.

    Args:
      tenant_name: Nombre del tenant.
      device: Instancia Device (para name/ip).
      logs: Lista de LogEntry ya filtrados.
      fecha_inicio: ISO string (UTC) o None.
      fecha_fin: ISO string (UTC) o None.

    Returns:
      bytes del PDF listo para respuesta HTTP.
    """
    max_rows = int(os.getenv("LOG_PDF_MAX_ROWS", "5000"))
    rows = logs[:max_rows]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Logs {device.name}",
    )

    styles = getSampleStyleSheet()
    story = []

    # Encabezado
    header = Paragraph(f"<b>mk-monitor · Logs</b>", styles["Title"])
    sub = Paragraph(
        f"Tenant: <b>{tenant_name or 'N/A'}</b> &nbsp;&nbsp; "
        f"Device: <b>{device.name}</b> (IP: {device.ip_address})",
        styles["Normal"],
    )
    rango = Paragraph(
        f"Rango (UTC): <b>{fecha_inicio or '—'}</b> → <b>{fecha_fin or '—'}</b> &nbsp;&nbsp; "
        f"Total registros: <b>{len(rows)}</b>",
        styles["Normal"],
    )

    story.extend([header, Spacer(1, 6), sub, rango, Spacer(1, 10)])

    # Tabla
    data = [["Fecha (UTC)", "Device", "Topic", "Message"]]
    for l in rows:
        ts = l.timestamp_equipo.isoformat() if l.timestamp_equipo else ""
        topic, msg = _split_topic_and_message(l.raw_log)
        # Truncado defensivo
        max_msg_len = int(os.getenv("LOG_PDF_MSG_TRUNC", "200"))
        if len(msg) > max_msg_len:
            msg = msg[: max_msg_len - 1] + "…"
        data.append([ts, f"{device.name}#{device.id}", topic, msg])

    table = Table(data, colWidths=[40 * mm, 40 * mm, 40 * mm, 60 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes