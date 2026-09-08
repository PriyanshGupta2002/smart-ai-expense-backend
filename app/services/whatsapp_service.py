import httpx


class WhatsAppService:

    def __init__(
        self,
        base_url: str,
        api_key: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_session(
        self,
        name: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={
                    "name": name,
                },
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def start_session(
        self,
        session_id: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions/" f"{session_id}/start"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def get_qr(
        self,
        session_id: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions/" f"{session_id}/qr"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers(),
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def get_session(
        self,
        session_id: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions/" f"{session_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers(),
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def create_webhook(
        self,
        session_id: str,
        webhook_url: str,
    ):
        url = f"{self.base_url}" f"/api/sessions/{session_id}/webhooks"

        payload = {
            "url": webhook_url,
            "events": [
                "message.received",
                "session.status",
            ],
        }

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

            response.raise_for_status()

            return response.json()

    async def send_text(
        self,
        session_id: str,
        chat_id: str,
        text: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions/" f"{session_id}/messages/send-text"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={
                    "chatId": chat_id,
                    "text": text,
                },
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def get_session(
        self,
        session_id: str,
    ) -> dict:

        url = f"{self.base_url}/api/sessions/{session_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers(),
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

    async def delete_session(
        self,
        session_id: str,
    ) -> bool:

        url = f"{self.base_url}/api/sessions/{session_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=self._headers(),
                timeout=30,
            )

            response.raise_for_status()

            return True
