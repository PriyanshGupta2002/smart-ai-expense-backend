from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.thread import Thread
from app.models.message import Message
from app.models.user import User


class ThreadService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create_thread(
        self,
        user: User,
    ) -> Thread:

        thread = Thread(
            user_id=user.id,
        )

        self.db.add(thread)

        self.db.commit()

        self.db.refresh(thread)

        return thread

    def get_threads(
        self,
        user: User,
    ) -> list[Thread]:

        stmt = (
            select(Thread)
            .where(Thread.user_id == user.id)
            .order_by(Thread.updated_at.desc())
        )

        return list(self.db.scalars(stmt).all())

    def get_thread(
        self,
        user: User,
        thread_id: UUID,
    ) -> Thread | None:

        stmt = select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == user.id,
        )

        return self.db.scalar(stmt)

    def get_messages(
        self,
        user: User,
        thread_id: UUID,
    ) -> list[Message]:

        # Important security check
        thread = self.get_thread(
            user=user,
            thread_id=thread_id,
        )

        if thread is None:
            return []

        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
        )

        return list(self.db.scalars(stmt).all())

    def update_thread(
        self,
        user: User,
        thread_id: UUID,
        title: str,
    ):
        thread = self.get_thread(
            user=user,
            thread_id=thread_id,
        )

        if thread is None:
            return None

        thread.title = title.strip()

        self.db.commit()
        self.db.refresh(thread)

        return thread

    def delete_thread(
        self,
        user: User,
        thread_id: UUID,
    ):
        thread = self.get_thread(
            user=user,
            thread_id=thread_id,
        )

        if thread is None:
            return False

        self.db.delete(thread)
        self.db.commit()

        return True
