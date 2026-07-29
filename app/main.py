from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.auth_router import router as AuthRouter
from app.router.receipt_router import router as ReceiptRouter
from app.router.dashboard_router import router as DashboardRouter
from app.router.chat_router import router as ChatRouter
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

app = FastAPI()

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


# Example GET route for app
@app.get("/")
def read_root():

    return {"message": "Healthy Server"}
