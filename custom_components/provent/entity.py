from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USE_SSL, DOMAIN, MANUFACTURER, MODEL
from .coordinator import ProventDataUpdateCoordinator


class ProventEntity(CoordinatorEntity[ProventDataUpdateCoordinator]):
    def __init__(self, coordinator: ProventDataUpdateCoordinator, entity_key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        entry = self.coordinator.entry
        return DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=self._configuration_url(),
        )

    def _configuration_url(self) -> str | None:
        """Link to the WebManipulator web UI so the device card shows 'Visit device'."""
        data = self.coordinator.entry.data
        host = data.get(CONF_HOST)
        if not host:
            return None
        use_ssl = bool(data.get(CONF_USE_SSL))
        scheme = "https" if use_ssl else "http"
        default_port = 443 if use_ssl else 80
        port = data.get(CONF_PORT)
        try:
            has_custom_port = port is not None and int(port) != default_port
        except (TypeError, ValueError):
            has_custom_port = False
        return f"{scheme}://{host}:{port}" if has_custom_port else f"{scheme}://{host}"
