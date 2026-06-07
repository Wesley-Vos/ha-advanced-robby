"""The Robby integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant


_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.LAWN_MOWER
]

type AdvancedRobbyConfigEntry = ConfigEntry  # noqa: F821


async def async_setup_entry(hass: HomeAssistant, entry: AdvancedRobbyConfigEntry) -> bool:
    """Set up Robby from a config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AdvancedRobbyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
