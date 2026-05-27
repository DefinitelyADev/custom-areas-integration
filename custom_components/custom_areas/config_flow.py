"""Config flow for Custom Areas Integration."""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import selector
from homeassistant.util import slugify

if TYPE_CHECKING:
    # `ConfigFlowResult` only exists on newer HA versions. The CI matrix
    # spans HA 2024/2025/2026; the locally-installed phacc-pinned HA used
    # for type-checking may not expose it. Pull it in under TYPE_CHECKING
    # only and use the string forward reference in signatures. The suppress
    # below is needed because pyright still evaluates TYPE_CHECKING blocks.
    from homeassistant.config_entries import ConfigFlowResult  # pyright: ignore[reportAttributeAccessIssue]

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


class AreasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Areas."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "AreasOptionsFlowHandler":
        """Return the options flow handler for an existing entry."""
        return AreasOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> "ConfigFlowResult":
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate area name is unique. Slugify first so "Living Room",
            # "living room", and " Living Room " all collide on the same
            # unique_id rather than coexisting as separate entries.
            await self.async_set_unique_id(slugify(user_input[CONF_AREA_NAME]))
            self._abort_if_unique_id_configured()

            # Ensure icon has a default value if not provided
            if CONF_ICON not in user_input or user_input[CONF_ICON] is None:
                user_input[CONF_ICON] = DEFAULT_ICON

            return self.async_create_entry(
                title=user_input[CONF_AREA_NAME],
                data=user_input,
            )

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
        )


class AreasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle reconfiguring an existing area entry.

    Mirrors `AreasConfigFlow.async_step_user`'s schema without the
    unique-id check (the entry already exists). Defaults pull from
    `entry.options` first, falling back to `entry.data`, so a partially-
    edited entry keeps unchanged fields.
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Capture the entry being reconfigured."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> "ConfigFlowResult":
        """Show the options form, then save into `entry.options`."""
        if user_input is not None:
            # Ensure icon has a default value if not provided
            if CONF_ICON not in user_input or user_input[CONF_ICON] is None:
                user_input[CONF_ICON] = DEFAULT_ICON

            return self.async_create_entry(title="", data=user_input)

        def _current(key: str) -> Any:
            """Options take precedence over data for default values."""
            if key in self.config_entry.options:
                return self.config_entry.options[key]
            return self.config_entry.data.get(key)

        schema: dict[Any, Any] = {
            vol.Required(CONF_AREA_NAME, default=_current(CONF_AREA_NAME)): str,
        }

        # Optional fields default to `vol.UNDEFINED` if neither options nor data
        # has them set — voluptuous treats that as "no default" rather than
        # rendering an empty entity selector with None.
        for key, sel in (
            (CONF_ICON, selector.IconSelector(selector.IconSelectorConfig(placeholder="mdi:texture-box"))),
            (CONF_POWER_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))),
            (CONF_ENERGY_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))),
            (CONF_TEMP_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))),
            (CONF_HUMIDITY_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))),
            (CONF_MOTION_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))),
            (CONF_WINDOW_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))),
            (CONF_CLIMATE_ENTITY, selector.EntitySelector(selector.EntitySelectorConfig(domain="climate"))),
        ):
            current = _current(key)
            if current is not None:
                schema[vol.Optional(key, default=current)] = sel
            else:
                schema[vol.Optional(key)] = sel

        threshold_default = _current(CONF_ACTIVE_THRESHOLD)
        if threshold_default is not None:
            schema[vol.Optional(CONF_ACTIVE_THRESHOLD, default=threshold_default)] = vol.All(
                vol.Coerce(float), vol.Range(min=0)
            )
        else:
            schema[vol.Optional(CONF_ACTIVE_THRESHOLD)] = vol.All(vol.Coerce(float), vol.Range(min=0))

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))
