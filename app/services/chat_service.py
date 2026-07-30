import json

from langchain_core.messages import (
    AIMessageChunk,
    HumanMessage,
)


from app.ai.agent.context import ExpenseAgentContext

from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User

import logging

logger = logging.getLogger(__name__)


class ChatService:

    def __init__(self, db, agent):
        self.db = db
        self.agent = agent

    @staticmethod
    def _event(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

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

    def stream_chat(
        self,
        user: User,
        thread: Thread,
        message: str,
    ):
        user_message = Message(
            thread_id=thread.id,
            role="user",
            content=message,
        )

        self.db.add(user_message)

        if thread.title is None:
            thread.title = self._create_thread_title(message)

        self.db.commit()

        context: ExpenseAgentContext = {
            "db": self.db,
            "user_id": user.id,
        }

        config = {
            "configurable": {
                "thread_id": str(thread.id),
            }
        }

        complete_response = ""

        try:

            for chunk in self.agent.stream(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                context=context,
                stream_mode="messages",
            ):
                message_chunk, metadata = chunk

                if not isinstance(
                    message_chunk,
                    AIMessageChunk,
                ):
                    continue

                if message_chunk.tool_calls:
                    continue

                content = message_chunk.content

                if not content or not isinstance(content, str):
                    continue

                complete_response += content

                yield self._event(
                    {
                        "type": "token",
                        "content": content,
                    }
                )

            if complete_response:

                assistant_message = Message(
                    thread_id=thread.id,
                    role="assistant",
                    content=complete_response,
                )

                self.db.add(assistant_message)

                self.db.commit()

            yield self._event({"type": "done"})

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
