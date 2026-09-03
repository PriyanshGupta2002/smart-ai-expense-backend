# import csv
# import io

# from enum import Enum
# from typing import Any

# from openpyxl import Workbook
# from copy import copy

# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import (
#     SimpleDocTemplate,
#     Table,
#     TableStyle,
#     Paragraph,
#     Spacer,
# )
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from datetime import date, datetime
# from decimal import Decimal
# from uuid import UUID


# class ExportFormat(str, Enum):
#     CSV = "csv"
#     XLSX = "xlsx"
#     PDF = "pdf"


# class ExportResult:
#     def __init__(
#         self,
#         content: bytes,
#         filename: str,
#         mime_type: str,
#     ):
#         self.content = content
#         self.filename = filename
#         self.mime_type = mime_type


# class ExportService:

#     def _csv(
#         self,
#         rows: list[dict[str, Any]],
#         filename: str,
#     ) -> ExportResult:

#         output = io.StringIO()

#         columns = list(rows[0].keys())

#         writer = csv.DictWriter(
#             output,
#             fieldnames=columns,
#         )

#         writer.writeheader()

#         for row in rows:
#             writer.writerow(row)

#         content = output.getvalue().encode("utf-8-sig")

#         return ExportResult(
#             content=content,
#             filename=f"{filename}.csv",
#             mime_type="text/csv",
#         )

#     def _xlsx(
#         self,
#         rows: list[dict[str, Any]],
#         filename: str,
#     ) -> ExportResult:

#         workbook = Workbook()

#         sheet = workbook.active
#         sheet.title = "Expenses"

#         columns = list(rows[0].keys())

#         # Header
#         sheet.append(columns)

#         # Rows
#         for row in rows:
#             sheet.append([row.get(column) for column in columns])

#         # Header styling
#         for cell in sheet[1]:
#             font = copy(cell.font)
#             font.bold = True
#             cell.font = font

#         # Reasonable column widths
#         for column_cells in sheet.columns:

#             max_length = 0

#             column_letter = column_cells[0].column_letter

#             for cell in column_cells:
#                 value = str(cell.value or "")
#                 max_length = max(
#                     max_length,
#                     len(value),
#                 )

#             sheet.column_dimensions[column_letter].width = min(
#                 max_length + 3,
#                 50,
#             )

#         output = io.BytesIO()

#         workbook.save(output)

#         return ExportResult(
#             content=output.getvalue(),
#             filename=f"{filename}.xlsx",
#             mime_type=(
#                 "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
#             ),
#         )

#     def _pdf(
#         self,
#         rows: list[dict[str, Any]],
#         filename: str,
#         title: str | None = None,
#     ) -> ExportResult:

#         output = io.BytesIO()

#         document = SimpleDocTemplate(
#             output,
#             pagesize=A4,
#             rightMargin=30,
#             leftMargin=30,
#             topMargin=30,
#             bottomMargin=30,
#         )

#         styles = getSampleStyleSheet()

#         elements = []

#         if title:
#             elements.append(
#                 Paragraph(
#                     title,
#                     styles["Title"],
#                 )
#             )

#             elements.append(Spacer(1, 16))

#         columns = list(rows[0].keys())

#         table_data = [[self._format_column(column) for column in columns]]

#         for row in rows:
#             table_data.append([str(row.get(column) or "") for column in columns])

#         table = Table(
#             table_data,
#             repeatRows=1,
#         )

#         table.setStyle(
#             TableStyle(
#                 [
#                     (
#                         "BACKGROUND",
#                         (0, 0),
#                         (-1, 0),
#                         colors.lightgrey,
#                     ),
#                     (
#                         "FONTNAME",
#                         (0, 0),
#                         (-1, 0),
#                         "Helvetica-Bold",
#                     ),
#                     (
#                         "GRID",
#                         (0, 0),
#                         (-1, -1),
#                         0.5,
#                         colors.grey,
#                     ),
#                     (
#                         "VALIGN",
#                         (0, 0),
#                         (-1, -1),
#                         "TOP",
#                     ),
#                     (
#                         "FONTSIZE",
#                         (0, 0),
#                         (-1, -1),
#                         8,
#                     ),
#                     (
#                         "BOTTOMPADDING",
#                         (0, 0),
#                         (-1, 0),
#                         8,
#                     ),
#                 ]
#             )
#         )

