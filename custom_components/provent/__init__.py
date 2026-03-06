from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.service import async_register_admin_service

from .api import ProventApiClient
from .coordinator import ProventDataUpdateCoordinator
from .const import (
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    CONF_API_PATH,
    CONF_USE_SSL,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEND_COMMAND,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): str,
        vol.Optional(ATTR_ENTRY_ID): str,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def async_handle_send_command(service_call) -> None:
        client = _get_client_for_service(hass, service_call.data.get(ATTR_ENTRY_ID))
        await client.async_send_command(service_call.data[ATTR_COMMAND])

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SEND_COMMAND,
        async_handle_send_command,
        schema=SERVICE_SEND_COMMAND_SCHEMA,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp_client.async_get_clientsession(hass)
    client = ProventApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_API_PATH],
        entry.data[CONF_USE_SSL],
    )

    coordinator = ProventDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await hass.config_entries.async_unload_entry_platforms(entry, PLATFORMS):
        return False

    hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


def _get_client_for_service(hass: HomeAssistant, entry_id: str | None):
    if not hass.data.get(DOMAIN):
        raise HomeAssistantError("No ProVent entries configured")
    if entry_id:
        entry_data = hass.data[DOMAIN].get(entry_id)
        if not entry_data:
            raise HomeAssistantError(f"Unknown entry {entry_id}")
    else:
        entry_data = next(iter(hass.data[DOMAIN].values()))
    return entry_data["client"]
