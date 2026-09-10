from langchain.agents.middleware import dynamic_prompt, ModelRequest

from app.ai.agent.context import ExpenseAgentContext
from app.ai.agent.prompt import EXPENSE_AGENT_PROMPT, build_preferences_prompt


@dynamic_prompt
def user_preferences_prompt(
    request: ModelRequest[ExpenseAgentContext],
) -> str:
    """
    Build the system prompt dynamically using the current user's preferences.
    """

    context = request.runtime.context

    if context is None or context.preferences is None:
        return EXPENSE_AGENT_PROMPT

    preferences_prompt = build_preferences_prompt(context.preferences)

    return f"""
{EXPENSE_AGENT_PROMPT}

{preferences_prompt}
"""
