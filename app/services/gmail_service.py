# # app/services/gmail_service.py

# from uuid import UUID
# import base64
# from email.mime.text import MIMEText

# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build
# from sqlalchemy.orm import Session

# from app.models.google_connections import GoogleConnection
# from app.core.config import settings


# class GmailService:

#     def __init__(self, db: Session):
#         self.db = db

#     def get_connection(
#         self,
#         user_id: UUID,
#     ) -> GoogleConnection | None:
#         return (
#             self.db.query(GoogleConnection)
#             .filter(GoogleConnection.user_id == user_id)
#             .first()
#         )

#     def get_resource(
#         self,
#         user_id: UUID,
#     ):
#         connection = self.get_connection(user_id)

#         if not connection:
#             raise ValueError("Google account is not connected")

#         credentials = Credentials(
#             token=connection.access_token,
#             refresh_token=connection.refresh_token,
#             token_uri="https://oauth2.googleapis.com/token",
#             client_id=settings.GOOGLE_CLIENT_ID,
#             client_secret=settings.GOOGLE_CLIENT_SECRET,
#             scopes=connection.scopes,
#         )

#         service = build(
#             "gmail",
#             "v1",
#             credentials=credentials,
#         )

#         return service

#     def send_email(
#         self,
#         user_id: UUID,
#         subject: str,
#         body: str,
#     ):
#         """
#         Send an email using the user's connected Gmail account.
#         """

#         gmail = self.get_resource(user_id)
#         profile = gmail.users().getProfile(userId="me").execute()

#         message = MIMEText(body)

#         message["To"] = profile["emailAddress"]
#         message["Subject"] = subject

#         encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

#         response = (
#             gmail.users()
#             .messages()
#             .send(
#                 userId="me",
#                 body={
#                     "raw": encoded_message,
#                 },
#             )
#             .execute()
#         )

#         return response

# app/services/gmail_service.py
# app/services/gmail_service.py

from uuid import UUID
import base64

from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from sqlalchemy.orm import Session

from app.models.google_connections import GoogleConnection
from app.core.config import settings


class GmailService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # GET GOOGLE CONNECTION
    # ============================================================

    def get_connection(
        self,
        user_id: UUID,
    ) -> GoogleConnection | None:

        return (
            self.db.query(GoogleConnection)
            .filter(GoogleConnection.user_id == user_id)
            .first()
        )

    # ============================================================
    # REFRESH ACCESS TOKEN
    # ============================================================

    def _refresh_token(
        self,
        connection: GoogleConnection,
    ) -> None:

        if not connection.refresh_token:
            raise ValueError(
                "Google access token has expired and no refresh token is available. "
                "Please reconnect your Google account."
            )

        credentials = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=connection.scopes,
        )

        # Ask Google for a new access token
        credentials.refresh(Request())

        # -----------------------------------------
        # Save new access token
        # -----------------------------------------

        connection.access_token = credentials.token

        # Google credentials.expiry is normally timezone-aware,
        # but normalize it before storing.
        if credentials.expiry:

            expiry = credentials.expiry

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            else:
                expiry = expiry.astimezone(timezone.utc)

            connection.token_expires_at = expiry

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

    # ============================================================
    # GET GMAIL RESOURCE
    # ============================================================

    def get_resource(
        self,
        user_id: UUID,
    ):

        connection = self.get_connection(user_id)

        if not connection:
            raise ValueError("Google account is not connected")

        # --------------------------------------------------------
        # Normalize DB expiry to timezone-aware UTC
        # --------------------------------------------------------

        expires_at = connection.token_expires_at

        if expires_at:

            if expires_at.tzinfo is None:
                # DB returned a naive datetime.
                # Treat it as UTC.
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at = expires_at.astimezone(timezone.utc)

        # --------------------------------------------------------
        # Refresh slightly BEFORE actual expiration
        #
        # 60-second buffer prevents race conditions where the
        # token expires while an API request is being made.
        # --------------------------------------------------------

        should_refresh = expires_at is not None and datetime.now(
            timezone.utc
        ) >= expires_at - timedelta(seconds=60)

        if should_refresh:

            self._refresh_token(connection)

        # --------------------------------------------------------
        # Create credentials using the latest DB values
        # --------------------------------------------------------

        credentials = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=connection.scopes,
        )

        # --------------------------------------------------------
        # Build Gmail API client
        # --------------------------------------------------------

        gmail = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

        return gmail

    # ============================================================
    # SEND EMAIL
    # ============================================================

    def send_email(
        self,
        user_id: UUID,
        subject: str,
        body: str,
    ):
        """
        Send an email using the user's connected Gmail account.

        The email is sent FROM the user's connected Gmail account
        TO that same Gmail account.
        """

        gmail = self.get_resource(user_id)

        # Get the connected Gmail address
        profile = gmail.users().getProfile(userId="me").execute()

        email_address = profile["emailAddress"]

        # Create email
        message = MIMEText(
            body,
            "plain",
            "utf-8",
        )

        message["To"] = email_address
        message["Subject"] = subject

        # Encode for Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send
        response = (
            gmail.users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw": encoded_message,
                },
            )
            .execute()
        )

        return response

    def search_messages(
        self,
        user_id: UUID,
        query: str,
        max_results: int = 50,
    ):
        """ "Search for messages in the user's Gmail account using a query string."""
        gmail = self.get_resource(user_id)
        response = (
            gmail.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return response.get("messages", [])

    def get_message(
        self,
        user_id: UUID,
        message_id: str,
    ):
        """
        Fetch a complete Gmail message.
        """

        gmail = self.get_resource(user_id)

        return (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )
