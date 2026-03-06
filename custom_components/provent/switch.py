from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .commands import validate_command
from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator
from .entity import ProventEntity
from .parsing import parse_anti_smog_available, parse_anti_smog_state, parse_spd


@dataclass
class ProventSwitchEntityDescription(SwitchEntityDescription):
    command_on: str = ""
    command_off: str = ""
    value_fn: Callable[[dict], bool] | None = None
    exists_fn: Callable[[dict], bool] | None = None


class ProventSwitch(ProventEntity, SwitchEntity):
    entity_description: ProventSwitchEntityDescription

    def __init__(self, coordinator: ProventDataUpdateCoordinator, description: ProventSwitchEntityDescription) -> None:
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
    def is_on(self) -> bool:
        if not self.coordinator.data or not self.entity_description.value_fn:
            return False
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        await self.coordinator.async_send_command(validate_command(self.entity_description.command_on))

    async def async_turn_off(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        await self.coordinator.async_send_command(validate_command(self.entity_description.command_off))


SWITCH_DESCRIPTIONS: tuple[ProventSwitchEntityDescription, ...] = (
    ProventSwitchEntityDescription(
        key="ventilation_boost",
        name="Ventilation Boost",
        icon="mdi:weather-windy",
        command_on="spd:w1",
        command_off="spd:w0",
        value_fn=lambda data: (parse_spd(data.get("spd")).get("ventilation_remaining") or 0) > 0,
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventSwitchEntityDescription(
        key="humidity_control",
        name="Humidity Control",
        icon="mdi:water-percent",
        command_on="spd:h1",
        command_off="spd:h0",
        value_fn=lambda data: "h" in (parse_spd(data.get("spd")).get("flags") or "").lower(),
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventSwitchEntityDescription(
        key="co2_control",
        name="CO2 Control",
        icon="mdi:molecule-co2",
        command_on="spd:c1",
        command_off="spd:c0",
        value_fn=lambda data: "c" in (parse_spd(data.get("spd")).get("flags") or "").lower(),
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventSwitchEntityDescription(
        key="anti_smog_shield",
        name="Anti-Smog Shield",
        icon="mdi:shield-airplane",
        command_on="elf:t1",
        command_off="elf:t0",
        value_fn=lambda data: parse_anti_smog_state(data.get("elf")),
        exists_fn=lambda data: parse_anti_smog_available(data.get("elf")),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):  # type: ignore[no-untyped-def]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [ProventSwitch(coordinator, description) for description in SWITCH_DESCRIPTIONS]
    async_add_entities(entities)
