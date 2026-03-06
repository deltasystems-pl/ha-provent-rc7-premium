from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTemperature

from .commands import validate_command
from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator
from .entity import ProventEntity
from .parsing import parse_device_state, parse_spd


@dataclass
class ProventNumberEntityDescription(NumberEntityDescription):
    command_fn: Callable[[float], str] | None = None
    value_fn: Callable[[dict], float | None] | None = None
    exists_fn: Callable[[dict], bool] | None = None


class ProventNumber(ProventEntity, NumberEntity):
    entity_description: ProventNumberEntityDescription

    def __init__(self, coordinator: ProventDataUpdateCoordinator, description: ProventNumberEntityDescription) -> None:
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
    def native_value(self) -> float | None:
        if not self.coordinator.data or not self.entity_description.value_fn:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        if not self.entity_description.command_fn:
            return
        await self.coordinator.async_send_command(validate_command(self.entity_description.command_fn(value)))


NUMBER_DESCRIPTIONS: tuple[ProventNumberEntityDescription, ...] = (
    ProventNumberEntityDescription(
        key="fan_speed",
        name="Fan Speed Setpoint",
        icon="mdi:fan-chevron-up",
        native_min_value=0,
        native_max_value=4,
        native_step=1,
        mode="slider",
        command_fn=lambda value: f"spd:b{int(value)}",
        value_fn=lambda data: parse_spd(data.get("spd")).get("speed"),
        exists_fn=lambda data: data.get("spd") is not None,
    ),
    ProventNumberEntityDescription(
        key="heating_setpoint",
        name="Heating Setpoint",
        icon="mdi:radiator",
        native_min_value=4,
        native_max_value=35,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode="slider",
        command_fn=lambda value: f"nag:T{int(value)}",
        value_fn=lambda data: parse_device_state(data.get("nag")).get("setpoint"),
        exists_fn=lambda data: data.get("nag") is not None,
    ),
    ProventNumberEntityDescription(
        key="cooling_setpoint",
        name="Cooling Setpoint",
        icon="mdi:snowflake-thermometer",
        native_min_value=4,
        native_max_value=35,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode="slider",
        command_fn=lambda value: f"chl:T{int(value)}",
        value_fn=lambda data: parse_device_state(data.get("chl")).get("setpoint"),
        exists_fn=lambda data: data.get("chl") is not None,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):  # type: ignore[no-untyped-def]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [ProventNumber(coordinator, description) for description in NUMBER_DESCRIPTIONS]
    async_add_entities(entities)
