from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.auth_router import router as AuthRouter
from app.router.receipt_router import router as ReceiptRouter
from app.router.dashboard_router import router as DashboardRouter
from app.router.chat_router import router as ChatRouter
from pathlib import Path
from app.core.checkpointer import get_checkpointer
from app.ai.agent.agent import create_expense_agent
from contextlib import asynccontextmanager
from app.router.thread_router import router as ThreadRouter

APP_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):

    checkpointer_context = get_checkpointer()

    checkpointer = checkpointer_context.__enter__()

    # Creates LangGraph checkpoint tables if needed.
    checkpointer.setup()

    expense_agent = create_expense_agent(checkpointer=checkpointer)

    app.state.checkpointer = checkpointer
    app.state.expense_agent = expense_agent

    try:
        yield

    finally:
        checkpointer_context.__exit__(
            None,
            None,
            None,
        )


app = FastAPI(lifespan=lifespan)

# Not safe! Add your own allowed domains
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(AuthRouter)
app.include_router(ReceiptRouter)
app.include_router(DashboardRouter)
app.include_router(ChatRouter)
app.include_router(ThreadRouter)


# Example GET route for app
@app.get("/")
def read_root():

    return {"message": "Healthy Server"}
