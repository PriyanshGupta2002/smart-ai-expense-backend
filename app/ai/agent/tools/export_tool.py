from datetime import datetime
from typing import Literal

from langchain.tools import tool, ToolRuntime


from sqlalchemy import select

from app.ai.agent.context import ExpenseAgentContext
from app.models.receipt import Receipt
from app.services.export_services import (
    ExportFormat,
    ExportService,
)


@tool
def export_expenses(
    format: Literal["csv", "xlsx", "pdf"],
    runtime: ToolRuntime[ExpenseAgentContext],
    filename: str = "expenses",
    title: str | None = "Expense Report",
    category: str | None = None,
    merchant: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """
    Generate a downloadable expense report for the current user.

    Use this tool when the user asks to export, download,
    save, or generate expense data as CSV, Excel/XLSX, or PDF.

    Filters:
    - category: filter by expense category
    - merchant: filter by merchant name
    - start_date: include expenses on or after this datetime
    - end_date: include expenses before this datetime

    Only apply filters explicitly requested or clearly implied
    by the user's request.
    """

    db = runtime.context.db
    user_id = runtime.context.user_id
    storage = runtime.context.storage

    filters = [
        Receipt.user_id == user_id,
        Receipt.processing_status == "COMPLETED",
    ]

    if category:
        filters.append(Receipt.expense_type == category)

    if merchant:
        filters.append(Receipt.merchant_name.ilike(f"%{merchant}%"))

    if start_date:
        filters.append(Receipt.purchase_datetime >= start_date)

    if end_date:
        filters.append(Receipt.purchase_datetime < end_date)

    stmt = (
        select(
            Receipt.purchase_datetime.label("date"),
            Receipt.merchant_name.label("merchant"),
            Receipt.expense_type.label("category"),
            Receipt.payment_method.label("payment_method"),
            Receipt.total.label("amount"),
            Receipt.currency.label("currency"),
        )
        .where(*filters)
        .order_by(Receipt.purchase_datetime.desc())
    )

    result = db.execute(stmt)

    rows = [dict(row._mapping) for row in result.all()]

    if not rows:
        return {
            "success": False,
            "message": "No expenses found matching the requested filters.",
        }

    service = ExportService()

    export = service.generate(
        rows=rows,
        format=ExportFormat(format),
        filename=filename,
        title=title,
    )

    uploaded = storage.upload(
        content=export.content,
        filename=export.filename,
        folder=f"/exports/{user_id}",
    )
    return {
        "success": True,
        "artifact": {
            "name": export.filename,
            "mime_type": export.mime_type,
            "url": uploaded["url"],
            "file_id": uploaded["file_id"],
            "size": len(export.content),
        },
    }