#         elements.append(table)

#         document.build(elements)

#         return ExportResult(
#             content=output.getvalue(),
#             filename=f"{filename}.pdf",
#             mime_type="application/pdf",
#         )

#     @staticmethod
#     def normalize_value(value):

#         if value is None:
#             return ""

#         if isinstance(value, Decimal):
#             return float(value)

#         if isinstance(value, datetime):
#             return value.isoformat()

#         if isinstance(value, date):
#             return value.isoformat()

#         if isinstance(value, UUID):
#             return str(value)

#         return value

#     def normalize_rows(
#         self,
#         rows: list[dict],
#     ) -> list[dict]:

#         return [
#             {key: self.normalize_value(value) for key, value in row.items()}
#             for row in rows
#         ]

#     @staticmethod
#     def _format_column(value: str) -> str:
#         return value.replace("_", " ").title()

#     def generate(
#         self,
#         *,
#         rows: list[dict[str, Any]],
#         format: ExportFormat,
#         filename: str,
#         title: str | None = None,
#     ) -> ExportResult:

#         if not rows:
#             raise ValueError("Cannot export empty data.")

#         if format == ExportFormat.CSV:
#             return self._csv(rows, filename)

#         if format == ExportFormat.XLSX:
#             return self._xlsx(rows, filename)

#         if format == ExportFormat.PDF:
#             return self._pdf(
#                 rows,
#                 filename,
#                 title=title,
#             )

#         raise ValueError(f"Unsupported export format: {format}")


# export_service = ExportService()


import csv
import io

