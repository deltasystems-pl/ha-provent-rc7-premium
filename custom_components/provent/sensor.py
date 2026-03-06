from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator
from .entity import ProventEntity
from .parsing import (
    TEMP_SENSOR_KEYS,
    coerce_int,
    parse_device_state,
    parse_hex,
    parse_season,
    parse_spd,
    parse_temperatures,
    parse_timestamp,
)


@dataclass
class ProventSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None


class ProventSensor(ProventEntity, SensorEntity):
    entity_description: ProventSensorEntityDescription

    def __init__(self, coordinator: ProventDataUpdateCoordinator, description: ProventSensorEntityDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        if not self.entity_description.value_fn or not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)


def _get_temp_value(data: dict[str, Any], key: str) -> float | None:
    temps = parse_temperatures(data.get("tmp"))
    return temps.get(key)


general_sensor_descriptions: tuple[ProventSensorEntityDescription, ...] = (
    ProventSensorEntityDescription(
        key="dat",
        name="Control Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: parse_timestamp(data.get("dat")),
    ),
    ProventSensorEntityDescription(
        key="spd_speed",
        name="Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="step",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_spd(data.get("spd")).get("speed"),
    ),
    ProventSensorEntityDescription(
        key="spd_flags",
        name="Fan Flags",
        icon="mdi:chart-bell-curve",
        value_fn=lambda data: parse_spd(data.get("spd")).get("flags"),
    ),
    ProventSensorEntityDescription(
        key="spd_remaining",
        name="Ventilation Remaining",
        icon="mdi:timer",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_spd(data.get("spd")).get("ventilation_remaining"),
    ),
    ProventSensorEntityDescription(
        key="flt",
        name="Filter Replacement Days",
        icon="mdi:filter",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: coerce_int(data.get("flt")),
    ),
    ProventSensorEntityDescription(
        key="bps",
        name="Bypass Position",
        icon="mdi:swap-vertical",
        native_unit_of_measurement="value",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_hex(data.get("bps")),
    ),
    ProventSensorEntityDescription(
        key="gwc",
        name="GWC Position",
        icon="mdi:water",
        native_unit_of_measurement="value",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_hex(data.get("gwc")),
    ),
    ProventSensorEntityDescription(
        key="sez_current",
        name="Current Season",
        icon="mdi:weather-lightning",
        value_fn=lambda data: parse_season(data.get("sez")).get("current"),
    ),
    ProventSensorEntityDescription(
        key="sez_mode",
        name="Season Mode",
        icon="mdi:calendar-sync",
        value_fn=lambda data: parse_season(data.get("sez")).get("mode"),
    ),
    ProventSensorEntityDescription(
        key="stn",
        name="System State",
        icon="mdi:shield-check",
        value_fn=lambda data: data.get("stn"),
    ),
    ProventSensorEntityDescription(
        key="asc",
        name="Alarm State",
        icon="mdi:alarm-light",
        value_fn=lambda data: data.get("asc"),
    ),
    ProventSensorEntityDescription(
        key="iaw",
        name="Active Notes",
        icon="mdi:alert-circle-outline",
        value_fn=lambda data: ", ".join(data.get("iaw", [])),
    ),
    ProventSensorEntityDescription(
        key="nag_setpoint",
        name="Heating Setpoint",
        icon="mdi:radiator",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_device_state(data.get("nag")).get("setpoint"),
    ),
    ProventSensorEntityDescription(
        key="nag_temp",
        name="Heating Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_device_state(data.get("nag")).get("temperature"),
    ),
    ProventSensorEntityDescription(
        key="nag_status",
        name="Heating Status",
        icon="mdi:thermometer-check",
        value_fn=lambda data: parse_device_state(data.get("nag")).get("status"),
    ),
    ProventSensorEntityDescription(
        key="chl_setpoint",
        name="Cooling Setpoint",
        icon="mdi:snowflake",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_device_state(data.get("chl")).get("setpoint"),
    ),
    ProventSensorEntityDescription(
        key="chl_temp",
        name="Cooling Temperature",
        icon="mdi:snowflake",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: parse_device_state(data.get("chl")).get("temperature"),
    ),
    ProventSensorEntityDescription(
        key="chl_status",
        name="Cooling Status",
        icon="mdi:snowflake-alert",
        value_fn=lambda data: parse_device_state(data.get("chl")).get("status"),
    ),
    ProventSensorEntityDescription(
        key="elf",
        name="Electrofilter Status",
        icon="mdi:cloud-filter",
        value_fn=lambda data: data.get("elf"),
    ),
)


def _build_temp_descriptions() -> tuple[ProventSensorEntityDescription, ...]:
    descriptions: list[ProventSensorEntityDescription] = []
    for key, label in TEMP_SENSOR_KEYS:
        descriptions.append(
            ProventSensorEntityDescription(
                key=f"tmp_{key}",
                name=f"Temperature {label}",
                icon="mdi:thermometer",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, temp_key=key: _get_temp_value(data, temp_key),
            )
        )
    return tuple(descriptions)


async def async_setup_entry(hass, entry, async_add_entities):  # type: ignore[no-untyped-def]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = [ProventSensor(coordinator, description) for description in general_sensor_descriptions]
    entities += [ProventSensor(coordinator, description) for description in _build_temp_descriptions()]
    async_add_entities(entities)
