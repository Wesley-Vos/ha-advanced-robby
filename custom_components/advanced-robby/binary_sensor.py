"""Robby Lawn Mower Entity for Home Assistant."""

from dataclasses import dataclass, field

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription
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
    entities = [RobbyBinarySensorEntity(hass, entry, description) for description in ROBBY_BINARY_SENSOR_ENTITIES]
    
    await attach_entities_to_source_device(entry, entities, hass, entry.data[CONF_MOWER_ENTITY])

    async_add_entities(entities)

class RobbyBinarySensorEntity(BinarySensorEntity):
    """Representation of a Robby charging binary sensor."""

    def __init__(self, hass: HomeAssistant, entry: AdvancedRobbyConfigEntry, description: RobbyBinarySensorEntityDescription):
        """Initialize the charging binary sensor entity."""
        self.hass = hass
        self._mower_entity = entry.data[CONF_MOWER_ENTITY]
        self._attr_has_entity_name = True
        self._attr_unique_id = f"robby_{description.key}_binary_sensor_{self._mower_entity}"
        self.entity_description = description
        self._state = False
        self._attr_available = False

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
            
            new_state = new_state.attributes.get("raw_activity") in self.entity_description.state_vals
            self._state = new_state if not self.entity_description.invert else not new_state

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
        return self._state

@dataclass
class RobbyBinarySensorEntityDescription(
    BinarySensorEntityDescription
):
    """Describes Robby binary sensor entity."""

    state_vals: list[str] = field(default_factory=list)
    invert: bool = False


ROBBY_BINARY_SENSOR_ENTITIES = (
    RobbyBinarySensorEntityDescription(
        key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        state_vals=["CHARGING", "CHARGING_WITH_TASK_SUSPEND"]
    ),
    RobbyBinarySensorEntityDescription(
        key="locked",
        name="Locked",
        device_class=BinarySensorDeviceClass.LOCK,
        state_vals=["LOCKED"],
        invert=True
    )
)