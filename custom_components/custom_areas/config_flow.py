"""Config flow for Custom Areas Integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_AREA_NAME,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_ICON,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_ICON,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AreasConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):  # type: ignore[call-arg]  # HA's __init_subclass__ accepts domain parameter
    """Handle a config flow for Areas."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate area name is unique
            await self.async_set_unique_id(user_input[CONF_AREA_NAME])
            self._abort_if_unique_id_configured()

            # Ensure icon has a default value if not provided
            if CONF_ICON not in user_input or user_input[CONF_ICON] is None:
                user_input[CONF_ICON] = DEFAULT_ICON

            return self.async_create_entry(
                title=user_input[CONF_AREA_NAME],
                data=user_input,
            )  # pyright: ignore[reportReturnType]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_NAME): str,
                    vol.Optional(CONF_ICON): selector.IconSelector(
                        selector.IconSelectorConfig(placeholder="mdi:texture-box")
                    ),
                    vol.Optional(CONF_POWER_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_ENERGY_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_TEMP_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_MOTION_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(CONF_WINDOW_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="climate")
                    ),
                    vol.Optional(CONF_ACTIVE_THRESHOLD): vol.All(vol.Coerce(float), vol.Range(min=0)),
                }
            ),
            errors=errors,
        )  # pyright: ignore[reportReturnType]
