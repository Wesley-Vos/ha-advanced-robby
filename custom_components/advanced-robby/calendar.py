import logging
from typing import Optional

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
        STATE_UNAVAILABLE,
)
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import AdvancedRobbyConfigEntry
from .const import (
    CONF_MOWER_ENTITY,
    CONF_QUERY_SCHEDULES_BUTTON_ENTITY,
)
from .device_binding import attach_entities_to_source_device
from .helper import build_week, decode_schedule

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdvancedRobbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    
    entities = [
        RobbyScheduleCalendar(
            hass,
            entry.data[CONF_MOWER_ENTITY],
            entry.data[CONF_QUERY_SCHEDULES_BUTTON_ENTITY],
        )
    ]

    await attach_entities_to_source_device(entry, entities, hass, entry.data[CONF_MOWER_ENTITY])

    async_add_entities(entities)


class RobbyScheduleCalendar(CalendarEntity):

    def __init__(self, hass, mower_entity, button_entity):
        self.hass = hass
        self._attr_unique_id = (
            f"robby_schedule_{mower_entity}"
        )
        self._attr_name = "Robby tijdschema"

        self._mower_entity = mower_entity
        self._button_entity = button_entity
        self._button_available = False
        self._events_cache = []
        self._ha_has_started = False

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        async def async_state_changed_listener(
            event: Event[EventStateChangedData] | None = None,
        ) -> None:
            """Triggered whenever mower entity updates."""
            if not self._ha_has_started:
                _LOGGER.debug("Home Assistant hasn't started yet, waiting initialization")
                return
            
            if event:
                _LOGGER.debug(f"Receiving state change event for {event.data.get('entity_id')}, changing from {event.data.get("old_state")} to {event.data.get("new_state")}")

            if self._button_available and event and event.data.get("entity_id") == self._button_entity:
                return
            
            if (
                button_state := self.hass.states.get(self._button_entity)
            ) is None or button_state.state == STATE_UNAVAILABLE:
                _LOGGER.debug("Button entity is unavailable or not yet created")
                self._attr_available = False
                self._button_available = False
                return
            else:
                self._button_available = True

            if (
                new_state := self.hass.states.get(self._mower_entity)
            ) is None or new_state.state == STATE_UNAVAILABLE:
                _LOGGER.debug("Mower entity is unavailable or not yet created")
                self._attr_available = False
                return

            payload = new_state.attributes.get("schedule")
            
            if not payload:
                _LOGGER.debug("Schedule attribute is not (yet) present in mower entity attributes")
                try:
                    _LOGGER.debug("Pressing query schedule button")
                    await self.hass.services.async_call(
                        "button",
                        "press",
                        {"entity_id": self._button_entity},
                        blocking=True,
                    )
                except Exception as e:
                    _LOGGER.error("Button press failed: %s", e)
                
                return

            decoded = decode_schedule(payload)
            self._events_cache = build_week(decoded)

            _LOGGER.debug("Schedule is decoded, calendar available")
            self._attr_available = True
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._mower_entity, self._button_entity], async_state_changed_listener
            )
        )

        @callback
        async def async_on_ha_started(event):
            self._ha_has_started = True
            await async_state_changed_listener()

        if self.hass.is_running:
            self.hass.async_create_task(async_on_ha_started(None))
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED,
                async_on_ha_started,
            )

    # -----------------------------------------------------
    # Calendar API
    # -----------------------------------------------------
    async def async_get_events(self, hass, start_date, end_date):
        return self._events_cache

    @property
    def event(self) -> Optional[CalendarEvent]:
        if not self._events_cache:
            return None
        return self._events_cache[0]
