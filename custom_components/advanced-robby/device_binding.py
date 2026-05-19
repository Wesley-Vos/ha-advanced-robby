import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry, DeviceInfo
from homeassistant.helpers.entity import Entity


_LOGGER = logging.getLogger(__name__)


async def attach_entities_to_source_device(
    config_entry: ConfigEntry | None,
    entities_to_add: list[Entity],
    hass: HomeAssistant,
    parent_entity_id: str,
) -> None:
    
    entity_registry = er.async_get(hass)    
    parent_entity_entry = entity_registry.async_get(parent_entity_id)

    device_registry = dr.async_get(hass)
    parent_device_entry = (
        device_registry.async_get(parent_entity_entry.device_id) if parent_entity_entry and parent_entity_entry.device_id else None
    )

    if config_entry:
        bind_config_entry_to_device(hass, config_entry, parent_device_entry)

    for entity in (entity for entity in entities_to_add if isinstance(entity, Entity)):
        try:
            entity.device_entry = parent_device_entry
        except AttributeError:  # pragma: no cover
            _LOGGER.error("%s: Cannot set device id on entity", entity.entity_id)


def bind_config_entry_to_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> None:
    
    if config_entry.entry_id not in device_entry.config_entries:
        device_registry = dr.async_get(hass)
        device_registry.async_update_device(
            device_entry.id,
            add_config_entry_id=config_entry.entry_id,
        )
