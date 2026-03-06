from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature

from .commands import validate_command
from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ProventDataUpdateCoordinator
from .entity import ProventEntity
from .parsing import parse_spd, parse_spd_modes


class ProventFan(ProventEntity, FanEntity):
    _attr_icon = "mdi:fan"
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["auto", "manual"]

    def __init__(self, coordinator: ProventDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "fan_main", "Fan")

    @property
    def percentage_step(self) -> int:
        return 25

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data and self.coordinator.data.get("spd"))

    @property
    def is_on(self) -> bool:
        speed = parse_spd(self.coordinator.data.get("spd")).get("speed") if self.coordinator.data else 0
        return bool(speed and speed > 0)

    @property
    def percentage(self) -> int:
        speed = parse_spd(self.coordinator.data.get("spd")).get("speed") if self.coordinator.data else 0
        if not speed:
            return 0
        return max(0, min(100, int(speed) * 25))

    @property
    def preset_mode(self) -> str | None:
        if not self.coordinator.data:
            return None
        return parse_spd_modes(self.coordinator.data.get("spd")).get("mode")

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        current_speed = parse_spd(self.coordinator.data.get("spd")).get("speed") if self.coordinator.data else 0
        new_speed = current_speed if current_speed and current_speed > 0 else 1
        await self.coordinator.async_send_command(validate_command(f"spd:b{int(new_speed)}"))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send_command(validate_command("spd:b0"))

    async def async_set_percentage(self, percentage: int) -> None:
        speed = round(max(0, min(100, percentage)) / 25)
        await self.coordinator.async_send_command(validate_command(f"spd:b{speed}"))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in self.preset_modes:
            return
        cmd = "spd:ta" if preset_mode == "auto" else "spd:tm"
        await self.coordinator.async_send_command(validate_command(cmd))


async def async_setup_entry(hass, entry, async_add_entities):  # type: ignore[no-untyped-def]
    coordinator: ProventDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([ProventFan(coordinator)])
