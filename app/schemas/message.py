from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
