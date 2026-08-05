# from langchain_openrouter import ChatOpenRouter
# from dotenv import load_dotenv
# from app.ai.receipt.schemas import ReceiptExtraction
# from app.ai.receipt.state import ReceiptState
# from app.ai.prompts.prompt import RECEIPT_EXTRACTION_PROMPT

# load_dotenv()


# extractor = ChatOpenRouter(model="openai/gpt-5-mini").with_structured_output(
#     ReceiptExtraction
# )


# def extraction_node(state: ReceiptState):

#     layout_text = state["layout_text"]
#     ocr_text = state["ocr_text"]

#     result = extractor.invoke(
#         [
#             {
#                 "role": "system",
#                 "content": RECEIPT_EXTRACTION_PROMPT,
#             },
#             {
#                 "role": "user",
#                 "content": f"""
# Extract the complete receipt/invoice below.

# IMPORTANT:
# - This document may contain multiple pages.
# - Treat all pages as ONE document.
# - Read every page before producing the result.
# - Information may continue from one page to another.
# - Items may appear on multiple pages.
# - Combine items from ALL pages.
# - Totals may appear only on the final page.
# - Do not stop extraction after PAGE 1.
# - Do not fabricate missing information.

# LAYOUT-AWARE DOCUMENT:

# {layout_text}

# RAW OCR:

# {ocr_text}
# """,
#             },
#         ]
#     )

#     return {"extracted_receipt": result}
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

from app.ai.prompts.prompt import (
    RECEIPT_EXTRACTION_PROMPT,
    INVOICE_EXTRACTION_PROMPT,
)
from app.ai.receipt.schemas import ReceiptExtraction
from app.ai.receipt.state import ReceiptState

load_dotenv()

model = ChatOpenRouter(
    model="openai/gpt-5-mini",
)

receipt_extractor = model.with_structured_output(
    ReceiptExtraction,
)

invoice_extractor = model.with_structured_output(
    ReceiptExtraction,
)


def extraction_node(state: ReceiptState):

    if state["is_complex"]:

        extractor = invoice_extractor

        user_prompt = f"""
The following document has already been processed using a document
structure parser.

The Markdown preserves:
- document hierarchy
- reading order
- tables
- merged cells

Use the Markdown as the PRIMARY source.

Only refer to the OCR text if some information is missing from
the Markdown.

===========================
DOCUMENT MARKDOWN
===========================

{state["markdown_text"]}

===========================
RAW OCR
===========================

{state["ocr_text"]}
"""

    else:

        extractor = receipt_extractor

        user_prompt = f"""
The following document is a simple retail receipt.

Use the OCR text below to extract all receipt information.

===========================
RAW OCR
===========================

{state["ocr_text"]}
"""

    extracted_receipt = extractor.invoke(
        [
            {
                "role": "system",
                "content": (
                    INVOICE_EXTRACTION_PROMPT
                    if state["is_complex"]
                    else RECEIPT_EXTRACTION_PROMPT
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
    )

    return {
        "extracted_receipt": extracted_receipt,
    }
