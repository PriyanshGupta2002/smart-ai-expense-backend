import csv
import io

from enum import Enum
from typing import Any

from openpyxl import Workbook
from copy import copy

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class ExportResult:
    def __init__(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
    ):
        self.content = content
        self.filename = filename
        self.mime_type = mime_type


class ExportService:

    def _csv(
        self,
        rows: list[dict[str, Any]],
        filename: str,
    ) -> ExportResult:

        output = io.StringIO()

        columns = list(rows[0].keys())

        writer = csv.DictWriter(
            output,
            fieldnames=columns,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        content = output.getvalue().encode("utf-8-sig")

        return ExportResult(
            content=content,
            filename=f"{filename}.csv",
            mime_type="text/csv",
        )

    def _xlsx(
        self,
        rows: list[dict[str, Any]],
        filename: str,
    ) -> ExportResult:

        workbook = Workbook()

        sheet = workbook.active
        sheet.title = "Expenses"

        columns = list(rows[0].keys())

        # Header
        sheet.append(columns)

        # Rows
        for row in rows:
            sheet.append([row.get(column) for column in columns])

        # Header styling
        for cell in sheet[1]:
            font = copy(cell.font)
            font.bold = True
            cell.font = font

        # Reasonable column widths
        for column_cells in sheet.columns:

            max_length = 0

            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                value = str(cell.value or "")
                max_length = max(
                    max_length,
                    len(value),
                )

            sheet.column_dimensions[column_letter].width = min(
                max_length + 3,
                50,
            )

        output = io.BytesIO()

        workbook.save(output)

        return ExportResult(
            content=output.getvalue(),
            filename=f"{filename}.xlsx",
            mime_type=(
                "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
            ),
        )

    def _pdf(
        self,
        rows: list[dict[str, Any]],
        filename: str,
        title: str | None = None,
    ) -> ExportResult:

        output = io.BytesIO()

        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        styles = getSampleStyleSheet()

        elements = []

        if title:
            elements.append(
                Paragraph(
                    title,
                    styles["Title"],
                )
            )

            elements.append(Spacer(1, 16))

        columns = list(rows[0].keys())

        table_data = [[self._format_column(column) for column in columns]]

        for row in rows:
            table_data.append([str(row.get(column) or "") for column in columns])

        table = Table(
            table_data,
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        8,
                    ),
                ]
            )
        )

        elements.append(table)

        document.build(elements)

        return ExportResult(
            content=output.getvalue(),
            filename=f"{filename}.pdf",
            mime_type="application/pdf",
        )

    @staticmethod
    def normalize_value(value):

        if value is None:
            return ""

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, UUID):
            return str(value)

        return value

    def normalize_rows(
        self,
        rows: list[dict],
    ) -> list[dict]:

        return [
            {key: self.normalize_value(value) for key, value in row.items()}
            for row in rows
        ]

    @staticmethod
    def _format_column(value: str) -> str:
        return value.replace("_", " ").title()

    def generate(
        self,
        *,
        rows: list[dict[str, Any]],
        format: ExportFormat,
        filename: str,
        title: str | None = None,
    ) -> ExportResult:

        if not rows:
            raise ValueError("Cannot export empty data.")

        if format == ExportFormat.CSV:
            return self._csv(rows, filename)

        if format == ExportFormat.XLSX:
            return self._xlsx(rows, filename)

        if format == ExportFormat.PDF:
            return self._pdf(
                rows,
                filename,
                title=title,
            )

        raise ValueError(f"Unsupported export format: {format}")


export_service = ExportService()
