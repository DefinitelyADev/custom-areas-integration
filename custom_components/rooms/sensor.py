"""Sensor platform for Rooms integration."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    STATE_ON,
    STATE_OFF,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_ACTIVE_THRESHOLD,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    DOMAIN,
    ICON_HOME,
    ICON_MOTION,
    ICON_WINDOW_OPEN,
    STATE_ACTIVE,
    STATE_CLASS_MEASUREMENT,
    STATE_IDLE,
    STATE_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [RoomSummarySensor(coordinator, config_entry)]

    async_add_entities(entities)


class RoomSensorCoordinator:
    """Coordinator for room sensors."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.config_entry = config_entry
        self._listeners = []
        self._summary_sensor = None

    async def async_config_entry_first_refresh(self) -> None:
        """Set up state change listeners."""
        entities_to_track = []

        # Add core entities
        for key in [
            CONF_POWER_ENTITY,
            CONF_ENERGY_ENTITY,
            CONF_TEMP_ENTITY,
            CONF_HUMIDITY_ENTITY,
            CONF_MOTION_ENTITY,
            CONF_WINDOW_ENTITY,
            CONF_CLIMATE_ENTITY,
        ]:
            entity_id = self.config_entry.data.get(key)
            if entity_id:
                entities_to_track.append(entity_id)

        if entities_to_track:
            self._listeners.append(
                async_track_state_change_event(
                    self.hass, entities_to_track, self._handle_state_change
                )
            )

    @callback
    def _handle_state_change(self, event):
        """Handle state change events."""
        if self._summary_sensor:
            self._summary_sensor.async_schedule_update_ha_state()

    def register_summary_sensor(self, sensor):
        """Register the summary sensor."""
        self._summary_sensor = sensor

    async def async_shutdown(self):
        """Clean up listeners."""
        for listener in self._listeners:
            listener()


class RoomSummarySensor(SensorEntity):
    """Room summary sensor."""

    def __init__(self, coordinator: RoomSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = config_entry.data[CONF_ROOM_NAME]
        self._attr_unique_id = f"{config_entry.entry_id}_summary"
        self._attr_should_poll = False

        # Register with coordinator
        coordinator.register_summary_sensor(self)

        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Room: {config_entry.data[CONF_ROOM_NAME]}",
            manufacturer="Rooms Integration",
            model="Room Sensor",
        )

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        data = self.config_entry.data

        # Check motion first
        motion_entity = data.get(CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            if motion_state and motion_state.state == STATE_ON:
                return STATE_ACTIVE

        # Check power threshold
        power_entity = data.get(CONF_POWER_ENTITY)
        active_threshold = data.get(CONF_ACTIVE_THRESHOLD, DEFAULT_ACTIVE_THRESHOLD)
        if power_entity:
            power_state = self.hass.states.get(power_entity)
            if power_state:
                try:
                    power_value = float(power_state.state)
                    if power_value > active_threshold:
                        return STATE_ACTIVE
                except (ValueError, TypeError):
                    pass

        # Check if any core entities exist
        core_entities = [
            data.get(CONF_POWER_ENTITY),
            data.get(CONF_TEMP_ENTITY),
            data.get(CONF_HUMIDITY_ENTITY),
            data.get(CONF_MOTION_ENTITY),
            data.get(CONF_WINDOW_ENTITY),
            data.get(CONF_CLIMATE_ENTITY),
        ]

        if any(entity for entity in core_entities if entity):
            return STATE_IDLE

        return STATE_UNKNOWN

    @property
    def icon(self) -> str:
        """Return the icon."""
        data = self.config_entry.data

        # Check window first
        window_entity = data.get(CONF_WINDOW_ENTITY)
        if window_entity:
            window_state = self.hass.states.get(window_entity)
            if window_state and window_state.state == STATE_ON:
                return ICON_WINDOW_OPEN

        # Check motion
        motion_entity = data.get(CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            if motion_state and motion_state.state == STATE_ON:
                return ICON_MOTION

        return ICON_HOME

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        data = self.config_entry.data

        # Core attributes
        power_entity = data.get(CONF_POWER_ENTITY)
        if power_entity:
            power_state = self.hass.states.get(power_entity)
            if power_state:
                try:
                    attrs["power_w"] = float(power_state.state)
                except (ValueError, TypeError):
                    attrs["power_w"] = 0.0
            else:
                attrs["power_w"] = 0.0

        energy_entity = data.get(CONF_ENERGY_ENTITY)
        if energy_entity:
            energy_state = self.hass.states.get(energy_entity)
            if energy_state:
                try:
                    attrs["energy_wh"] = float(energy_state.state)
                except (ValueError, TypeError):
                    attrs["energy_wh"] = 0.0
            else:
                attrs["energy_wh"] = 0.0

        temp_entity = data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            temp_state = self.hass.states.get(temp_entity)
            if temp_state:
                try:
                    attrs["temperature_c"] = float(temp_state.state)
                except (ValueError, TypeError):
                    pass

        humidity_entity = data.get(CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            humidity_state = self.hass.states.get(humidity_entity)
            if humidity_state:
                try:
                    attrs["humidity_pct"] = float(humidity_state.state)
                except (ValueError, TypeError):
                    pass

        motion_entity = data.get(CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            attrs["occupied"] = motion_state.state == STATE_ON if motion_state else False

        window_entity = data.get(CONF_WINDOW_ENTITY)
        if window_entity:
            window_state = self.hass.states.get(window_entity)
            attrs["window_open"] = window_state.state == STATE_ON if window_state else False

        climate_entity = data.get(CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = self.hass.states.get(climate_entity)
            if climate_state:
                attrs["climate_mode"] = climate_state.state
                if climate_state.attributes.get("temperature"):
                    attrs["climate_target_c"] = climate_state.attributes["temperature"]

        return attrs


