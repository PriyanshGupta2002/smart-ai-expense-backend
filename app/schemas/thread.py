from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ThreadCreate(BaseModel):
    pass


class ThreadResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]


class ThreadUpdate(BaseModel):
    title: str
