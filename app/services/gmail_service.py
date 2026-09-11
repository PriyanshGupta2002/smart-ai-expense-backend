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
from google.auth.exceptions import RefreshError
from email.mime.multipart import MIMEMultipart


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

        # No refresh token at all
        if not connection.refresh_token:
            connection.authorization_status = "reauthorization_required"
            self.db.commit()

            raise ValueError(
                "Google authorization has expired or been revoked. "
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

        try:
            # Ask Google for a new access token
            credentials.refresh(Request())

        except RefreshError as exc:
            # Refresh token itself is invalid / revoked / expired.
            # The user must authorize Google again.

            connection.authorization_status = "reauthorization_required"

            self.db.commit()

            raise ValueError(
                "Google authorization has expired or been revoked. "
                "Please reconnect your Google account."
            ) from exc

        # -----------------------------------------
        # Refresh succeeded
        # -----------------------------------------

        connection.access_token = credentials.token

        # Google may return a new refresh token.
        # If it does, save it.
        if credentials.refresh_token:
            connection.refresh_token = credentials.refresh_token

        # -----------------------------------------
        # Save token expiry
        # -----------------------------------------

        if credentials.expiry:
            expiry = credentials.expiry

            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            else:
                expiry = expiry.astimezone(timezone.utc)

            connection.token_expires_at = expiry

        # Authorization is working again
        connection.authorization_status = "authorized"

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
        html_body: str | None = None,
    ):
        """
        Send an email using the user's connected Gmail account.

        `body` is the plain-text fallback.
        `html_body` is optional and can be used for rich emails.
        """

        gmail = self.get_resource(user_id)

        profile = gmail.users().getProfile(userId="me").execute()
        email_address = profile["emailAddress"]

        if html_body:

            message = MIMEMultipart("alternative")

            message["To"] = email_address
            message["Subject"] = subject

            # Plain-text fallback
            # message.attach(MIMEText(body, "plain", "utf-8"))

            # Rich HTML version
            message.attach(MIMEText(html_body, "html", "utf-8"))

        else:
            message = MIMEText(
                body,
                "plain",
                "utf-8",
            )

            message["To"] = email_address
            message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

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
        print(
            "SENDING GMAIL",
            "user_id=",
            user_id,
            "gmail_account=",
            email_address,
        )

        return response

    def search_messages(
        self,
        user_id: UUID,
        query: str,
        max_results: int = 50,
        page_token: str | None = None,
    ):
        """Search for messages in the user's Gmail account using a query string."""

        gmail = self.get_resource(user_id)

        params = {
            "userId": "me",
            "q": query,
            "maxResults": max_results,
        }

        if page_token:
            params["pageToken"] = page_token

        response = gmail.users().messages().list(**params).execute()

        return {
            "messages": response.get("messages", []),
            "next_page_token": response.get("nextPageToken"),
        }

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
