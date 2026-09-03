from __future__ import annotations

import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

from bs4 import BeautifulSoup


class GmailParser:
    """
    Converts a raw Gmail API message into a clean, application-friendly
    representation.

    This class does NOT determine whether an email is an expense,
    income, transfer, etc. Its only responsibility is parsing the email.
    """

    @staticmethod
    def _get_headers(
        message: dict[str, Any],
    ) -> dict[str, str]:
        headers = message.get("payload", {}).get("headers", [])

        return {
            header["name"].lower(): header["value"]
            for header in headers
            if "name" in header and "value" in header
        }

    @staticmethod
    def _decode_body(
        data: str | None,
    ) -> str:
        if not data:
            return ""

        try:
            decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

            return decoded.decode(
                "utf-8",
                errors="replace",
            )

        except Exception:
            return ""

    @staticmethod
    def _html_to_text(
        html: str,
    ) -> str:
        """
        Convert HTML email content into clean readable text.
        """

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # Remove elements that don't contain useful email content
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "head",
                "title",
            ]
        ):
            tag.decompose()

        # Preserve reasonable line breaks
        text = soup.get_text(
            separator="\n",
        )

        # Clean whitespace
        lines = []

        for line in text.splitlines():
            line = " ".join(line.split())

            if line:
                lines.append(line)

        return "\n".join(lines).strip()

    def _extract_body(
        self,
        payload: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Recursively extract text/plain and text/html bodies.

        Returns:
            (plain_text, html_text)
        """

        plain_text = []
        html_text = []

        mime_type = payload.get("mimeType")

        body = payload.get("body", {})
        data = body.get("data")

        if data:
            decoded = self._decode_body(data)

            if mime_type == "text/plain":
                plain_text.append(decoded)

            elif mime_type == "text/html":
                html_text.append(decoded)

        for part in payload.get("parts", []):
            part_plain, part_html = self._extract_body(part)

            if part_plain:
                plain_text.append(part_plain)

            if part_html:
                html_text.append(part_html)

        return (
            "\n".join(plain_text),
            "\n".join(html_text),
        )

    @staticmethod
    def _parse_date(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return parsedate_to_datetime(value)

        except (TypeError, ValueError, OverflowError):
            return None

    def parse_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Parse a raw Gmail API message.
        """

        headers = self._get_headers(message)

        plain_text, html_text = self._extract_body(message.get("payload", {}))

        plain_text = plain_text.strip()
        html_text = html_text.strip()

        # Prefer plain text.
        #
        # If the email is HTML-only, convert the HTML into
        # clean readable text.

        if plain_text not in (None, ""):
            text = plain_text
        else:
            text = self._html_to_text(html_text)

        return {
            "message_id": message.get("id"),
            "thread_id": message.get("threadId"),
            "sender": headers.get("from"),
            "recipient": headers.get("to"),
            "subject": headers.get("subject"),
            "date": self._parse_date(headers.get("date")),
            "plain_text": plain_text,
            "html": html_text,
            "text": text,
            "snippet": message.get("snippet"),
            "label_ids": message.get(
                "labelIds",
                [],
            ),
        }
