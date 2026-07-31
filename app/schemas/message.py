from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatArtifactResponse(BaseModel):
    name: str
    url: str
    mime_type: str
    size: int | None = None


class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    role: str
    content: str
    created_at: datetime
    artifacts: list[ChatArtifactResponse]

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
