from langchain_core.messages import HumanMessage, SystemMessage
from app.ai.receipt.state import ReceiptState
from app.ai.receipt.schemas import Classification
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv()

classifier = ChatOpenRouter(model="openai/gpt-5-mini").with_structured_output(
    Classification
)


def classification_node(state: ReceiptState):
    receipt = state["extracted_receipt"]

    if receipt is None:
        raise ValueError("Cannot classify receipt: extracted_receipt is missing")

    classification = classifier.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expense classification system. "
                    "Classify receipts using only the supplied receipt data. "
                    "Do not fabricate or infer unsupported information."
                )
            ),
            HumanMessage(content=receipt.model_dump_json(indent=2)),
        ]
    )

    return {"classification": classification}
