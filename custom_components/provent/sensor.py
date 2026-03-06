from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator

DEVICE_LETTERS = ["a", "b", "c", "d"]
TEMP_SENSOR_KEYS = [
    (f"t{block}{letter}", f"T{block} {letter.upper()}")
    for block in range(1, 6)
    for letter in DEVICE_LETTERS
]

DEVICE_STATUS_RE = re.compile(r"(?P<setpoint>\d+)(?P<temperature>[+-]?\d+\.\d)(?P<status>.{3})")


@dataclass
class ProventSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None


class ProventSensor(CoordinatorEntity, SensorEntity):
    entity_description: ProventSensorEntityDescription

    def __init__(self, coordinator: ProventDataUpdateCoordinator, description: ProventSensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{coordinator.entry.title} {description.name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
        )

    @property
    def native_value(self) -> Any:
        if not self.entity_description.value_fn or not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value or len(value) < 11:
        return None
    try:
        hour = int(value[1:3])
        minute = int(value[3:5])
        day = int(value[5:7])
        month = int(value[7:9])
        year = 2000 + int(value[9:11])
        return datetime(year, month, day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    except ValueError:
        return None


def _parse_spd(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    result: dict[str, Any] = {}
    if value[0].isdigit():
        result["speed"] = int(value[0])
    if len(value) >= 3:
        tail = value[-2:]
        if tail.isdigit():
            result["ventilation_remaining"] = int(tail)
            result["flags"] = value[1:-2]
        else:
            result["flags"] = value[1:]
    else:
        result["flags"] = value[1:]
    return result


def _parse_season(value: str | None) -> dict[str, str | None]:
    season_map = {"z": "winter", "l": "summer"}
    mode_map = {"a": "auto", "z": "forced_winter", "l": "forced_summer"}
    result = {"current": None, "mode": None}
    if not value or len(value) < 2:
        return result
    result["current"] = season_map.get(value[0].lower())
    result["mode"] = mode_map.get(value[1].lower())
    return result


def _parse_device_state(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    match = DEVICE_STATUS_RE.match(value)
    if not match:
        return {}
    data = match.groupdict()
    return {
        "setpoint": _coerce_float(data["setpoint"]),
        "temperature": _coerce_float(data["temperature"]),
        "status": data["status"].strip(),
    }


def _parse_temperatures(value: str | None) -> dict[str, float | None]:
    if not value:
        return {}
    result: dict[str, float | None] = {}
    segments = [segment.strip() for segment in value.split(";") if segment.strip()]
    key_index = 0
    for segment in segments:
        parts = [part.strip() for part in segment.split(",") if part.strip()]
        for part in parts:
            if key_index >= len(TEMP_SENSOR_KEYS):
                break
            key = TEMP_SENSOR_KEYS[key_index][0]
            if part == "---":
                result[key] = None
            else:
                try:
                    result[key] = float(part)
                except ValueError:
                    result[key] = None
            key_index += 1
        if key_index >= len(TEMP_SENSOR_KEYS):
            break
    return result


def _parse_hex(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


def _get_temp_value(data: dict[str, Any], key: str) -> float | None:
    temps = _parse_temperatures(data.get("tmp"))
    return temps.get(key)


general_sensor_descriptions: tuple[ProventSensorEntityDescription, ...] = (
    ProventSensorEntityDescription(
        key="dat",
        name="Control Timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _parse_timestamp(data.get("dat")),
    ),
    ProventSensorEntityDescription(
        key="spd_speed",
        name="Fan Speed",
        icon="mdi:fan",
        native_unit_of_measurement="step",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_spd(data.get("spd")).get("speed"),
    ),
    ProventSensorEntityDescription(
        key="spd_flags",
        name="Fan Flags",
        icon="mdi:chart-bell-curve",
        value_fn=lambda data: _parse_spd(data.get("spd")).get("flags"),
    ),
    ProventSensorEntityDescription(
        key="spd_remaining",
        name="Ventilation Remaining",
        icon="mdi:timer",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_spd(data.get("spd")).get("ventilation_remaining"),
    ),
    ProventSensorEntityDescription(
        key="flt",
        name="Filter Replacement Days",
        icon="mdi:filter",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _coerce_int(data.get("flt")),
    ),
    ProventSensorEntityDescription(
        key="bps",
        name="Bypass Position",
        icon="mdi:swap-vertical",
        native_unit_of_measurement="value",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_hex(data.get("bps")),
    ),
    ProventSensorEntityDescription(
        key="gwc",
        name="GWC Position",
        icon="mdi:water",
        native_unit_of_measurement="value",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_hex(data.get("gwc")),
    ),
    ProventSensorEntityDescription(
        key="sez_current",
        name="Current Season",
        icon="mdi:weather-lightning",
        value_fn=lambda data: _parse_season(data.get("sez")).get("current"),
    ),
    ProventSensorEntityDescription(
        key="sez_mode",
        name="Season Mode",
        icon="mdi:calendar-sync",
        value_fn=lambda data: _parse_season(data.get("sez")).get("mode"),
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
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_device_state(data.get("nag")).get("setpoint"),
    ),
    ProventSensorEntityDescription(
        key="nag_temp",
        name="Heating Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_device_state(data.get("nag")).get("temperature"),
    ),
    ProventSensorEntityDescription(
        key="nag_status",
        name="Heating Status",
        icon="mdi:thermometer-check",
        value_fn=lambda data: _parse_device_state(data.get("nag")).get("status"),
    ),
    ProventSensorEntityDescription(
        key="chl_setpoint",
        name="Cooling Setpoint",
        icon="mdi:snowflake",
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_device_state(data.get("chl")).get("setpoint"),
    ),
    ProventSensorEntityDescription(
        key="chl_temp",
        name="Cooling Temperature",
        icon="mdi:snowflake",
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_device_state(data.get("chl")).get("temperature"),
    ),
    ProventSensorEntityDescription(
        key="chl_status",
        name="Cooling Status",
        icon="mdi:snowflake-alert",
        value_fn=lambda data: _parse_device_state(data.get("chl")).get("status"),
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
                native_unit_of_measurement=TEMP_CELSIUS,
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
