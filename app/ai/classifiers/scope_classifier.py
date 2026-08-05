from enum import Enum

from pydantic import BaseModel, Field

from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from app.ai.prompts.prompt import SCOPE_CLASSIFIER_SYSTEM_PROMPT

load_dotenv()


class Scope(str, Enum):
    EXPENSE = "expense"
    OUT_OF_SCOPE = "out_of_scope"


class ScopeResult(BaseModel):
    scope: Scope = Field(description="Whether the question belongs to Expense AI.")


class ScopeClassifier:

    def __init__(self):

        self.model = ChatOpenRouter(
            model="gpt-5-nano",
            temperature=0,
        ).with_structured_output(ScopeResult)

    def classify(
        self,
        messages: list[HumanMessage | AIMessage],
    ) -> Scope:

        result = self.model.invoke(
            [
                SystemMessage(content=SCOPE_CLASSIFIER_SYSTEM_PROMPT),
                *messages,
            ]
        )

        return result.scope
