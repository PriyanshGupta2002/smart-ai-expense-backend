from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
from app.ai.receipt.schemas import ReceiptExtraction
from app.ai.receipt.state import ReceiptState
from app.ai.prompts.prompt import RECEIPT_EXTRACTION_PROMPT

load_dotenv()


extractor = ChatOpenRouter(model="openai/gpt-5-mini").with_structured_output(
    ReceiptExtraction
)


def extraction_node(state: ReceiptState):

    layout_text = state["layout_text"]
    ocr_text = state["ocr_text"]

    result = extractor.invoke(
        [
            {
                "role": "system",
                "content": RECEIPT_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
Extract the complete receipt/invoice below.

IMPORTANT:
- This document may contain multiple pages.
- Treat all pages as ONE document.
- Read every page before producing the result.
- Information may continue from one page to another.
- Items may appear on multiple pages.
- Combine items from ALL pages.
- Totals may appear only on the final page.
- Do not stop extraction after PAGE 1.
- Do not fabricate missing information.

LAYOUT-AWARE DOCUMENT:

{layout_text}

RAW OCR:

{ocr_text}
""",
            },
        ]
    )

    return {"extracted_receipt": result}
