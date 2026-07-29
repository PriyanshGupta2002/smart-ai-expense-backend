from app.ai.receipt.state import ReceiptState


def route_after_validation(state: ReceiptState) -> str:

    validation = state["validation"]

    if validation is None:
        return "failed"

    if validation.is_valid:
        return "normalize"

    if state["retry_count"] >= state["max_retries"]:
        return "failed"

    if validation.retry_from == "ocr":
        return "retry_ocr"

    if validation.retry_from == "extraction":
        return "retry_extraction"

    return "failed"