from copy import copy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from openpyxl import Workbook

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


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

    # ==========================================
    # EXPENSE AI THEME
    # ==========================================

    PRIMARY = HexColor("#4F46E5")
    PRIMARY_DARK = HexColor("#3730A3")

    BACKGROUND = HexColor("#FFFFFF")
    FOREGROUND = HexColor("#27272A")

    MUTED = HexColor("#F4F4F5")
    MUTED_FOREGROUND = HexColor("#71717A")

    BORDER = HexColor("#E4E4E7")

    TABLE_HEADER = HexColor("#F4F4F5")

    SUCCESS = HexColor("#16A34A")

    # ==========================================
    # CSV
    # ==========================================

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

    # ==========================================
    # XLSX
    # ==========================================

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
        sheet.append([self._format_column(column) for column in columns])

        # Rows
        for row in rows:
            sheet.append([row.get(column) for column in columns])

        # Header styling
        for cell in sheet[1]:
            font = copy(cell.font)
            font.bold = True
            cell.font = font

        # Freeze header
        sheet.freeze_panes = "A2"

        # Column widths
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

    # ==========================================
    # PDF
    # ==========================================

    def _pdf(
        self,
        rows: list[dict[str, Any]],
        filename: str,
        title: str | None = None,
        logo_path: str | None = None,
    ) -> ExportResult:

        output = io.BytesIO()

        # --------------------------------------
        # LANDSCAPE A4
        # --------------------------------------

        page_width, page_height = landscape(A4)

        document = SimpleDocTemplate(
            output,
            pagesize=landscape(A4),
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=title or "Expense AI Report",
            author="Expense AI",
        )

        # --------------------------------------
        # STYLES
        # --------------------------------------

        styles = getSampleStyleSheet()

        brand_style = ParagraphStyle(
            "Brand",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=self.PRIMARY,
            alignment=TA_LEFT,
            spaceAfter=2,
        )

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=self.FOREGROUND,
            alignment=TA_LEFT,
        )

        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=self.MUTED_FOREGROUND,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=self.FOREGROUND,
        )

        table_body_style = ParagraphStyle(
            "TableBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=self.FOREGROUND,
        )

        amount_style = ParagraphStyle(
            "Amount",
            parent=table_body_style,
            alignment=TA_RIGHT,
            fontName="Helvetica-Bold",
        )

        summary_label_style = ParagraphStyle(
            "SummaryLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=self.MUTED_FOREGROUND,
        )

        summary_value_style = ParagraphStyle(
            "SummaryValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=self.FOREGROUND,
        )

        # --------------------------------------
        # HELPERS
        # --------------------------------------

        def paragraph(
            value: Any,
            style: ParagraphStyle,
        ):
            return Paragraph(
                self._escape(str(value or "")),
                style,
            )

        # --------------------------------------
        # CALCULATE TOTAL
        # --------------------------------------

        total = Decimal("0")

        for row in rows:

            amount = row.get("amount")

            if amount is None:
                continue

            try:
                total += Decimal(str(amount))
            except Exception:
                pass

        # --------------------------------------
        # CURRENCY
        # --------------------------------------

        currencies = []

        for row in rows:

            currency = row.get("currency")

            if currency and currency not in currencies:
                currencies.append(currency)

        currency_text = ", ".join(currencies) if currencies else ""

        # --------------------------------------
        # HEADER
        # --------------------------------------

        elements = []

        # Optional logo
        if logo_path:

            try:

                logo = Image(
                    logo_path,
                    width=32 * mm,
                    height=10 * mm,
                    kind="proportional",
                )

                elements.append(logo)
                elements.append(Spacer(1, 4 * mm))

            except Exception:
                # If logo cannot be loaded,
                # simply continue with text branding.
                pass

        elements.append(
            paragraph(
                "Expense AI",
                brand_style,
            )
        )

        elements.append(Spacer(1, 2 * mm))

        elements.append(
            paragraph(
                title or "Expense Report",
                title_style,
            )
        )

        elements.append(Spacer(1, 1.5 * mm))

        elements.append(
            paragraph(
                (f"Generated on " f"{datetime.now().strftime('%d %b %Y, %I:%M %p')}"),
                subtitle_style,
            )
        )

        elements.append(Spacer(1, 7 * mm))

        # --------------------------------------
        # SUMMARY CARDS
        # --------------------------------------

        summary_data = [
            [
                paragraph(
                    "TOTAL SPENT",
                    summary_label_style,
                ),
                paragraph(
                    "TRANSACTIONS",
                    summary_label_style,
                ),
                paragraph(
                    "CURRENCY",
                    summary_label_style,
                ),
            ],
            [
                paragraph(
                    f"{currency_text} {total:,.2f}",
                    summary_value_style,
                ),
                paragraph(
                    f"{len(rows):,}",
                    summary_value_style,
                ),
                paragraph(
                    currency_text or "—",
                    summary_value_style,
                ),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                245 * mm,
                100 * mm,
                100 * mm,
            ],
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        self.MUTED,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        self.BORDER,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        self.BORDER,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        elements.append(summary_table)

        elements.append(Spacer(1, 8 * mm))

        # --------------------------------------
        # TABLE
        # --------------------------------------

        columns = list(rows[0].keys())

        # Human readable headers
        headers = [self._format_column(column) for column in columns]

        table_data = [
            [
                paragraph(
                    header,
                    table_header_style,
                )
                for header in headers
            ]
        ]

        # --------------------------------------
        # TABLE ROWS
        # --------------------------------------

        for row in rows:

            table_row = []

            for column in columns:

                value = row.get(column)

                # Date formatting
                if isinstance(value, datetime):

                    value = value.strftime("%d %b %Y, %I:%M %p")

                elif isinstance(value, date):

                    value = value.strftime("%d %b %Y")

                # Amount formatting
                if column == "amount":

                    if value is not None:

                        try:

                            value = f"{Decimal(str(value)):,.2f}"

                        except Exception:
                            pass

                    table_row.append(
                        paragraph(
                            value,
                            amount_style,
                        )
                    )

                else:

                    table_row.append(
                        paragraph(
                            value,
                            table_body_style,
                        )
                    )

            table_data.append(table_row)

        # --------------------------------------
        # COLUMN WIDTHS
        # --------------------------------------

        # Specifically control widths so that
        # amount NEVER gets pushed outside page.

        width_map = {
            "date": 35 * mm,
            "merchant": 85 * mm,
            "category": 32 * mm,
            "payment_method": 35 * mm,
            "amount": 32 * mm,
            "currency": 25 * mm,
        }

        available_width = page_width - document.leftMargin - document.rightMargin

        column_widths = []

        for column in columns:

            column_widths.append(
                width_map.get(
                    column,
                    35 * mm,
                )
            )

        # Scale widths if necessary
        total_width = sum(column_widths)

        if total_width > available_width:

            scale = available_width / total_width

            column_widths = [width * scale for width in column_widths]

        table = Table(
            table_data,
            colWidths=column_widths,
            repeatRows=1,
            splitByRow=1,
            hAlign="LEFT",
        )

        # --------------------------------------
        # TABLE STYLING
        # --------------------------------------

        table.setStyle(
            TableStyle(
                [
                    # Header
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        self.TABLE_HEADER,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        self.FOREGROUND,
                    ),
                    # Header bottom border
                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, 0),
                        1,
                        self.PRIMARY,
                    ),
                    # Grid
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        self.BORDER,
                    ),
                    # Alignment
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    # Padding
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    # Alternate rows
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            HexColor("#FAFAFA"),
                        ],
                    ),
                ]
            )
        )

        elements.append(table)

        # --------------------------------------
        # FOOTER
        # --------------------------------------

        def draw_footer(canvas, doc):

            canvas.saveState()

            canvas.setStrokeColor(self.BORDER)

            canvas.line(
                document.leftMargin,
                10 * mm,
                page_width - document.rightMargin,
                10 * mm,
            )

            canvas.setFont(
                "Helvetica",
                7,
            )

            canvas.setFillColor(self.MUTED_FOREGROUND)

            canvas.drawString(
                document.leftMargin,
                6 * mm,
                "Expense AI • Personal Expense Report",
            )

            canvas.drawRightString(
                page_width - document.rightMargin,
                6 * mm,
                f"Page {doc.page}",
            )

            canvas.restoreState()

        # --------------------------------------
        # BUILD PDF
        # --------------------------------------

        document.build(
            elements,
            onFirstPage=draw_footer,
            onLaterPages=draw_footer,
        )

        return ExportResult(
            content=output.getvalue(),
            filename=f"{filename}.pdf",
            mime_type="application/pdf",
        )

    # ==========================================
    # NORMALIZATION
    # ==========================================

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

    # ==========================================
    # HELPERS
    # ==========================================

    @staticmethod
    def _format_column(
        value: str,
    ) -> str:

        return value.replace("_", " ").title()

    @staticmethod
    def _escape(
        value: str,
    ) -> str:

        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # ==========================================
    # GENERATE
    # ==========================================

    def generate(
        self,
        *,
        rows: list[dict[str, Any]],
        format: ExportFormat,
        filename: str,
        title: str | None = None,
        logo_path: str | None = None,
    ) -> ExportResult:

        if not rows:
            raise ValueError("Cannot export empty data.")

        if format == ExportFormat.CSV:

            return self._csv(
                rows,
                filename,
            )

        if format == ExportFormat.XLSX:

            return self._xlsx(
                rows,
                filename,
            )

        if format == ExportFormat.PDF:

            return self._pdf(
                rows,
                filename,
                title=title,
                logo_path=logo_path,
            )

        raise ValueError(f"Unsupported format: {format}")


export_service = ExportService()
