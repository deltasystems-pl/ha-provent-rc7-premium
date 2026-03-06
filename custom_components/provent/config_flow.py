from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ProventApiClient, ProventApiError
from .const import (
    CONF_API_PATH,
    CONF_USE_SSL,
    DEFAULT_API_PATH,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class ProventConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            use_ssl = user_input[CONF_USE_SSL]
            api_path = user_input[CONF_API_PATH]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            try:
                await self._async_test_connection(host, port, use_ssl, api_path)
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except ProventApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}{api_path}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_USE_SSL: use_ssl,
                        CONF_API_PATH: api_path,
                        CONF_NAME: name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST) if user_input else ""): str,
                    vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME) if user_input else DEFAULT_NAME): str,
                    vol.Optional(
                        CONF_PORT,
                        default=(user_input.get(CONF_PORT) if user_input else DEFAULT_PORT),
                    ): vol.All(vol.Coerce(int)),
                    vol.Optional(CONF_API_PATH, default=user_input.get(CONF_API_PATH, DEFAULT_API_PATH) if user_input else DEFAULT_API_PATH): str,
                    vol.Optional(CONF_USE_SSL, default=user_input.get(CONF_USE_SSL, False) if user_input else False): cv.boolean,
                }
            ),
            errors=errors,
        )

    async def _async_test_connection(self, host: str, port: int, use_ssl: bool, api_path: str) -> None:
        session = async_get_clientsession(self.hass)
        client = ProventApiClient(session, host, port, api_path, use_ssl)
        await client.async_get_all()
