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
    """Decode the packed ``spd`` string emitted by the WebManipulator daemon.

    Grammar (RC7 premium / RC7 home firmware, per the device's ``cm``/``cmgc``
    frame composer)::

        gear(1 digit, 0-4)
          + 'c'                             -> CO-alarm state, nothing follows
          | mode(1: 'a'=auto / 'm'=manual)
            airflow(1: 'o' / 'w')
            humidity(1: '1'/'0', or '-' when no humidity sensor is fitted)
            co2(1: '1'/'0', or '-' when no CO2 sensor is fitted)
            airing_duration(2 digits, always present)
            [airing_remaining(2 digits) only while airing/wietrzenie is active]

    The trailing two digits when airing is *inactive* are the configured airing
    duration, not a live countdown (Modbus register 10 reads 0 when inactive);
    a remaining value is appended only while airing runs. Reading the last two
    digits as the remaining time made the ventilation-boost switch (which is on
    when ``ventilation_remaining > 0``) read permanently on and uncontrollable.
    Humidity/CO2 are single positional flags, not the letters ``h``/``c``.
    """
    if not value:
        return {}

    result: dict[str, Any] = {}
    if value[0].isdigit():
        result["speed"] = int(value[0])

    rest = value[1:]

    # CO-alarm special state: gear followed by a lone 'c', no other fields.
    if rest[:1] == "c":
        result["flags"] = "c"
        result["co_alarm"] = True
        result["humidity"] = None
        result["co2"] = None
        result["ventilation_remaining"] = 0
        return result

    # Fixed-width flag block: mode, airflow, humidity, co2.
    result["flags"] = rest[:4]
    result["co_alarm"] = False

    humidity = rest[2:3]
    result["humidity"] = True if humidity == "1" else False if humidity == "0" else None
    co2 = rest[3:4]
    result["co2"] = True if co2 == "1" else False if co2 == "0" else None

    digits = rest[4:]
    result["ventilation_duration"] = coerce_int(digits[:2]) if len(digits) >= 2 else None
    # A live countdown is present only while airing is active (extra 2 digits).
    result["ventilation_remaining"] = (coerce_int(digits[2:]) or 0) if len(digits) > 2 else 0
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
