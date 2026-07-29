from langchain_openrouter import ChatOpenRouter
from app.ai.prompts.prompt import INSIGHT_SYSTEM_PROMPT
from app.ai.insight.schema import AIInsights

llm = ChatOpenRouter(model="openai/gpt-5-mini")
insight_model = llm.with_structured_output(AIInsights)


def get_insight_model_result(human_content: str):
    result = insight_model.invoke(
        [
            {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analyze this spending data and return "
                    "the most useful dashboard insights.\n\n" + human_content
                ),
            },
        ]
    )
    return result
