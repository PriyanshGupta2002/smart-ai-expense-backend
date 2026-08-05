import re

from app.ai.receipt.state import ReceiptState

INVOICE_KEYWORDS = {
    "invoice",
    "invoice no",
    "gstin",
    "hsn",
    "cgst",
    "sgst",
    "igst",
    "tax invoice",
    "purchase order",
}


def document_analysis_node(
    state: ReceiptState,
):

    text = state["ocr_text"].lower()

    blocks = state["raw_ocr"]

    score = 0

    # --------------------------------------------------
    # OCR Density
    # --------------------------------------------------

    if len(blocks) > 120:
        score += 2

    elif len(blocks) > 80:
        score += 1

    # --------------------------------------------------
    # Invoice keywords
    # --------------------------------------------------

    matches = sum(keyword in text for keyword in INVOICE_KEYWORDS)

    score += matches

    # --------------------------------------------------
    # Multiple pages
    # --------------------------------------------------

    if len(state["image_paths"]) > 1:
        score += 2

    # --------------------------------------------------
    # Long document
    # --------------------------------------------------

    if len(text) > 4000:
        score += 2

    elif len(text) > 2500:
        score += 1

    # --------------------------------------------------

    is_complex = score >= 4

    return {
        "complexity_score": score,
        "is_complex": is_complex,
    }
