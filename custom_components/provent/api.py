from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import DEFAULT_API_PATH

_LOGGER = logging.getLogger(__name__)

class ProventApiError(Exception):
    pass

class ProventApiClient:
    def __init__(self, session: aiohttp.ClientSession, host: str, port: int, api_path: str, use_ssl: bool) -> None:
        scheme = "https" if use_ssl else "http"
        path = api_path or DEFAULT_API_PATH
        if not path.startswith("/"):
            path = f"/{path}"
        path = path.rstrip("/")
        self._base_url = f"{scheme}://{host}:{port}{path}"
        self._session = session

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/{endpoint}"

    async def async_get_all(self) -> dict[str, Any]:
        response = await self._post("getdata.php", {"variable": ["all"]})
        if not isinstance(response, dict):
            raise ProventApiError("Unexpected payload from getdata.php")
        payload = response.get("all")
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError as err:
                raise ProventApiError("Failed to parse returned JSON") from err
        if isinstance(payload, dict):
            return payload
        return response

    async def async_send_command(self, command: str) -> None:
        if not command:
            raise ProventApiError("Empty command")
        await self._post("savedata.php", {"data": command})

    async def _post(self, endpoint: str, data: dict[str, Any]) -> Any:
        url = self._build_url(endpoint)
        _LOGGER.debug("Posting %s to %s", data, url)
        async with async_timeout.timeout(10):
            response = await self._session.post(url, data=data)
        if response.status != 200:
            raise ProventApiError(f"Unexpected status code {response.status}")
        try:
            return await response.json()
        except aiohttp.ContentTypeError:
            text = await response.text()
            _LOGGER.debug("Response text: %s", text)
            try:
                return json.loads(text)
            except json.JSONDecodeError as err:
                raise ProventApiError("API response is not JSON") from err
