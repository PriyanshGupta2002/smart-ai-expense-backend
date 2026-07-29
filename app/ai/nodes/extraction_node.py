from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
from app.ai.receipt.schemas import ReceiptExtraction
from app.ai.receipt.state import ReceiptState

load_dotenv()


extractor = ChatOpenRouter(model="openai/gpt-5-mini").with_structured_output(
    ReceiptExtraction
)


def extraction_node(
    state: ReceiptState,
):

    receipt = extractor.invoke(f"""
You extract structured information from receipts and invoices.

Use only information supported by the supplied OCR.

IMPORTANT:
- Do not fabricate missing values.
- A product name may span multiple physical lines.
- Do not treat every OCR line as a separate item.
- Use the reconstructed row/layout information to determine
  whether text continues the previous item.
- Tax shown on a receipt may already be included in item prices.
- total means the final amount payable.

RAW OCR:
{state["ocr_text"]}

RECONSTRUCTED LAYOUT:
{state["layout_text"]}
""")

    return {"extracted_receipt": receipt}
