
# Expense AI — Backend

Backend service for **Expense AI**, an AI-powered expense tracking application that turns receipts and Gmail transaction emails into structured financial data and lets users interact with their expenses through natural language.

The backend handles receipt processing, Gmail transaction ingestion, AI classification, agent execution, conversational memory, background jobs, file exports, profile management, and real-time response streaming.

---

## What is Expense AI?

Expense AI helps users understand and manage their personal finances without manually searching through receipts and transaction emails.

Users can:

- Upload receipts and invoices.
- Automatically extract structured expense information.
- Connect their Gmail account.
- Automatically detect transaction emails from Gmail.
- Classify transactions using AI.
- Automatically add genuine expenses to their expense history.
- Ask questions about their spending using natural language.
- Generate downloadable expense reports.
- Send reports through their connected Gmail account.

Example questions:

```text
How much did I spend this month?

Show all my medical expenses.

Which category am I spending the most on?

What did I buy from Amazon?

Export my July expenses to Excel.

Send me my expenses by email.
````

---

## Features

### Receipt Processing

Users can upload receipt images or PDFs and automatically extract structured information including:

* Merchant
* Purchase date
* Total amount
* Currency
* Payment method
* Expense category
* Individual purchased items
* Merchant information

Receipt processing runs asynchronously in the background using Celery.

Typical flow:

```text
Upload Receipt
      ↓
Store File
      ↓
Create Receipt
      ↓
Queue Celery Task
      ↓
Receipt Processing
      ↓
AI Extraction
      ↓
Save Structured Data
      ↓
Receipt Available to AI Agent
```

---

### AI Expense Agent

A conversational AI agent built using **LangGraph / LangChain**.

The agent can use tools to interact with the user's expense data instead of relying only on model knowledge.

Example:

```text
User:

How much did I spend on medical expenses this month?

        ↓

Agent determines the required data

        ↓

Expense SQL Tool

        ↓

Queries the authenticated user's data

        ↓

Generates a natural-language response
```

The agent can work with:

* Expenses
* Receipts
* Receipt items
* Budgets
* Expense exports
* Gmail

---

### AI Transaction Classification

Gmail transaction emails are classified using an LLM.

The system distinguishes between:

* `expense`
* `income`
* `transfer`
* `unknown`

For example:

```text
₹1,000 transferred to myself
→ TRANSFER

₹1,000 sent to a friend
→ TRANSFER

₹850 paid to a restaurant
→ EXPENSE

₹50,000 salary credited
→ INCOME

OTP / promotional email
→ UNKNOWN
```

The classifier extracts structured information such as:

* Amount
* Merchant
* Currency
* Transaction date
* Payment method
* Category
* Description
* Confidence

Example:

```json
{
  "is_transaction": true,
  "transaction_type": "expense",
  "amount": 850,
  "currency": "INR",
  "merchant_name": "XYZ Restaurant",
  "transaction_date": "2026-09-03T22:45:00+05:30",
  "payment_method": "UPI",
  "category": "food",
  "confidence": 0.96
}
```

The LLM only performs classification and extraction. The backend decides whether the transaction should be persisted.

---

### Gmail Integration

Users can connect their Google account using Google OAuth.

The backend stores the Google connection information required for Gmail access:

* Access token
* Refresh token
* Token expiration time
* Granted scopes
* Last Gmail synchronization timestamp

The Gmail connection is associated with the authenticated application user.

---

### Gmail Transaction Ingestion

Expense AI can read transaction emails from the user's Gmail account and automatically convert relevant transactions into expenses.

```text
Transaction happens
        ↓
Bank / Payment provider sends email
        ↓
Gmail
        ↓
Gmail Sync
        ↓
Email Parser
        ↓
LLM Classification
        ↓
Transaction Processor
        ↓
Receipt
```

Gmail-originated receipts are stored with:

```text
source = "gmail"
```

while manually uploaded receipts use:

```text
source = "upload"
```

Gmail-generated expenses do not require an ImageKit receipt image.

---

### Gmail Email Parser

Raw Gmail API responses contain encoded content, MIME structures, nested parts, headers, and HTML bodies.

Expense AI converts these messages into normalized application data.

The parser extracts:

* Gmail message ID
* Thread ID
* Sender
* Recipient
* Subject
* Date
* Plain text
* HTML
* Normalized text
* Gmail labels
* Email snippet

For HTML-only emails, the parser converts HTML into readable text before sending the content to the transaction classifier.

Typical flow:

```text
Gmail API Message
       ↓
Decode MIME content
       ↓
Extract headers
       ↓
Extract text/plain
       ↓
Extract HTML
       ↓
HTML → readable text when required
       ↓
Normalized Email
```

---

### Gmail Transaction Processing

After parsing an email, the transaction processor:

1. Checks whether the Gmail message was already imported.
2. Sends the email to the transaction classifier.
3. Ignores non-transaction emails.
4. Ignores income transactions for expense creation.
5. Ignores person-to-person transfers.
6. Validates the transaction amount.
7. Creates a `Receipt` for genuine expenses.

This keeps ordinary transfers from being incorrectly recorded as expenses.

---

### Incremental Gmail Synchronization

Each Google connection stores:

```text
last_gmail_sync_at
```

This allows subsequent synchronizations to focus on newer transaction emails rather than repeatedly scanning the entire mailbox.

First synchronization:

```text
last_gmail_sync_at = NULL
        ↓
Find transaction emails
        ↓
Parse
        ↓
Classify
        ↓
Create Receipts
        ↓
Update last_gmail_sync_at
```

Later synchronizations:

```text
last_gmail_sync_at
        ↓
Find newer transaction emails
        ↓
Parse
        ↓
Classify
        ↓
Process
        ↓
Create new Receipts
```

The existing `gmail_message_id` uniqueness constraint provides an additional duplicate-protection layer.

---

### Gmail Token Refresh

Google access tokens expire.

Expense AI automatically refreshes expired access tokens using the stored refresh token.

```text
Gmail Operation
      ↓
Get Google Connection
      ↓
Check token expiry
      ↓
Token expired?
   /          \
 NO            YES
 ↓              ↓
Gmail API    Refresh Token
                 ↓
          New Access Token
                 ↓
             Update DB
                 ↓
              Gmail API
```

This means the user does not need to reconnect Google every time the access token expires.

---

### Background Gmail Processing

Gmail synchronization runs asynchronously using **Celery + Redis**.

When a user connects their Google account, an initial Gmail synchronization can be queued as a background task.

```text
Google OAuth
      ↓
Save GoogleConnection
      ↓
Queue Gmail Sync Task
      ↓
Celery Worker
      ↓
Gmail Sync
      ↓
Transaction Classification
      ↓
Receipt Creation
```

---

### Automatic Gmail Synchronization

Celery Beat periodically schedules Gmail synchronization.

The current scheduler runs every **5 minutes**.

```text
Celery Beat
      ↓
Every 5 minutes
      ↓
Find connected Google accounts
      ↓
Queue Gmail sync tasks
      ↓
Celery Worker
      ↓
GmailSyncService
      ↓
New transaction emails
      ↓
AI classification
      ↓
Receipt creation
```

This means that after a transaction email arrives, the expense can automatically be imported during the next scheduled synchronization.

The current implementation uses periodic polling. Gmail push notifications using Google Pub/Sub can be introduced later for more immediate processing.

---

### Duplicate Protection

Every Gmail-imported receipt stores:

```text
gmail_message_id
```

The field has a unique constraint so the same Gmail message cannot create duplicate expenses.

```text
Gmail Message
      ↓
gmail_message_id = abc123
      ↓
Receipt created

Same Gmail Message
      ↓
gmail_message_id = abc123
      ↓
Already imported
      ↓
Skip
```

---

### Gmail Sending

The AI agent can send emails using the user's connected Gmail account.

For example:

```text
User:

Send me my expenses.
```

The agent can:

```text
Query expenses
      ↓
Generate report
      ↓
Generate PDF / CSV / XLSX
      ↓
Upload file
      ↓
Send through Gmail
```

The recipient does not need to be supplied by the model. The Gmail service obtains the authenticated user's email address from the connected Gmail profile.

---

### Real-Time Streaming

AI responses are streamed to the frontend using **Server-Sent Events (SSE)**.

This allows responses to appear incrementally instead of waiting for the complete response.

```text
User Message
      ↓
FastAPI
      ↓
Chat Service
      ↓
LangGraph Agent
      ↓
Tool Calls
      ↓
LLM
      ↓
SSE Stream
      ↓
Frontend
```

Generated artifacts can also be streamed to the frontend and persisted with assistant messages.

---

### Persistent Conversations

Chat threads and messages are persisted in PostgreSQL.

LangGraph checkpointing is used to maintain agent execution state and conversational memory.

Users can return to previous threads and continue conversations.

---

### File Exports

The AI agent can generate downloadable expense reports directly from chat.

Supported formats:

* CSV
* XLSX
* PDF

Example:

```text
User

"Export my July expenses to Excel"

        ↓

LangGraph Agent

        ↓

Expense Query

        ↓

Structured Data

        ↓

Export Tool

        ↓

Generate XLSX

        ↓

Upload File

        ↓

Artifact

        ↓

