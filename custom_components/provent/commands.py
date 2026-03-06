from __future__ import annotations

import re

from .api import ProventApiError

_SIMPLE_PATTERNS: dict[str, str] = {
    "spd": r"^(?:b[0-4]|t[am]|p[onw]|w[01]|h[01]|c[01])$",
    "bps": r"^t[azw]$",
    "sez": r"^s[azl]$",
    "gwc": r"^t[azw]$",
    "dat": r"^(?:d[0-6]|g(?:[0-9]|1[0-9]|2[0-3])|m(?:[0-9]|[1-5][0-9])|D(?:[1-9]|[12][0-9]|3[01])|M(?:[1-9]|1[0-2])|R[0-9]{1,2})$",
    "asc": r"^r$",
    "str": r"^[1-4](?:s[01]|t[ar])$",
    "elf": r"^(?:f[0-3]|[Jj][0-3]|n(?:[6-9]|[1-5][0-9]|60)|s[2-5]|[Pp]|t[01])$",
}

_HTCL_RE = re.compile(r"^(?:(?:[12])?(?:t[amw]|T(?:[4-9]|[12][0-9]|3[0-5])))$")


def split_commands(raw: str) -> list[str]:
    commands = [command.strip() for command in raw.split(",") if command.strip()]
    if not commands:
        raise ProventApiError("Empty command")
    return commands


def validate_command(command: str) -> str:
    if ":" not in command:
        return command

    group, payload = command.split(":", 1)
    group = group.strip().lower()
    payload = payload.strip()
    if not payload:
        raise ProventApiError(f"Invalid command payload for {group}")

    if group in {"nag", "chl"}:
        if not _HTCL_RE.fullmatch(payload):
            raise ProventApiError(
                f"Unsupported {group} payload '{payload}'. Expected t[a|m|w] or T4..35 (optional channel prefix)."
            )
        return f"{group}:{payload}"

    pattern = _SIMPLE_PATTERNS.get(group)
    if pattern and re.fullmatch(pattern, payload) is None:
        raise ProventApiError(f"Unsupported {group} payload '{payload}'")

    return f"{group}:{payload}"


def validate_commands(raw: str) -> str:
    commands = split_commands(raw)
    return ",".join(validate_command(command) for command in commands)
