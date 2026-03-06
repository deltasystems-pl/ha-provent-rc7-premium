from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ProventDataUpdateCoordinator


class ProventEntity(CoordinatorEntity[ProventDataUpdateCoordinator]):
    def __init__(self, coordinator: ProventDataUpdateCoordinator, entity_key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
        )