Chat Message
```

Generated artifacts are persisted with messages so they remain accessible when a conversation is reopened.

---

### Profile Management

Expense AI provides account profile management including:

* First name
* Last name
* Email
* Profile image

Profile images are stored using ImageKit, while profile image metadata is associated with the user's database record.

---

## SQL Safety and User Isolation

AI-generated SQL is validated before execution.

The SQL execution layer enforces:

* PostgreSQL-compatible SQL
* SELECT-only queries
* Allowed table restrictions
* User-level data isolation
* Maximum row limits
* SQL parsing and validation

Queries against user-owned tables must be scoped to the authenticated user.

Example:

```sql
SELECT
    COALESCE(SUM(total), 0) AS total_spent
FROM receipts
WHERE user_id = :user_id
  AND purchase_datetime >= date_trunc('month', CURRENT_DATE);
```

The actual authenticated user ID is supplied by the application's runtime context rather than generated or requested from the user.

---

## Architecture

```text
                         ┌─────────────────────┐
                         │      Next.js        │
                         │      Frontend       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │         API         │
                         └──────┬───────┬──────┘
                                │       │
                ┌───────────────┘       └────────────────┐
                │                                        │
                ▼                                        ▼
       ┌─────────────────┐                      ┌─────────────────┐
       │   PostgreSQL    │                      │      Redis      │
       │                 │                      │                 │
       │ Users           │                      │ Celery Broker   │
       │ Receipts        │                      │                 │
       │ ReceiptItems    │                      └────────┬────────┘
       │ Threads         │                               │
       │ Messages        │                               ▼
       │ GoogleConnection│                      ┌─────────────────┐
       └────────┬────────┘                      │ Celery Workers  │
                │                               │                 │
                │                               │ Receipt Tasks   │
                │                               │ Gmail Sync      │
                │                               └─────────────────┘
                │
                ▼
       ┌─────────────────────┐
       │   LangGraph Agent   │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │        Tools        │
       │                     │
       │ Expense Queries     │
       │ SQL Execution       │
       │ Exports             │
       │ Gmail               │
       └─────────────────────┘
```

### Gmail Transaction Pipeline

```text
                         ┌─────────────────┐
                         │      Gmail      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Gmail Sync    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Email Parser   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  LLM Classifier │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
                 EXPENSE        INCOME       TRANSFER
                    │             │             │
                    ▼             ▼             ▼
                 Receipt        Ignore       Ignore
```

### End-to-End Expense Flow

```text
Receipt Upload
      │
      ├──────────────────────┐
      │                      │
      ▼                      ▼
Image / PDF              Gmail Transaction
      │                      │
      ▼                      ▼
Receipt Processing      Gmail Parser
      │                      │
      ▼                      ▼
AI Extraction          LLM Classification
      │                      │
      └──────────────┬───────┘
                     │
                     ▼
                  Receipt
                     │
                     ▼
                PostgreSQL
                     │
                     ▼
              LangGraph Agent
                     │
                     ▼
              Natural Language
```

---

## Project Structure

```text
app/
│
├── ai/
│   ├── agent/
│   │   ├── context.py
│   │   ├── prompt.py
│   │   └── tools/
│   │       ├── execute_sql.py
│   │       ├── export_tool.py
│   │       ├── gmail_tools.py
│   │       ├── get_sample_data.py
│   │       ├── get_table_schema.py
│   │       └── list_tables.py
│   │
│   └── gmail/
│       ├── schemas.py
│       ├── prompt.py
│       └── transaction_classifier.py
│
├── core/
│   ├── config.py
│   ├── dependencies.py
│   └── security.py
│
├── db/
│   ├── base.py
│   └── session.py
│
├── models/
│   ├── user.py
│   ├── thread.py
│   ├── message.py
│   ├── receipt.py
│   ├── receipt_item.py
│   └── google_connections.py
│
├── router/
│   ├── auth_router.py
│   ├── chat_router.py
│   ├── receipt_router.py
│   ├── thread_router.py
│   ├── user_router.py
│   └── google_router.py
│
├── schemas/
│
├── services/
│   ├── chat_service.py
│   ├── receipt_service.py
│   ├── export_service.py
│   ├── gmail_service.py
│   ├── gmail_parser.py
│   ├── gmail_ingestion_service.py
│   ├── gmail_transaction_processor.py
│   ├── gmail_sync_service.py
│   ├── google_oauth_service.py
│   └── google_connection_service.py
│
├── tasks/
│   ├── receipt_tasks.py
│   ├── gmail_tasks.py
│   └── gmail_scheduler_tasks.py
│
├── celery_app.py
│
└── main.py
```

The exact structure may evolve as the project develops.

---

## Tech Stack

* **Python**
* **FastAPI**
* **PostgreSQL**
* **SQLAlchemy**
* **Alembic**
* **LangChain**
* **LangGraph**
* **Gemini 2.5 Flash**
* **Celery**
* **Redis**
* **Pydantic**
* **Server-Sent Events (SSE)**
* **Gmail API**
* **Google OAuth**
* **ImageKit**
* **Clerk Authentication**

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/PriyanshGupta2002/smart-ai-expense-backend.git

cd smart-ai-expense-backend
```

