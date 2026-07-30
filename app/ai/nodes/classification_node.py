from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_openrouter import ChatOpenRouter

from app.ai.receipt.state import ReceiptState
from app.ai.receipt.schemas import Classification
from dotenv import load_dotenv

load_dotenv()

from app.ai.prompts.prompt import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_HUMAN_PROMPT,
)

classifier = ChatOpenRouter(
    model="openai/gpt-5-mini",
).with_structured_output(Classification)


def classification_node(
    state: ReceiptState,
):
    receipt = state["extracted_receipt"]

    if receipt is None:
        raise ValueError("Cannot classify receipt: " "extracted_receipt is missing")

    receipt_json = receipt.model_dump_json(indent=2)

    classification = classifier.invoke(
        [
            SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
            HumanMessage(
                content=CLASSIFICATION_HUMAN_PROMPT.format(
                    receipt=receipt_json,
                )
            ),
        ]
    )

    return {"classification": classification}
