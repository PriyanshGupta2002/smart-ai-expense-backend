from typing import Literal

from app.ai.receipt.state import ReceiptState


def route_after_document_analysis(
    state: ReceiptState,
) -> Literal[
    "simple",
    "complex",
]:

    if state["is_complex"]:
        return "complex"

    return "simple"
