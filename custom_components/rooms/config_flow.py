"""Config flow for Rooms integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_CLIMATE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_METRICS,
    CONF_METRIC_CREATE_CHILD,
    CONF_METRIC_DEVICE_CLASS,
    CONF_METRIC_ENTITY_ID,
    CONF_METRIC_LABEL,
    CONF_METRIC_STATE_CLASS,
    CONF_METRIC_UNIT,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_ACTIVE_THRESHOLD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class RoomsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rooms."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate room name is unique
            await self.async_set_unique_id(user_input[CONF_ROOM_NAME])
            self._abort_if_unique_id_configured()

            self._data.update(user_input)
            return await self.async_step_metrics()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ROOM_NAME): str,
                vol.Optional(CONF_POWER_ENTITY): selector.EntitySelector(
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
                vol.Optional(CONF_ACTIVE_THRESHOLD, default=DEFAULT_ACTIVE_THRESHOLD): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
            }),
            errors=errors,
        )

    async def async_step_metrics(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the metrics step."""
        if user_input is not None:
            if user_input.get("add_metric"):
                return await self.async_step_add_metric()

            self._data[CONF_METRICS] = []
            return self.async_create_entry(
                title=self._data[CONF_ROOM_NAME],
                data=self._data,
            )

        return self.async_show_form(
            step_id="metrics",
            data_schema=vol.Schema({
                vol.Optional("add_metric", default=False): bool,
            }),
        )

    async def async_step_add_metric(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle adding a metric."""
        errors = {}

        if user_input is not None:
            # Validate entity exists
            entity_id = user_input[CONF_METRIC_ENTITY_ID]
            if not self.hass.states.get(entity_id):
                errors[CONF_METRIC_ENTITY_ID] = "entity_not_found"

            if not errors:
                if CONF_METRICS not in self._data:
                    self._data[CONF_METRICS] = []
                self._data[CONF_METRICS].append({
                    CONF_METRIC_LABEL: user_input[CONF_METRIC_LABEL],
                    CONF_METRIC_ENTITY_ID: user_input[CONF_METRIC_ENTITY_ID],
                    CONF_METRIC_UNIT: user_input.get(CONF_METRIC_UNIT, ""),
                    CONF_METRIC_DEVICE_CLASS: user_input.get(CONF_METRIC_DEVICE_CLASS, ""),
                    CONF_METRIC_STATE_CLASS: user_input.get(CONF_METRIC_STATE_CLASS, ""),
                    CONF_METRIC_CREATE_CHILD: user_input[CONF_METRIC_CREATE_CHILD],
                })
                return await self.async_step_metrics()

        device_class_options = [
            "",
            "battery",
            "current",
            "energy",
            "humidity",
            "illuminance",
            "power",
            "power_factor",
            "pressure",
            "signal_strength",
            "temperature",
            "voltage",
        ]

        state_class_options = [
            "",
            "measurement",
            "total",
            "total_increasing",
        ]

        return self.async_show_form(
            step_id="add_metric",
            data_schema=vol.Schema({
                vol.Required(CONF_METRIC_LABEL): str,
                vol.Required(CONF_METRIC_ENTITY_ID): selector.EntitySelector(),
                vol.Optional(CONF_METRIC_UNIT): str,
                vol.Optional(CONF_METRIC_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=device_class_options)
                ),
                vol.Optional(CONF_METRIC_STATE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=state_class_options)
                ),
                vol.Required(CONF_METRIC_CREATE_CHILD, default=False): bool,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RoomsOptionsFlowHandler(config_entry)


class RoomsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Rooms."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self._data = dict(config_entry.data)
        self._metrics = list(self._data.get(CONF_METRICS, []))

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_metrics()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_ROOM_NAME, default=self._data.get(CONF_ROOM_NAME)): str,
                vol.Optional(CONF_POWER_ENTITY, default=self._data.get(CONF_POWER_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_TEMP_ENTITY, default=self._data.get(CONF_TEMP_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HUMIDITY_ENTITY, default=self._data.get(CONF_HUMIDITY_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_MOTION_ENTITY, default=self._data.get(CONF_MOTION_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(CONF_WINDOW_ENTITY, default=self._data.get(CONF_WINDOW_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(CONF_CLIMATE_ENTITY, default=self._data.get(CONF_CLIMATE_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Optional(CONF_ACTIVE_THRESHOLD, default=self._data.get(CONF_ACTIVE_THRESHOLD, DEFAULT_ACTIVE_THRESHOLD)): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
            }),
            errors=errors,
        )

    async def async_step_metrics(self, user_input=None):
        """Manage metrics."""
        if user_input is not None:
            if user_input.get("add_metric"):
                return await self.async_step_add_metric()
            elif user_input.get("edit_metric") is not None:
                self._edit_index = user_input["edit_metric"]
                return await self.async_step_edit_metric()
            elif user_input.get("delete_metric") is not None:
                del self._metrics[user_input["delete_metric"]]
                return await self.async_step_metrics()

            self._data[CONF_METRICS] = self._metrics
            return self.async_create_entry(title="", data=self._data)

        # Build options for existing metrics
        options = []
        for i, metric in enumerate(self._metrics):
            options.append(f"{i}: {metric[CONF_METRIC_LABEL]}")

        return self.async_show_form(
            step_id="metrics",
            data_schema=vol.Schema({
                vol.Optional("add_metric", default=False): bool,
                vol.Optional("edit_metric"): vol.In(options) if options else str,
                vol.Optional("delete_metric"): vol.In(options) if options else str,
            }),
        )

    async def async_step_add_metric(self, user_input=None):
        """Add a new metric."""
        return await self._handle_metric_step(user_input, "add_metric")

    async def async_step_edit_metric(self, user_input=None):
        """Edit an existing metric."""
        return await self._handle_metric_step(user_input, "edit_metric", self._edit_index)

    async def _handle_metric_step(self, user_input, step_id, edit_index=None):
        """Handle metric add/edit step."""
        errors = {}

        if user_input is not None:
            # Validate entity exists
            entity_id = user_input[CONF_METRIC_ENTITY_ID]
            if not self.hass.states.get(entity_id):
                errors[CONF_METRIC_ENTITY_ID] = "entity_not_found"

            if not errors:
                metric_data = {
                    CONF_METRIC_LABEL: user_input[CONF_METRIC_LABEL],
                    CONF_METRIC_ENTITY_ID: user_input[CONF_METRIC_ENTITY_ID],
                    CONF_METRIC_UNIT: user_input.get(CONF_METRIC_UNIT, ""),
                    CONF_METRIC_DEVICE_CLASS: user_input.get(CONF_METRIC_DEVICE_CLASS, ""),
                    CONF_METRIC_STATE_CLASS: user_input.get(CONF_METRIC_STATE_CLASS, ""),
                    CONF_METRIC_CREATE_CHILD: user_input[CONF_METRIC_CREATE_CHILD],
                }

                if edit_index is not None:
                    self._metrics[edit_index] = metric_data
                else:
                    self._metrics.append(metric_data)

                return await self.async_step_metrics()

        # Get default values for editing
        defaults = {}
        if edit_index is not None:
            metric = self._metrics[edit_index]
            defaults = {
                CONF_METRIC_LABEL: metric[CONF_METRIC_LABEL],
                CONF_METRIC_ENTITY_ID: metric[CONF_METRIC_ENTITY_ID],
                CONF_METRIC_UNIT: metric.get(CONF_METRIC_UNIT, ""),
                CONF_METRIC_DEVICE_CLASS: metric.get(CONF_METRIC_DEVICE_CLASS, ""),
                CONF_METRIC_STATE_CLASS: metric.get(CONF_METRIC_STATE_CLASS, ""),
                CONF_METRIC_CREATE_CHILD: metric.get(CONF_METRIC_CREATE_CHILD, False),
            }

        device_class_options = [
            "",
            "battery",
            "current",
            "energy",
            "humidity",
            "illuminance",
            "power",
            "power_factor",
            "pressure",
            "signal_strength",
            "temperature",
            "voltage",
        ]

        state_class_options = [
            "",
            "measurement",
            "total",
            "total_increasing",
        ]

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema({
                vol.Required(CONF_METRIC_LABEL, default=defaults.get(CONF_METRIC_LABEL)): str,
                vol.Required(CONF_METRIC_ENTITY_ID, default=defaults.get(CONF_METRIC_ENTITY_ID)): selector.EntitySelector(),
                vol.Optional(CONF_METRIC_UNIT, default=defaults.get(CONF_METRIC_UNIT, "")): str,
                vol.Optional(CONF_METRIC_DEVICE_CLASS, default=defaults.get(CONF_METRIC_DEVICE_CLASS, "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=device_class_options)
                ),
                vol.Optional(CONF_METRIC_STATE_CLASS, default=defaults.get(CONF_METRIC_STATE_CLASS, "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=state_class_options)
                ),
                vol.Required(CONF_METRIC_CREATE_CHILD, default=defaults.get(CONF_METRIC_CREATE_CHILD, False)): bool,
            }),
            errors=errors,
        )
