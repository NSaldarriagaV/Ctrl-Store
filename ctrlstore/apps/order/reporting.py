from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO, StringIO
from typing import Iterable, Sequence

import csv

from django.utils import timezone
from decimal import Decimal
from typing import Any


class ReportGenerator(ABC):
    """
    Abstracción para la generación de reportes de ventas.
    La HU pide explícitamente que exista esta clase.
    """

    @abstractmethod
    def generate(self, rows: Sequence[dict]) -> bytes:
        """Recibe filas (lista de dicts) y devuelve los bytes del archivo."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        ...


class CsvReportGenerator(ReportGenerator):
    content_type = "text/csv"
    file_extension = "csv"

    def generate(self, rows: Sequence[dict]) -> bytes:
        if not rows:
            return b""

        output = StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        return output.getvalue().encode("utf-8")


# ---- PDF ----
# Requiere instalar reportlab:
#   pip install reportlab
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.pdfgen import canvas     # type: ignore


class PdfReportGenerator(ReportGenerator):
    content_type = "application/pdf"
    file_extension = "pdf"

    def generate(self, rows: Sequence[dict]) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        width, height = A4
        x = 40
        y = height - 50

        # Encabezado
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Reporte de ventas")
        y -= 25

        if not rows:
            c.setFont("Helvetica", 10)
            c.drawString(x, y, "No hay datos en el rango seleccionado.")
            c.showPage()
            c.save()
            return buffer.getvalue()

        # Cabeceras
        c.setFont("Helvetica-Bold", 10)
        fieldnames = list(rows[0].keys())
        for i, field in enumerate(fieldnames):
            c.drawString(x + i * 100, y, field)
        y -= 15

        # Filas
        c.setFont("Helvetica", 9)
        for row in rows:
            if y < 40:  # salto de página
                c.showPage()
                y = height - 50
                c.setFont("Helvetica-Bold", 10)
                for i, field in enumerate(fieldnames):
                    c.drawString(x + i * 100, y, field)
                y -= 15
                c.setFont("Helvetica", 9)

            for i, field in enumerate(fieldnames):
                text = str(row.get(field, ""))
                c.drawString(x + i * 100, y, text[:30])  # recortar un poco
            y -= 12

        c.showPage()
        c.save()
        return buffer.getvalue()


# ---- Excel ----
# Requiere instalar openpyxl:
#   pip install openpyxl
from openpyxl import Workbook  # type: ignore


class ExcelReportGenerator(ReportGenerator):
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    file_extension = "xlsx"

    def generate(self, rows: Sequence[dict]) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Ventas"

        if not rows:
            # Al menos dejamos la hoja vacía
            buffer = BytesIO()
            wb.save(buffer)
            return buffer.getvalue()

        fieldnames = list(rows[0].keys())
        # Cabeceras
        ws.append(fieldnames)
        # Filas
        for row in rows:
            ws.append([row.get(f) for f in fieldnames])

        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()




class SalesReportService:
    """
    Servicio que sabe cómo transformar Orders -> filas de reporte,
    pero no sabe nada del formato (PDF/Excel/CSV).
    Depende de la abstracción ReportGenerator.
    """

    def __init__(self, generator: ReportGenerator):
        self.generator = generator

    def build_rows(self, orders) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for o in orders:
            items_str = "; ".join(
                f"{it.product.name} x{it.quantity}" for it in o.items.all()
            )

            rows.append(
                {
                    "order_id": o.id,
                    "fecha": timezone.localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
                    "usuario": (o.user.get_full_name() or o.user.username) if o.user_id else "",
                    "email": o.user.email if o.user_id else "",
                    "total": str(o.total_amount or Decimal("0.00")),
                    "items": items_str,
                }
            )

        return rows

    def build_report(self, orders) -> bytes:
        rows = self.build_rows(orders)
        return self.generator.generate(rows)
