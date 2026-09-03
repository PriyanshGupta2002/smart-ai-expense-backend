import secrets

from google_auth_oauthlib.flow import Flow

from app.core.config import settings

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]


class GoogleOAuthService:

    def generate_state(self) -> str:
        return secrets.token_urlsafe(32)

    def create_flow(self) -> Flow:

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        return Flow.from_client_config(
            client_config,
            scopes=GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

    def get_authorization_url(
        self,
        state: str,
    ) -> tuple[str, str]:

        flow = self.create_flow()

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        return authorization_url, flow.code_verifier

    def exchange_code(
        self,
        code: str,
        code_verifier: str,
    ):

        flow = self.create_flow()

        flow.fetch_token(
            code=code,
            code_verifier=code_verifier,
        )

        return flow.credentials
