from typing import Literal

from pydantic import BaseModel, Field


class AIInsight(BaseModel):
    title: str
    description: str

    type: Literal[
        "warning",
        "positive",
        "trend",
        "observation",
    ]

    importance: Literal[
        "high",
        "medium",
        "low",
    ]

    related_category: str | None = None


class AIInsights(BaseModel):

    insights: list[AIInsight] = Field(
        description="The 1 to 3 most useful spending insights."
    )
