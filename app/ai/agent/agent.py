from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

from langchain.agents.middleware import (
    ToolRetryMiddleware,
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
    ModelCallLimitMiddleware,
)

from app.ai.agent.context import ExpenseAgentContext
from app.ai.agent.prompt import EXPENSE_AGENT_PROMPT

from app.ai.agent.tools import (
    list_tables,
    get_table_schema,
    get_sample_data,
    execute_sql,
)

model = ChatOpenRouter(
    model="openai/gpt-5-mini",
    temperature=0,
)


def create_expense_agent(checkpointer):
    return create_agent(
        model=model,
        tools=[
            list_tables,
            get_table_schema,
            get_sample_data,
            execute_sql,
        ],
        context_schema=ExpenseAgentContext,
        system_prompt=EXPENSE_AGENT_PROMPT,
        checkpointer=checkpointer,
        middleware=[
            ToolRetryMiddleware(
                max_retries=2,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
            ModelRetryMiddleware(
                max_retries=2,
                backoff_factor=2.0,
                initial_delay=1.0,
            ),
            ToolCallLimitMiddleware(
                run_limit=10,
            ),
            ModelCallLimitMiddleware(
                run_limit=8,
            ),
            SummarizationMiddleware(
                model=model,
                trigger=("tokens", 8000),
                keep=("messages", 10),
            ),
        ],
    )
