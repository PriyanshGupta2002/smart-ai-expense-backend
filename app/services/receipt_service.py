import os
import tempfile

from decimal import Decimal

from fastapi import (
    HTTPException,
    UploadFile,
)

import math
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from app.ai.receipt.graph import workflow
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.user import User
from app.services.imagekit_service import ImageKitService
from app.utils.date_range import DashboardPeriod, get_period_range
from app.services.insight_cache_service import InsightCacheService

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

MAX_FILE_SIZE = 10 * 1024 * 1024


def to_decimal(value):
    if value is None:
        return None

    return Decimal(str(value))


class ReceiptService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.imagekit = ImageKitService()

    def process_receipt(
        self,
        file: UploadFile,
        user: User,
    ) -> Receipt:

        # =====================================
        # Validate
        # =====================================

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=415,
                detail="Unsupported image type",
            )

        original_filename = file.filename or "receipt.jpg"

        extension = os.path.splitext(original_filename)[1].lower()

        temp_path = None
        imagekit_result = None
        receipt = None

        try:

            # =====================================
            # Temporary file
            # =====================================

            size = 0

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
            ) as temp:

                temp_path = temp.name

                while True:
                    chunk = file.file.read(1024 * 1024)

                    if not chunk:
                        break

                    size += len(chunk)

                    if size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="Image exceeds 10 MB",
                        )

                    temp.write(chunk)

            # =====================================
            # ImageKit
            # =====================================

            imagekit_result = self.imagekit.upload_receipt(
                file_path=temp_path,
                user_id=user.id,
                original_filename=original_filename,
            )

            # =====================================
            # Create processing receipt
            # =====================================

            receipt = Receipt(
                user_id=user.id,
                imagekit_file_id=(imagekit_result.file_id),
                image_url=(imagekit_result.url),
                image_path=(imagekit_result.file_path),
                original_filename=original_filename,
                processing_status="PROCESSING",
            )

            self.db.add(receipt)
            self.db.commit()
            self.db.refresh(receipt)

            # =====================================
            # AI Workflow
            # =====================================

            result = workflow.invoke(
                {
                    "file_path": temp_path,
                    "content_type": file.content_type,
                    "image_paths": [],
                    "retry_count": 0,
                    "max_retries": 3,
                    "warnings": [],
                    "errors": [],
                }
            )

            normalized = result.get("normalized_receipt")

            classification = result.get("classification")

            validation = result.get("validation")

            if normalized is None:
                raise RuntimeError("Receipt extraction failed")

            # =====================================
            # Merchant
            # =====================================

            receipt.merchant_name = normalized.merchant.name

            receipt.merchant_address = normalized.merchant.address

            receipt.merchant_phone = normalized.merchant.phone

            receipt.gst_number = normalized.merchant.gst_number

            # =====================================
            # Receipt information
            # =====================================

            receipt.purchase_datetime = normalized.purchase_datetime

            receipt.receipt_number = normalized.receipt_number

            # =====================================
            # Totals
            # =====================================

            receipt.subtotal = to_decimal(normalized.totals.subtotal)

            receipt.tax = to_decimal(normalized.totals.tax)

            receipt.discount = to_decimal(normalized.totals.discount)

            receipt.total = to_decimal(normalized.totals.total)

            receipt.currency = normalized.totals.currency

            # =====================================
            # Payment
            # =====================================

            receipt.payment_method = normalized.payment.method

            receipt.payment_last_four = normalized.payment.last_four

            receipt.notes = normalized.notes

            # =====================================
            # Classification
            # =====================================

            if classification:

                receipt.expense_type = classification.expense_type

                receipt.classification_confidence = to_decimal(
                    classification.confidence
                )

            # =====================================
            # Validation
            # =====================================

            if validation:

                receipt.validation_status = validation.status

                receipt.validation_confidence = to_decimal(validation.confidence_score)

            # =====================================
            # Items
            # =====================================

            for item in normalized.items:

                db_item = ReceiptItem(
                    receipt_id=receipt.id,
                    name=item.name,
                    quantity=to_decimal(item.quantity),
                    unit_price=to_decimal(item.unit_price),
                    total_price=to_decimal(item.total_price),
                )

                self.db.add(db_item)

            # =====================================
            # Status
            # =====================================

            if validation and validation.status == "NEEDS_REVIEW":
                receipt.processing_status = "NEEDS_REVIEW"

            else:
                receipt.processing_status = "COMPLETED"

            self.db.commit()
            self.db.refresh(receipt)
            InsightCacheService.invalidate(user_id=user.id)

            return receipt

        except HTTPException:
            self.db.rollback()

            if imagekit_result is not None and receipt is None:
                try:
                    self.imagekit.delete_file(imagekit_result.file_id)
                except Exception:
                    pass

            raise

        except Exception as exc:

            self.db.rollback()

            # Receipt exists → preserve it
            # and mark processing failure.

            if receipt is not None:

                receipt.processing_status = "FAILED"
                receipt.processing_error = str(exc)

                self.db.add(receipt)
                self.db.commit()

            # Upload succeeded but DB receipt
            # wasn't created → clean ImageKit.

            elif imagekit_result is not None:

                try:
                    self.imagekit.delete_file(imagekit_result.file_id)
                except Exception:
                    pass

            raise HTTPException(
                status_code=500,
                detail="Receipt processing failed",
            )

        finally:

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def get_receipts(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        period: DashboardPeriod | None = None,
        category: str | None = None,
        search: str | None = None,
        status: str | None = None,
    ):

        filters = [
            Receipt.user_id == user.id,
        ]

        # ----------------------------
        # Period
        # ----------------------------

        if period:
            start_date, end_date = get_period_range(period)

            if start_date:
                filters.append(Receipt.purchase_datetime >= start_date)

            filters.append(Receipt.purchase_datetime < end_date)

        # ----------------------------
        # Category
        # ----------------------------

        if category:
            filters.append(Receipt.expense_type == category)

        # ----------------------------
        # Status
        # ----------------------------

        if status:
            filters.append(Receipt.processing_status == status)

        # ----------------------------
        # Search
        # ----------------------------

        if search:
            search_value = f"%{search.strip()}%"

            filters.append(
                or_(
                    Receipt.merchant_name.ilike(search_value),
                    Receipt.receipt_number.ilike(search_value),
                )
            )

        # ----------------------------
        # Count
        # ----------------------------

        total = self.db.scalar(select(func.count(Receipt.id)).where(*filters)) or 0

        # ----------------------------
        # Data
        # ----------------------------

        stmt = (
            select(Receipt)
            .where(*filters)
            .order_by(Receipt.purchase_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        receipts = self.db.scalars(stmt).all()

        return {
            "items": receipts,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": math.ceil(total / page_size),
        }
