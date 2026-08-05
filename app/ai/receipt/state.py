from typing import TypedDict

from app.ai.receipt.schemas import (
    Classification,
    OCRBlock,
    OCRRow,
    ReceiptExtraction,
    ValidationResult,
)

# class ReceiptState(TypedDict):

#     # Original uploaded file
#     file_path: str

#     # MIME type
#     content_type: str

#     # Prepared images for OCR
#     image_paths: list[str]

#     # OCR
#     raw_ocr: list[OCRBlock]
#     ocr_text: str

#     # Layout
#     layout: list[OCRRow]
#     layout_text: str | None

#     # LLM Extraction
#     extracted_receipt: ReceiptExtraction | None

#     # Classification
#     classification: Classification | None

#     # Validation
#     validation: ValidationResult | None

#     # Normalization
#     normalized_receipt: ReceiptExtraction | None

#     # Retry
#     retry_count: int
#     max_retries: int


#     # Metadata
#     warnings: list[str]
#     errors: list[str]
class ReceiptState(TypedDict):

    file_path: str
    content_type: str

    image_paths: list[str]

    raw_ocr: list[OCRBlock]
    ocr_text: str

    is_complex: bool
    complexity_score: int

    markdown_text: str | None
    document_json: list[dict] | None

    extracted_receipt: ReceiptExtraction | None

    classification: Classification | None

    validation: ValidationResult | None

    normalized_receipt: ReceiptExtraction | None

    retry_count: int
    max_retries: int

    warnings: list[str]
    errors: list[str]