### 2. Install dependencies

This project uses `uv`.

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/expense_ai

REDIS_URL=redis://localhost:6379/0

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key

# Add the remaining authentication,
# AI provider, storage, and application
# configuration required by your setup.
```

Never commit real credentials to the repository.

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start Redis

Make sure Redis is running locally.

```bash
redis-server
```

### 6. Start the Celery Worker

```bash
uv run celery -A app.celery_app:celery_app worker --loglevel=info
```

On environments where Celery's prefork pool causes issues, such as some local macOS setups:

```bash
uv run celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 7. Start Celery Beat

Celery Beat periodically schedules Gmail synchronization.

```bash
uv run celery -A app.celery_app:celery_app beat --loglevel=info
```

### 8. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The FastAPI development server should now be running locally.

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## API Overview

The backend provides APIs for:

* Authentication
* User profile management
* Profile image management
* Receipt uploads
* Receipt management
* Receipt deletion
* Receipt processing status
* Gmail OAuth connection
* Gmail connection status
* Gmail synchronization
* Chat threads
* Message history
* AI conversations
* Streaming AI responses

---

## Receipt Processing Flow

```text
User uploads receipt

        ↓

FastAPI validates upload

        ↓

File stored

        ↓

Receipt created

        ↓

Celery task queued

        ↓

Worker processes receipt

        ↓

AI extracts structured information

        ↓

Receipt + ReceiptItems saved

        ↓

Receipt becomes available to AI agent
```

---

## Gmail Processing Flow

```text
User connects Google account

        ↓

Google OAuth

        ↓

GoogleConnection saved

        ↓

Initial Gmail sync queued

        ↓

Celery Worker

        ↓

GmailSyncService

        ↓

Incremental Gmail search

        ↓

GmailParser

        ↓

Transaction Classifier

        ↓

Transaction Processor

        ↓

Expense?

     /       \
   YES        NO
   ↓           ↓
Receipt     Ignore
```

---

## AI Chat Flow

```text
User Message
      ↓
FastAPI
      ↓
Chat Service
      ↓
LangGraph Agent
      ↓
Tool Selection
      ↓
Expense / Receipt / Gmail Tools
      ↓
LLM Response
      ↓
SSE Stream
      ↓
Frontend
```

---

## Export Flow

```text
User

 ↓

"Export my July expenses to Excel"

 ↓

LangGraph Agent

 ↓

Expense Query

 ↓

Structured Data

 ↓

Export Tool

 ↓

Generate XLSX

 ↓

Upload File

 ↓

Artifact

 ↓

Chat Message
```

---

## Gmail Sync Flow

```text
Transaction happens

        ↓

Bank / Payment provider sends email

        ↓

Gmail

        ↓

Celery Beat

        ↓

Gmail Sync Task

        ↓

Gmail API

        ↓

Email Parser

        ↓

LLM Transaction Classifier

        ↓

Expense / Income / Transfer / Unknown

        ↓

Expense

        ↓

Receipt

        ↓

PostgreSQL
```

---

## Frontend

The frontend repository is available here:

[https://github.com/PriyanshGupta2002/smart-ai-expense-frontend](https://github.com/PriyanshGupta2002/smart-ai-expense-frontend)

---

## Roadmap

Potential future improvements include:

* Gmail push notifications using Google Pub/Sub
* Near-real-time Gmail transaction processing
* Gmail History API-based synchronization
* Invoice line-item extraction from Gmail
* Automatic recurring expense detection
* Spending analytics and visualizations
* Budgets and spending limits
* Spending alerts
* Bank statement imports
* Better transaction deduplication
* Advanced financial insights
* Agent evaluation and observability
* Improved AI extraction accuracy
* Human review for low-confidence transactions

---

## Contributing

Contributions, suggestions, and feedback are welcome.

If you find a bug or have an idea for a feature, feel free to open an issue or submit a pull request.

---

## Author

Built by **Priyansh Gupta**

GitHub:

[https://github.com/PriyanshGupta2002](https://github.com/PriyanshGupta2002)

Frontend:

[https://github.com/PriyanshGupta2002/smart-ai-expense-frontend](https://github.com/PriyanshGupta2002/smart-ai-expense-frontend)

