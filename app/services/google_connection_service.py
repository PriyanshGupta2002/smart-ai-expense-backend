from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.google_connections import GoogleConnection
from app.tasks.gmail_tasks import sync_user_gmail


class GoogleConnectionService:

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> GoogleConnection | None:
        return (
            self.db.query(GoogleConnection)
            .filter(GoogleConnection.user_id == user_id)
            .first()
        )

    def save_connection(
        self,
        user_id: UUID,
        access_token: str,
        refresh_token: str | None,
        token_expires_at: datetime | None,
        scopes: list[str] | None,
    ) -> GoogleConnection:

        connection = self.get_by_user_id(user_id)

        if connection:
            # -----------------------------------------
            # Existing connection = user is reconnecting
            # -----------------------------------------

            connection.access_token = access_token

            # Google may not return a refresh token
            # every time, so don't overwrite an existing one.
            if refresh_token:
                connection.refresh_token = refresh_token

            connection.token_expires_at = token_expires_at
            connection.scopes = scopes

            # OAuth succeeded, so authorization is active again.
            connection.authorization_status = "active"

        else:
            # -----------------------------------------
            # First-time Google connection
            # -----------------------------------------

            connection = GoogleConnection(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                scopes=scopes,
                authorization_status="active",
            )

            self.db.add(connection)

        self.db.commit()
        self.db.refresh(connection)

        # Start Gmail sync after successful connection/reconnection.
        sync_user_gmail.delay(str(user_id))

        return connection

    def disconnect(
        self,
        user_id: UUID,
    ) -> bool:

        connection = self.get_by_user_id(user_id)

        if not connection:
            return False

        self.db.delete(connection)
        self.db.commit()

        return True
