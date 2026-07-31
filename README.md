# Expense AI — Backend

Backend service for **Expense AI**, an AI-powered expense tracking application that turns receipts into structured financial data and lets users interact with their expenses through natural language.

The backend handles receipt processing, expense extraction, AI agent execution, conversational memory, background jobs, file exports, and real-time response streaming.

## What is Expense AI?

Expense AI lets users upload receipts and interact with their expense history through an AI assistant.

Instead of manually tracking every transaction, users can upload a receipt and ask questions such as:

- "How much did I spend this month?"
- "What items did I purchase?"
- "Show all my medical expenses."
- "Which category am I spending the most on?"
- "Export my July expenses to Excel."

The agent works with the user's actual expense data and can perform actions such as querying expenses and generating downloadable reports.

---

## Features

### Receipt Processing

Upload receipt images or PDFs and automatically extract structured information including:

- Merchant
- Purchase date
- Total amount
- Currency
- Payment method
- Expense category
- Individual purchased items

Receipt processing runs asynchronously in the background so users don't have to wait for extraction to complete.

### AI Expense Agent

A conversational AI agent built using **LangGraph / LangChain**.

The agent can use tools to interact with the user's expense data instead of relying only on the model's knowledge.

Example:

```text
User:
How much did I spend on medical expenses this month?

Agent:
→ determines the required data
→ calls the appropriate expense tool
→ queries the user's expense data
→ generates a response
```

### Real-Time Streaming

AI responses are streamed to the frontend using **Server-Sent Events (SSE)**.

This allows responses to appear token-by-token instead of waiting for the entire generation to finish.

### Persistent Conversations

Chat threads and messages are persisted so users can return to previous conversations.

LangGraph checkpointing is also used to maintain agent conversation state.

### Background Processing

Receipt extraction is handled asynchronously using:

- Celery
- Redis

The API can immediately return after a receipt upload while processing continues in the background.

Typical flow:

```text
Upload Receipt
      ↓
Store Receipt
      ↓
Queue Celery Task
      ↓
Process Receipt
      ↓
AI Extraction
      ↓
Store Structured Expense Data
```

### File Exports

The AI agent can generate downloadable reports directly from chat.

Supported formats:

- CSV
- Excel (`.xlsx`)
- PDF

Generated files are uploaded to storage and returned to the conversation as downloadable artifacts.

Artifacts are persisted with messages so generated files remain visible when a conversation is reopened.

---

## Tech Stack

- **Python**
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy**
- **Alembic**
- **LangChain**
- **LangGraph**
- **Celery**
- **Redis**
- **Pydantic**
- **SSE**
- **ImageKit / File Storage**
- **Clerk Authentication**

---

## Architecture

```text
                     ┌─────────────────────┐
                     │      Frontend       │
                     │       Next.js       │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │       FastAPI       │
                     │        API          │
                     └──────┬────────┬─────┘
                            │        │
                   ┌────────┘        └────────┐
                   ▼                          ▼
          ┌────────────────┐          ┌────────────────┐
          │   PostgreSQL   │          │     Redis      │
          │                │          │     Broker     │
          └────────────────┘          └───────┬────────┘
                                              │
                                              ▼
                                      ┌────────────────┐
                                      │ Celery Workers │
                                      │                │
                                      │ Receipt        │
                                      │ Processing     │
                                      └────────────────┘

                     FastAPI
                        │
                        ▼
                ┌─────────────────┐
                │ LangGraph Agent │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │      Tools      │
                │                 │
                │ Expenses        │
                │ Receipts        │
                │ Exports         │
                └─────────────────┘
```

---

## Project Structure

```text
app/
├── ai/
│   └── agent/
│       ├── context.py
│       ├── tools/
│       └── ...
│
├── core/
│   ├── celery_app.py
│   ├── config.py
│   └── dependencies.py
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
│   └── receipt_item.py
│
├── router/
│   ├── chat_router.py
│   ├── receipt_router.py
│   └── thread_router.py
│
├── schemas/
│
├── services/
│   ├── chat_service.py
│   ├── receipt_service.py
│   └── export_service.py
│
├── tasks/
│   └── receipt_tasks.py
│
└── main.py
```

The exact structure may evolve as the project develops.

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

# Add the authentication, AI provider,
# storage and other credentials required
# by your local configuration.
```

Never commit real credentials to the repository.

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start Redis

Make sure Redis is running locally.

For example:

```bash
redis-server
```

### 6. Start the Celery worker

```bash
uv run celery -A app.core.celery_app:celery_app worker --loglevel=info
```

On environments where Celery's prefork pool causes issues, such as some local macOS setups, you may use:

```bash
uv run celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 7. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The FastAPI development server should now be running locally.

---

## API Overview

The backend provides APIs for:

- Receipt uploads
- Receipt management
- Receipt deletion
- Processing status
- Chat threads
- Message history
- AI conversations
- Streaming AI responses

Interactive API documentation is available through FastAPI while the backend is running.

---

## Receipt Processing Flow

```text
User uploads receipt
        ↓
FastAPI validates upload
        ↓
File stored
        ↓
Receipt created with processing status
        ↓
Celery task queued
        ↓
Worker processes receipt
        ↓
AI extracts structured information
        ↓
Receipt + items saved to PostgreSQL
        ↓
Receipt becomes available to the AI agent
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
Expense / Receipt Data
     ↓
LLM Response
     ↓
SSE Stream
     ↓
Frontend
```

When an export is requested:

```text
User
 ↓
"Export my July expenses to Excel"
 ↓
Agent
 ↓
Expense Tool
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

## Frontend

The frontend repository is available here:

https://github.com/PriyanshGupta2002/smart-ai-expense-frontend

---

## Roadmap

Potential future improvements include:

- Spending analytics and visualizations
- Budgets and spending limits
- Recurring expense detection
- Spending alerts
- Bank statement imports
- Better receipt classification
- Advanced financial insights
- Improved agent evaluation and observability

---

## Contributing

Contributions, suggestions, and feedback are welcome.

If you find a bug or have an idea for a feature, feel free to open an issue or submit a pull request.

---

## Author

Built by **Priyansh Gupta**

GitHub: https://github.com/PriyanshGupta2002