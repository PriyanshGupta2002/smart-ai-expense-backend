# file_processor.py

from app.ai.receipt.preprocessing.pdf_processor import (
    pdf_to_images,
)


def prepare_receipt_images(
    file_path: str,
    content_type: str,
) -> list[str]:

    if content_type == "application/pdf":
        return pdf_to_images(file_path)

    return [file_path]
