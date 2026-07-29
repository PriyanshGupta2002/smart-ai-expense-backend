from app.ai.receipt.state import ReceiptState


def retry_ocr(state: ReceiptState):
    return {"retry_count": state["retry_count"] + 1}


def retry_extraction(state: ReceiptState):
    return {"retry_count": state["retry_count"] + 1}
