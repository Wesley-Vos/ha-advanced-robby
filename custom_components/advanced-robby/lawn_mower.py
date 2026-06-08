"""Robby Lawn Mower Entity for Home Assistant."""

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import AdvancedRobbyConfigEntry
from .const import ATTR_CHARGING, CONF_CANCEL_BUTTON_ENTITY, CONF_CONTINUE_BUTTON_ENTITY, CONF_MOWER_ENTITY, STATE_STANDBY
from .device_binding import attach_entities_to_source_device

import asyncio


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdvancedRobbyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lawn mower entity."""
    entities = [RobbyLawnMowerEntity(hass, entry)]

    await attach_entities_to_source_device(entry, entities, hass, entry.data[CONF_MOWER_ENTITY])

    async_add_entities(entities)

class RobbyLawnMowerEntity(LawnMowerEntity):
    """Representation of a Robby lawn mower."""

    def __init__(self, hass: HomeAssistant, entry: AdvancedRobbyConfigEntry) -> None:
        """Initialize the lawn mower entity."""
        self.hass = hass
        self._attr_name = "Robby"
        self._mower_entity = entry.data[CONF_MOWER_ENTITY]
        self._cancel_button_entity = entry.data[CONF_CANCEL_BUTTON_ENTITY]
        self._continue_button_entity = entry.data[CONF_CONTINUE_BUTTON_ENTITY]
        self._attr_unique_id = (
            f"advanced_robby_lawn_mower_{self._mower_entity}"
        )
        self._attr_supported_features = LawnMowerEntityFeature.PAUSE | LawnMowerEntityFeature.DOCK | LawnMowerEntityFeature.START_MOWING
        self._attr_translation_key = "activity"
        self._state = None
        self._attr_available = False
        self._docked = True

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        async def async_state_changed_listener(
            event: Event[EventStateChangedData] | None = None,
        ) -> None:
            """Triggered whenever mower entity updates."""

            if (
                new_state := self.hass.states.get(self._mower_entity)
            ) is None or new_state.state == STATE_UNAVAILABLE:
                self._attr_available = False
                return

            self._state = new_state.attributes.get("raw_activity")

            if event is not None: 
                old_raw_activity = event.data["old_state"].attributes.get("raw_activity")
                if old_raw_activity == "CHARGING" and self._state == "STANDBY":
                    self._docked = True # ready charging TODO: check what if not fully charged, then maybe standby
                elif old_raw_activity == "PARK" and self._state == "STANDBY":
                    self._docked = True # done parking
                else:
                    self._docked = False
            else:
                self._docked = self._state == "STANDBY"

            self._attr_available = True
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._mower_entity], async_state_changed_listener
            )
        )

        await async_state_changed_listener()

    @property
    def activity(self) -> LawnMowerActivity:
        """Return the current activity of the lawn mower."""
        if self._state is None:
            return None
        if self._state in ("CHARGING", "CHARGING_WITH_TASK_SUSPEND"):
            return LawnMowerActivity.DOCKED
        if self._state == "STANDBY":
            return LawnMowerActivity.DOCKED if self._docked else STATE_STANDBY
        if self._state in ("MOWING", "FIXED_MOWING"):
            return LawnMowerActivity.MOWING
        if self._state in ("EMERGENCY", "ERROR"):
            return LawnMowerActivity.ERROR
        if self._state == "PAUSED": 
            return LawnMowerActivity.PAUSED
        if self._state in ("PARK"):
            return LawnMowerActivity.RETURNING
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the lawn mower."""
        return {
            "raw_activity": self._state,
            "docked": self._docked,
            "charging": self._state in ("CHARGING", "CHARGING_WITH_TASK_SUSPEND"),
            "locked": self._state == "LOCKED"
        }

    async def async_start_mowing(self) -> None:

        if self._state == "PAUSED":
            await self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": self._continue_button_entity}
            )
            return
        
        if self._state == "PARK":
            await self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": self._cancel_button_entity}
            )
            
            await asyncio.sleep(2)
            
        """Start mowing"""
        await self.hass.services.async_call(
            "lawn_mower",
            "start_mowing",
            {"entity_id": self._mower_entity}
        )

    async def async_dock(self) -> None:
        
        if self._state == "MOWING":
            await self.hass.services.async_call(
                "lawn_mower",
                "pause",
                {"entity_id": self._mower_entity}
            )

            await asyncio.sleep(2)
            
        if self._state in ("MOWING", "PAUSED"):

            await self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": self._cancel_button_entity}
            )

            await asyncio.sleep(2)

        await self.hass.services.async_call(
            "lawn_mower",
            "dock",
            {"entity_id": self._mower_entity}
        )

    async def async_pause(self) -> None:

        """Pause the lawn mower."""
        await self.hass.services.async_call(
            "lawn_mower",
            "pause",
            {"entity_id": self._mower_entity},
        )
