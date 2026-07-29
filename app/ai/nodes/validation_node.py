from langchain_core.messages import HumanMessage, SystemMessage
from app.ai.receipt.state import ReceiptState
from app.ai.receipt.schemas import ReceiptExtraction, ValidationResult


def validation_node(state: ReceiptState):
    receipt = state["extracted_receipt"]

    if receipt is None:
        return {
            "validation": ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                status="INVALID",
                retry_from="extraction",
                errors=["Extracted receipt is missing"],
            )
        }

    warnings: list[str] = []
    errors: list[str] = []

    ocr_issues: list[str] = []
    extraction_issues: list[str] = []

    # --------------------------------------------------
    # 1. OCR quality
    # --------------------------------------------------

    raw_ocr = state.get("raw_ocr", [])

    if raw_ocr:
        avg_ocr_confidence = sum(block.confidence for block in raw_ocr) / len(raw_ocr)

        if avg_ocr_confidence < 0.80:
            message = f"Low OCR confidence: " f"{avg_ocr_confidence:.2f}"

            warnings.append(message)
            ocr_issues.append(message)

    else:
        avg_ocr_confidence = 0.0

        message = "OCR output is missing"

        errors.append(message)
        ocr_issues.append(message)

    # --------------------------------------------------
    # 2. Required extracted information
    # --------------------------------------------------

    if not receipt.merchant.name:
        message = "Merchant name is missing"

        warnings.append(message)
        extraction_issues.append(message)

    if receipt.totals.total is None:
        message = "Receipt total is missing"

        errors.append(message)
        extraction_issues.append(message)

    if receipt.totals.currency is None:
        message = "Currency could not be determined"

        warnings.append(message)
        extraction_issues.append(message)

    if receipt.purchase_datetime is None:
        message = "Purchase date/time is missing"

        warnings.append(message)
        extraction_issues.append(message)

    if not receipt.items:
        message = "No receipt items were extracted"

        warnings.append(message)
        extraction_issues.append(message)

    # --------------------------------------------------
    # 3. Receipt total consistency
    # --------------------------------------------------

    totals = receipt.totals

    if totals.subtotal is not None and totals.total is not None:
        tax = totals.tax or 0
        discount = totals.discount or 0

        expected_total = totals.subtotal + tax - discount

        if abs(expected_total - totals.total) > 0.02:
            message = (
                f"Total mismatch: calculated "
                f"{expected_total:.2f}, "
                f"extracted {totals.total:.2f}"
            )

            warnings.append(message)
            extraction_issues.append(message)

    # --------------------------------------------------
    # 4. Item/subtotal consistency
    # --------------------------------------------------

    item_prices = [
        item.total_price for item in receipt.items if item.total_price is not None
    ]

    if (
        item_prices
        and len(item_prices) == len(receipt.items)
        and totals.subtotal is not None
    ):
        calculated_subtotal = sum(item_prices)

        if abs(calculated_subtotal - totals.subtotal) > 0.02:
            message = (
                f"Item total mismatch: items sum to "
                f"{calculated_subtotal:.2f}, "
                f"subtotal is {totals.subtotal:.2f}"
            )

            warnings.append(message)
            extraction_issues.append(message)

    # --------------------------------------------------
    # 5. Determine validation status
    # --------------------------------------------------

    if errors:
        status = "INVALID"
        is_valid = False

    elif len(warnings) >= 3:
        status = "NEEDS_REVIEW"
        is_valid = False

    elif warnings:
        status = "LOW_CONFIDENCE"
        is_valid = True

    else:
        status = "VALID"
        is_valid = True

    # --------------------------------------------------
    # 6. Decide where retry should start
    # --------------------------------------------------

    if is_valid:
        retry_from = "none"

    elif ocr_issues:
        retry_from = "ocr"

    elif extraction_issues:
        retry_from = "extraction"

    else:
        retry_from = "none"

    # --------------------------------------------------
    # 7. Confidence
    # --------------------------------------------------

    confidence_score = max(
        0.0,
        min(1.0, avg_ocr_confidence - (len(warnings) * 0.05) - (len(errors) * 0.20)),
    )

    return {
        "validation": ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            status=status,
            retry_from=retry_from,
            warnings=warnings,
            errors=errors,
        )
    }
