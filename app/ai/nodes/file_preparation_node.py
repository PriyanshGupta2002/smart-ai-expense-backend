from app.ai.receipt.state import ReceiptState

from app.ai.receipt.preprocessing.file_processor import (
    prepare_receipt_images,
)


def file_preparation_node(
    state: ReceiptState,
):

    image_paths = prepare_receipt_images(
        file_path=state["file_path"],
        content_type=state["content_type"],
    )

    if not image_paths:
        raise ValueError("Could not prepare receipt for OCR")

    return {
        "image_paths": image_paths,
    }
