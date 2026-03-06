from __future__ import annotations

import logging

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ProventApiClient, ProventApiError
from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class ProventDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: ProventApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_all()
        except ProventApiError as err:
            raise UpdateFailed(err) from err

    async def async_send_command(self, command: str) -> None:
        try:
            await self.client.async_send_command(command)
        except ProventApiError as err:
            raise UpdateFailed(err) from err
        await self.async_request_refresh()
