from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
from app.ai.gmail import GmailTransactionClassifier

load_dotenv()

model = ChatOpenRouter(
    model="google/gemini-3.8-flash",
    temperature=0,
)

classifier = GmailTransactionClassifier(
    model=model,
)

result = classifier.classify(
    subject="UPI payment successful",
    sender="alerts@bank.com",
    date="2026-09-03T10:30:00+05:30",
    text="""
    Your UPI transaction was successful.

    ₹1,499 has been debited from your account.
    Merchant: Amazon
    Transaction ID: 123456789
    """,
)

print(result)
