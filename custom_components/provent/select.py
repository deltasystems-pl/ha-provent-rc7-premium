from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .commands import validate_command
from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator
from .entity import ProventEntity
from .parsing import parse_bypass_or_gwc_mode, parse_season, parse_spd_modes


@dataclass
class ProventSelectEntityDescription(SelectEntityDescription):
    command_fn: Callable[[str], str] | None = None
    value_fn: Callable[[dict], str | None] | None = None
    exists_fn: Callable[[dict], bool] | None = None


class ProventSelect(ProventEntity, SelectEntity):
    entity_description: ProventSelectEntityDescription

    def __init__(self, coordinator: ProventDataUpdateCoordinator, description: ProventSelectEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if not self.coordinator.data or not self.entity_description.exists_fn:
            return True
        return self.entity_description.exists_fn(self.coordinator.data)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data or not self.entity_description.value_fn:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        if not self.entity_description.command_fn:
            return
        await self.coordinator.async_send_command(validate_command(self.entity_description.command_fn(option)))


SELECT_DESCRIPTIONS: tuple[ProventSelectEntityDescription, ...] = (
    ProventSelectEntityDescription(
        key="ventilation_mode",
        name="Ventilation Mode",
        icon="mdi:hvac",
        options=["auto", "manual"],
        command_fn=lambda option: f"spd:t{'a' if option == 'auto' else 'm'}",
        value_fn=lambda data: parse_spd_modes(data.get("spd")).get("mode"),
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventSelectEntityDescription(
        key="airflow_mode",
        name="Airflow Mode",
        icon="mdi:air-filter",
        options=["both", "supply_only", "extract_only"],
        command_fn=lambda option: {"both": "spd:po", "supply_only": "spd:pn", "extract_only": "spd:pw"}[option],
        value_fn=lambda data: parse_spd_modes(data.get("spd")).get("vent_mode"),
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventSelectEntityDescription(
        key="season_override",
        name="Season Override",
        icon="mdi:weather-partly-snowy-rainy",
        options=["auto", "forced_winter", "forced_summer"],
        command_fn=lambda option: {"auto": "sez:sa", "forced_winter": "sez:sz", "forced_summer": "sez:sl"}[option],
        value_fn=lambda data: parse_season(data.get("sez")).get("mode"),
        exists_fn=lambda data: data.get("sez") is not None,
    ),
    ProventSelectEntityDescription(
        key="bypass_mode",
        name="Bypass Mode",
        icon="mdi:swap-horizontal",
        options=["auto", "forced_on", "forced_off"],
        command_fn=lambda option: {"auto": "bps:ta", "forced_on": "bps:tz", "forced_off": "bps:tw"}[option],
        value_fn=lambda data: parse_bypass_or_gwc_mode(data.get("bps")),
        exists_fn=lambda data: data.get("bps") is not None,
    ),
    ProventSelectEntityDescription(
        key="gwc_mode",
        name="GWC Mode",
        icon="mdi:water",
        options=["auto", "forced_on", "forced_off"],
        command_fn=lambda option: {"auto": "gwc:ta", "forced_on": "gwc:tz", "forced_off": "gwc:tw"}[option],
        value_fn=lambda data: parse_bypass_or_gwc_mode(data.get("gwc")),
        exists_fn=lambda data: data.get("gwc") is not None,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):  # type: ignore[no-untyped-def]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [ProventSelect(coordinator, description) for description in SELECT_DESCRIPTIONS]
    async_add_entities(entities)
