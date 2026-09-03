# app/services/google_credentials_service.py

from uuid import UUID

from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.google_connections import GoogleConnection


class GoogleCredentialsService:

    def __init__(self, db: Session):
        self.db = db

    def get_credentials(
        self,
        user_id: UUID,
    ) -> Credentials | None:

        connection = (
            self.db.query(GoogleConnection)
            .filter(GoogleConnection.user_id == user_id)
            .first()
        )

        if not connection:
            return None

        return Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=connection.scopes,
        )
