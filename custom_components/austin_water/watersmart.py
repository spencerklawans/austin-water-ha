from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import imaplib
import logging
import re
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    CONF_EMAIL_FOLDER,
    CONF_EMAIL_HOST,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_PORT,
    CONF_EMAIL_USERNAME,
    CONF_SUBJECT_FILTER,
    CONF_WAIT_TIME,
    DOWNLOAD_URL,
    EMAIL_SUBJECT_HINT,
    LOGIN_PATH,
    VERIFY_PATH,
)

_LOGGER = logging.getLogger(__name__)

_CODE_PATTERN = re.compile(r"(\d{6})")


@dataclass
class UsageRow:
    account_number: str
    read_date: datetime
    meter_reading: float
    gallons: float
    leak_detected: bool
    leak_volume: float
    meter_class: str

    @classmethod
    def from_csv(cls, row: dict[str, str]) -> "UsageRow":
        read_date_raw = (row.get("Read Date", "") or "").replace("  ", " ").strip()
        return cls(
            account_number=row.get("Account Number", ""),
            read_date=datetime.strptime(read_date_raw, "%Y-%m-%d %I:%M:%S %p").replace(tzinfo=timezone.utc),
            meter_reading=float(row.get("Meter Reading", 0) or 0),
            gallons=float(row.get("Gallons", 0) or 0),
            leak_detected=str(row.get("Leak Detected", "0")).strip().lower()
            not in ("0", "false", "no", ""),
            leak_volume=float(row.get("Leak Volume", 0) or 0),
            meter_class=row.get("Meter Class", ""),
        )


class WaterSmartClient:
    """Client for Austin WaterSmart portal."""

    def __init__(self, session: ClientSession, credentials: dict[str, Any]):
        self._session = session
        self._credentials = credentials
        self._logged_in = False

    async def login(self) -> None:
        """Perform login flow, including optional 2FA."""
        username = self._credentials.get("username")
        password = self._credentials.get("password")

        payload = {"username": username, "password": password}
        _LOGGER.debug("Attempting login for %s", username)
        try:
            async with self._session.post(LOGIN_PATH, data=payload, allow_redirects=True) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise ClientError(f"Login failed with status {resp.status}")
                if self._requires_2fa(text):
                    code = await self._wait_for_code()
                    await self._submit_2fa(code)
            self._logged_in = True
        except ClientError as err:
            _LOGGER.error("Unable to login: %s", err)
            raise

    async def fetch_usage(self) -> list[UsageRow]:
        """Download and parse the hourly usage CSV."""
        if not self._logged_in:
            await self.login()

        async with self._session.get(DOWNLOAD_URL) as resp:
            if resp.status >= 400:
                raise ClientError(f"Failed to download CSV: {resp.status}")
            content = await resp.text()
        reader = csv.DictReader(content.splitlines())
        usage: list[UsageRow] = []
        for row in reader:
            try:
                usage.append(UsageRow.from_csv(row))
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Skipping row because of parse error: %s", err)
        return usage

    def _requires_2fa(self, text: str) -> bool:
        markers = ["verification", "2fa", "two-factor", "otp"]
        lower = text.lower()
        return any(marker in lower for marker in markers)

    async def _submit_2fa(self, code: str) -> None:
        payload = {"code": code}
        async with self._session.post(VERIFY_PATH, data=payload, allow_redirects=True) as resp:
            if resp.status >= 400:
                raise ClientError(f"2FA verification failed with status {resp.status}")
            _LOGGER.debug("2FA verification completed")

    async def _wait_for_code(self) -> str:
        wait_time = int(self._credentials.get(CONF_WAIT_TIME, 90))
        subject_filter = self._credentials.get(CONF_SUBJECT_FILTER, EMAIL_SUBJECT_HINT)
        _LOGGER.debug("Waiting up to %s seconds for verification email", wait_time)
        for _ in range(wait_time // 5):
            code = await asyncio.get_running_loop().run_in_executor(
                None, self._read_email_code, subject_filter
            )
            if code:
                return code
            await asyncio.sleep(5)
        raise ClientError("Timed out waiting for verification code")

    def _read_email_code(self, subject_filter: str) -> str | None:
        host = self._credentials.get(CONF_EMAIL_HOST)
        if not host:
            _LOGGER.debug("No email host configured; skipping 2FA retrieval")
            return None
        username = self._credentials.get(CONF_EMAIL_USERNAME)
        password = self._credentials.get(CONF_EMAIL_PASSWORD)
        folder = self._credentials.get(CONF_EMAIL_FOLDER, "INBOX")
        port = int(self._credentials.get(CONF_EMAIL_PORT, 993))

        try:
            with imaplib.IMAP4_SSL(host, port) as imap:
                imap.login(username, password)
                imap.select(folder)
                status, data = imap.search(None, "UNSEEN")
                if status != "OK":
                    return None
                for num in data[0].split():
                    status, msg_data = imap.fetch(num, "(BODY[HEADER])")
                    if status != "OK":
                        continue
                    headers = msg_data[0][1].decode("utf-8", errors="ignore")
                    if subject_filter.lower() not in headers.lower():
                        continue
                    match = _CODE_PATTERN.search(headers)
                    if match:
                        imap.store(num, "+FLAGS", "(\\Seen)")
                        return match.group(1)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to read verification email: %s", err)
        return None
