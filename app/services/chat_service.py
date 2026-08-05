import json
import logging
from typing import Any

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage, AIMessage

from app.ai.agent.context import ExpenseAgentContext
from sqlalchemy import select
from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.ai.classifiers.scope_classifier import Scope

logger = logging.getLogger(__name__)


class ChatService:

    def __init__(
        self,
        db,
        agent,
        storage,
        classifier,
    ):
        self.db = db
        self.agent = agent
        self.storage = storage
        self.classifier = classifier

    # =========================================================
    # SSE
    # =========================================================

    @staticmethod
    def _event(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # =========================================================
    # Thread title
    # =========================================================

    @staticmethod
    def _create_thread_title(
        message: str,
        max_length: int = 50,
    ) -> str:
        title = " ".join(message.strip().split())

        if not title:
            return "New chat"

        if len(title) <= max_length:
            return title

        return title[: max_length - 3].rstrip() + "..."

    # =========================================================
    # Tool result parsing
    # =========================================================

    @staticmethod
    def _parse_tool_result(
        message: ToolMessage,
    ) -> dict[str, Any] | None:
        """
        Convert ToolMessage content into a dictionary.

        Tool results may arrive as:
        - a JSON string
        - a dict
        """

        content = message.content

        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            try:
                result = json.loads(content)

                if isinstance(result, dict):
                    return result

            except json.JSONDecodeError:
                return None

        return None

    def _create_message_history(self, messages):
        history = []

        for message in messages[-8:]:  # Last 8 messages

            if message.role == "user":
                history.append(HumanMessage(content=message.content))

            else:
                history.append(AIMessage(content=message.content))
        return history

    # =========================================================
    # Chat stream
    # =========================================================

    def stream_chat(
        self,
        user: User,
        thread: Thread,
        message: str,
    ):
        # -----------------------------------------------------
        # Save user message
        # -----------------------------------------------------

        stmt = (
            select(Message)
            .where(Message.thread_id == thread.id)
            .order_by(Message.created_at.asc())
        )

        messages = list(self.db.scalars(stmt).all())

        history = self._create_message_history(messages=messages)

        scope = self.classifier.classify(history)

        user_message = Message(
            thread_id=thread.id,
            role="user",
            content=message,
            artifacts=[],
        )

        self.db.add(user_message)

        # -----------------------------------------------------
        # Generate initial thread title
        # -----------------------------------------------------

        if thread.title is None:
            thread.title = self._create_thread_title(message)

        self.db.commit()

        # -----------------------------------------------------
        # Agent context
        # -----------------------------------------------------

        context: ExpenseAgentContext = {
            "db": self.db,
            "user_id": user.id,
            "storage": self.storage,
        }

        # -----------------------------------------------------
        # LangGraph thread
        # -----------------------------------------------------

        config = {
            "configurable": {
                "thread_id": str(thread.id),
            }
        }

        # -----------------------------------------------------
        # Response state
        # -----------------------------------------------------

        complete_response = ""

        # Artifacts generated during THIS assistant response.
        artifacts: list[dict[str, Any]] = []

        try:
            if scope == Scope.OUT_OF_SCOPE:

                response = (
                    "I'm **Expense AI**, so I can only help with your "
                    "expenses, receipts, spending, reports, budgets, "
                    "and financial insights.\n\n"
                    "Try asking something like:\n"
                    "- What did I spend this month?\n"
                    "- Show my restaurant expenses.\n"
                    "- What items did I purchase?\n"
                    "- Export my July expenses to Excel."
                )

                assistant_message = Message(
                    thread_id=thread.id,
                    role="assistant",
                    content=response,
                    artifacts=[],
                )

                self.db.add(assistant_message)

                self.db.commit()

                yield self._event(
                    {
                        "type": "token",
                        "content": response,
                    }
                )

                yield self._event(
                    {
                        "type": "done",
                    }
                )

                return
            # =================================================
            # Agent stream
            # =================================================

            for chunk in self.agent.stream(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                context=context,
                stream_mode="messages",
            ):
                message_chunk, metadata = chunk

                # =============================================
                # TOOL RESULT
                # =============================================

                if isinstance(
                    message_chunk,
                    ToolMessage,
                ):
                    self._handle_tool_message(message_chunk)

                    result = self._parse_tool_result(message_chunk)

                    if not result:
                        continue

                    artifact = result.get("artifact")

                    if not artifact:
                        continue

                    if not isinstance(artifact, dict):
                        continue

                    # -----------------------------------------
                    # Store artifact for DB persistence
                    # -----------------------------------------

                    artifacts.append(artifact)

                    # -----------------------------------------
                    # Send artifact immediately to frontend
                    # -----------------------------------------

                    yield self._event(
                        {
                            "type": "artifact",
                            "artifact": artifact,
                        }
                    )

                    continue

                # =============================================
                # AI TOKEN
                # =============================================

                if not isinstance(
                    message_chunk,
                    AIMessageChunk,
                ):
                    continue

                # Don't send tool-call chunks to frontend.
                if message_chunk.tool_calls:
                    continue

                content = message_chunk.content

                if not content:
                    continue

                if not isinstance(
                    content,
                    str,
                ):
                    continue

                complete_response += content

                yield self._event(
                    {
                        "type": "token",
                        "content": content,
                    }
                )

            # =================================================
            # Save assistant message
            # =================================================

            # Save if there is either:
            #
            # 1. assistant text
            # 2. generated artifacts
            #
            # This also handles a response containing only
            # a downloadable file.

            if complete_response or artifacts:
                assistant_message = Message(
                    thread_id=thread.id,
                    role="assistant",
                    content=complete_response,
                    artifacts=artifacts,
                )

                self.db.add(assistant_message)

                self.db.commit()

            # =================================================
            # Finished
            # =================================================

            yield self._event(
                {
                    "type": "done",
                }
            )

        except Exception:
            self.db.rollback()

            logger.exception(
                "Chat streaming failed",
                extra={
                    "thread_id": str(thread.id),
                    "user_id": str(user.id),
                },
            )

            yield self._event(
                {
                    "type": "error",
                    "message": "Unable to generate response.",
                }
            )

    # =========================================================
    # Tool logging
    # =========================================================

    @staticmethod
    def _handle_tool_message(
        message: ToolMessage,
    ) -> None:
        """
        Log completed tool calls.

        Useful while debugging agent behaviour.
        """

        logger.debug(
            "Agent tool completed",
            extra={
                "tool_name": message.name,
                "tool_call_id": (message.tool_call_id),
            },
        )
