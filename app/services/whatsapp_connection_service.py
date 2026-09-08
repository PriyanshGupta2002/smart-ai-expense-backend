import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.whatsapp_connections import WhatsAppConnection
from app.services.whatsapp_service import WhatsAppService


class WhatsAppConnectionService:

    def __init__(self, db: Session, whatsapp_service: WhatsAppService):
        self.db = db
        self.whatsapp_service = whatsapp_service

    def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> WhatsAppConnection | None:

        return (
            self.db.query(WhatsAppConnection)
            .filter(WhatsAppConnection.user_id == user_id)
            .first()
        )

    def create_connection(
        self,
        user_id: uuid.UUID,
    ) -> WhatsAppConnection:

        connection = self.get_by_user_id(user_id)

        if connection:
            return connection

        connection = WhatsAppConnection(
            user_id=user_id,
            session_id=None,
            phone_number=None,
            connected=False,
            connected_at=None,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        return connection

    def set_session_id(
        self,
        connection: WhatsAppConnection,
        session_id: str,
    ) -> WhatsAppConnection:

        connection.session_id = session_id

        self.db.commit()
        self.db.refresh(connection)

        return connection

    def mark_connected(
        self,
        connection: WhatsAppConnection,
        phone_number: str | None = None,
    ) -> WhatsAppConnection:

        connection.connected = True
        connection.phone_number = phone_number
        connection.connected_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(connection)

        return connection

    async def disconnect(
        self,
        user_id: uuid.UUID,
    ) -> bool:

        connection = self.get_by_user_id(user_id)

        if not connection:
            return False

        # Delete OpenWA session first
        if connection.session_id:
            await self.whatsapp_service.delete_session(connection.session_id)

        # Delete local DB connection
        self.db.delete(connection)
        self.db.commit()

        return True
