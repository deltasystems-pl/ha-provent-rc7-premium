from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

DEVICE_STATUS_RE = re.compile(r"(?P<setpoint>\d+)(?P<temperature>[+-]?\d+\.\d)(?P<status>.{3})")
DEVICE_LETTERS = ["a", "b", "c", "d"]
TEMP_SENSOR_KEYS = [
    (f"t{block}{letter}", f"T{block} {letter.upper()}")
    for block in range(1, 6)
    for letter in DEVICE_LETTERS
]


def coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_timestamp(value: str | None) -> datetime | None:
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


def parse_spd(value: str | None) -> dict[str, Any]:
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


def parse_spd_modes(value: str | None) -> dict[str, str | None]:
    parsed = parse_spd(value)
    flags = parsed.get("flags") or ""
    mode = None
    vent = None
    if len(flags) >= 1 and flags[0].lower() in {"a", "m"}:
        mode = "auto" if flags[0].lower() == "a" else "manual"
    if len(flags) >= 2 and flags[1].lower() in {"o", "n", "w"}:
        vent_map = {"o": "both", "n": "supply_only", "w": "extract_only"}
        vent = vent_map[flags[1].lower()]
    return {"mode": mode, "vent_mode": vent}


def parse_season(value: str | None) -> dict[str, str | None]:
    season_map = {"z": "winter", "l": "summer"}
    mode_map = {"a": "auto", "z": "forced_winter", "l": "forced_summer"}
    result = {"current": None, "mode": None}
    if not value or len(value) < 2:
        return result
    result["current"] = season_map.get(value[0].lower())
    result["mode"] = mode_map.get(value[1].lower())
    return result


def parse_bypass_or_gwc_mode(value: str | None) -> str | None:
    if not value or len(value) < 2:
        return None
    code = value[1].lower()
    mode_map = {"a": "auto", "z": "forced_on", "w": "forced_off"}
    return mode_map.get(code)


def parse_device_state(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    match = DEVICE_STATUS_RE.match(value)
    if not match:
        return {}
    data = match.groupdict()
    return {
        "setpoint": coerce_float(data["setpoint"]),
        "temperature": coerce_float(data["temperature"]),
        "status": data["status"].strip(),
    }


def parse_temperatures(value: str | None) -> dict[str, float | None]:
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


def parse_hex(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


def parse_anti_smog_available(value: str | None) -> bool:
    return bool(value and len(value) > 9 and value[9] != "-")


def parse_anti_smog_state(value: str | None) -> bool:
    if not value or len(value) <= 9:
        return False
    marker = value[9].lower()
    return marker in {"z", "1"}
