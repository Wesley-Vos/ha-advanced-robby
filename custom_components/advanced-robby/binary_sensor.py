"""Robby Lawn Mower Entity for Home Assistant."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import AdvancedRobbyConfigEntry
from .const import (
    CONF_MOWER_ENTITY,
)
from .device_binding import attach_entities_to_source_device


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdvancedRobbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the binary sensor entity."""
    entities = [RobbyChargingBinarySensorEntity(hass, entry)]
    
    await attach_entities_to_source_device(entry, entities, hass, entry.data[CONF_MOWER_ENTITY])

    async_add_entities(entities)


class RobbyChargingBinarySensorEntity(BinarySensorEntity):
    """Representation of a Robby charging binary sensor."""

    def __init__(self, hass: HomeAssistant, entry: AdvancedRobbyConfigEntry):
        """Initialize the charging binary sensor entity."""
        self.hass = hass
        self._mower_entity = entry.data[CONF_MOWER_ENTITY]
        self._attr_has_entity_name = True
        self._attr_unique_id = f"robby_charging_binary_sensor_{self._mower_entity}"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
        self.is_charging = False

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

            self.is_charging = new_state.attributes.get("raw_activity") in ("CHARGING", "CHARGING_WITH_TASK_SUSPEND")

            self._attr_available = True
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._mower_entity], async_state_changed_listener
            )
        )

        await async_state_changed_listener()

    # -----------------------------------------------------
    # Binary Sensor API
    # -----------------------------------------------------
    @property
    def is_on(self) -> bool | None:
        """Return the current state of the binary sensor."""
        return self.is_charging

