"""Config flow for the Robby integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.lawn_mower import DOMAIN as LAWN_MOWER_DOMAIN
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import CONF_MOWER_ENTITY, CONF_QUERY_SCHEDULES_BUTTON_ENTITY, DOMAIN


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MOWER_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[LAWN_MOWER_DOMAIN]),
        ),
        vol.Required(CONF_QUERY_SCHEDULES_BUTTON_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=[BUTTON_DOMAIN]
                )
            ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    return {
        "title": "Advanced Robby",
        "mower_entity": data[CONF_MOWER_ENTITY],
        "query_schedules_button_entity": data[CONF_QUERY_SCHEDULES_BUTTON_ENTITY]
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Robby."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            info = await validate_input(self.hass, user_input)
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
