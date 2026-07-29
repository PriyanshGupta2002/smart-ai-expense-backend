import json

from app.ai.agent.agent import expense_agent
from app.ai.agent.context import ExpenseAgentContext
from app.models.user import User


class ChatService:

    def __init__(self, db):
        self.db = db

    def stream_chat(
        self,
        user: User,
        message: str,
    ):
        context = ExpenseAgentContext(
            user_id=user.id,
            db=self.db,
        )

        try:
            for chunk in expense_agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
                context=context,
                stream_mode="messages",
            ):
                message_chunk, metadata = chunk

                content = message_chunk.content

                if not content:
                    continue

                # We'll tighten this below for your model's
                # exact content format.
                if isinstance(content, str):
                    yield self._sse(
                        "token",
                        {
                            "content": content,
                        },
                    )

            yield self._sse(
                "done",
                {},
            )

        except Exception as exc:
            yield self._sse(
                "error",
                {
                    "message": "Unable to complete the request.",
                },
            )

    @staticmethod
    def _sse(
        event: str,
        data: dict,
    ) -> str:

        return f"event: {event}\n" f"data: {json.dumps(data)}\n\n"
