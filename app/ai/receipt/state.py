from typing import TypedDict

from app.ai.receipt.schemas import (
    Classification,
    OCRBlock,
    OCRRow,
    ReceiptExtraction,
    ValidationResult,
)


class ReceiptState(TypedDict):
    # Input
    image_path: str

    # OCR
    raw_ocr: list[OCRBlock]
    ocr_text: str

    # Layout
    layout: list[OCRRow]
    layout_text: str

    # Extraction
    extracted_receipt: ReceiptExtraction | None

    # Classification
    classification: Classification | None

    # Validation
    validation: ValidationResult | None

    # Final
    normalized_receipt: ReceiptExtraction | None

    # Retry
    retry_count: int
    max_retries: int

    # Execution
    warnings: list[str]
    errors: list[str]
