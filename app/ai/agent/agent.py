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


expense_agent = create_agent(
    model=model,
    tools=[
        list_tables,
        get_table_schema,
        get_sample_data,
        execute_sql,
    ],
    context_schema=ExpenseAgentContext,
    system_prompt=EXPENSE_AGENT_PROMPT,
    middleware=[
        # -----------------------------
        # Tool retries
        # -----------------------------
        ToolRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
        # -----------------------------
        # Model/provider retries
        # -----------------------------
        ModelRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
        # -----------------------------
        # Prevent excessive tool usage
        # -----------------------------
        ToolCallLimitMiddleware(
            run_limit=10,
        ),
        # -----------------------------
        # Prevent runaway model loops
        # -----------------------------
        ModelCallLimitMiddleware(
            run_limit=8,
        ),
        # -----------------------------
        # Long conversation management
        # -----------------------------
        SummarizationMiddleware(
            model=model,
            trigger=("tokens", 8000),
            keep=("messages", 10),
        ),
    ],
)
