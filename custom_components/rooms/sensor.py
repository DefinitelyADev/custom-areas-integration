"""Sensor platform for Rooms integration."""

import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

# Try to import unit constants, fall back to local definitions if not available
try:
    from homeassistant.util.unit_conversion import UnitOfEnergy, UnitOfPower
    from homeassistant.util.unit_system import UnitOfTemperature

    UNIT_CELSIUS = UnitOfTemperature.CELSIUS
    UNIT_WATT = UnitOfPower.WATT
    UNIT_WATT_HOUR = UnitOfEnergy.WATT_HOUR
except ImportError:
    # Fallback for older versions or if unit system constants don't exist
    try:
        from homeassistant.const import ENERGY_WATT_HOUR, POWER_WATT, TEMP_CELSIUS

        UNIT_CELSIUS = TEMP_CELSIUS
        UNIT_WATT = POWER_WATT
        UNIT_WATT_HOUR = ENERGY_WATT_HOUR
    except ImportError:
        # Final fallback for versions where these constants don't exist
        UNIT_CELSIUS = "°C"
        UNIT_WATT = "W"
        UNIT_WATT_HOUR = "Wh"

from .const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_ICON,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_ACTIVE_THRESHOLD,
    DEFAULT_ICON,
    DOMAIN,
    ICON_MOTION,
    ICON_WINDOW_OPEN,
    STATE_ACTIVE,
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
        self._listeners: list[Callable[..., Any]] = []
        self._summary_sensor: Optional["RoomSummarySensor"] = None

    async def async_config_entry_first_refresh(self) -> None:
        """Set up state change listeners."""
        _LOGGER.debug("Setting up state change listeners for entities")
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
                _LOGGER.debug("Will track entity: %s", entity_id)

        _LOGGER.debug("Total entities to track: %d", len(entities_to_track))

        if entities_to_track:
            _LOGGER.debug(
                "Calling async_track_state_change_event with entities: %s",
                entities_to_track,
            )
            listener = async_track_state_change_event(self.hass, entities_to_track, self._handle_state_change)
            self._listeners.append(listener)  # pyright: ignore[reportArgumentType]
            _LOGGER.debug("Successfully registered state change listener")

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state change events."""
        if self._summary_sensor:
            # Extract data from event
            event_data = event.data
            entity_id = event_data.get("entity_id")
            old_state = event_data.get("old_state")
            new_state = event_data.get("new_state")

            _LOGGER.debug("State change for %s: %s -> %s", entity_id, old_state, new_state)

            self._summary_sensor.async_schedule_update_ha_state()  # pyright: ignore[reportUnusedCoroutine]
        return

    def register_summary_sensor(self, sensor: "RoomSummarySensor") -> None:
        """Register the summary sensor."""
        self._summary_sensor = sensor

    def async_shutdown(self):
        """Clean up listeners."""
        for listener in self._listeners:
            listener()


class RoomSummarySensor(SensorEntity):
    """Room summary sensor."""

    def __init__(self, coordinator: RoomSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        # Display name (friendly): just the room name
        self._attr_name = str(config_entry.data.get(CONF_ROOM_NAME, ""))
        self._attr_unique_id = f"room_{config_entry.entry_id}_summary"
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
    def name(self) -> str:
        """Return the name of the sensor (display name without room_ prefix)."""
        room_name = self.config_entry.data.get(CONF_ROOM_NAME, "")
        return str(room_name) if room_name else ""

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id so entity_id gets a room_ prefix.

        Home Assistant will slugify this into the final object_id.
        """
        room_name = str(self.config_entry.data.get(CONF_ROOM_NAME, "")).strip()
        return f"room_{room_name}" if room_name else None

    def _get_numeric_state(self, entity_id: str, default_value: float = 0.0) -> Optional[float]:
        """Get numeric state from entity, with fallback to default."""
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state:
            try:
                value = float(state.state)
                return value if value != 0.0 else default_value
            except (ValueError, TypeError) as err:
                _LOGGER.debug(
                    "Failed to convert state %s for entity %s: %s",
                    state.state,
                    entity_id,
                    err,
                )
                pass
        return None

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
            data.get(CONF_ENERGY_ENTITY),
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

        # Return configured icon or default
        return str(data.get(CONF_ICON, DEFAULT_ICON))

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attrs: Dict[str, Any] = {}
        data = self.config_entry.data

        # Cache state lookups for performance
        cached_states = {}

        def get_cached_state(entity_id: str):
            """Get state with caching to avoid multiple lookups."""
            if entity_id not in cached_states:
                cached_states[entity_id] = self.hass.states.get(entity_id)
            return cached_states[entity_id]

        def fmt(value: Optional[float], unit: str) -> Optional[str]:
            """Format a numeric value with its unit for nice display.

            Keep numbers compact: no trailing zeros, max 1 decimal place by default.
            Returns None if value is None.
            """
            if value is None:
                return None
            try:
                # Show up to 1 decimal place; strip trailing zeros/period
                text = f"{float(value):.1f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                return None
            return f"{text} {unit}"

        # Core attributes with consistent error handling
        power_entity = data.get(CONF_POWER_ENTITY)
        if power_entity:
            power_val = self._get_numeric_state(power_entity, 0.0) or 0.0
            # Numeric attribute for automations
            attrs["power_w"] = power_val
            # Display-friendly attribute (value with unit)
            power_disp = fmt(power_val, UNIT_WATT)
            if power_disp is not None:
                attrs["power"] = power_disp

        energy_entity = data.get(CONF_ENERGY_ENTITY)
        if energy_entity:
            energy_val = self._get_numeric_state(energy_entity, 0.0) or 0.0
            # Numeric attribute for automations
            attrs["energy_wh"] = energy_val
            # Display-friendly attribute
            energy_disp = fmt(energy_val, UNIT_WATT_HOUR)
            if energy_disp is not None:
                attrs["energy"] = energy_disp

        temp_entity = data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            temp_value = self._get_numeric_state(temp_entity)
            if temp_value is not None:  # Only add if we got a valid value
                # Numeric attribute for automations
                attrs["temperature_c"] = temp_value
                # Display-friendly attribute
                temp_disp = fmt(temp_value, UNIT_CELSIUS)
                if temp_disp is not None:
                    attrs["temperature"] = temp_disp

        humidity_entity = data.get(CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            humidity_value = self._get_numeric_state(humidity_entity)
            if humidity_value is not None:  # Only add if we got a valid value
                # Numeric attribute for automations
                attrs["humidity_pct"] = humidity_value
                # Display-friendly attribute
                humidity_disp = fmt(humidity_value, PERCENTAGE)
                if humidity_disp is not None:
                    attrs["humidity"] = humidity_disp

        motion_entity = data.get(CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = get_cached_state(motion_entity)
            attrs["occupied"] = motion_state.state == STATE_ON if motion_state else False

        window_entity = data.get(CONF_WINDOW_ENTITY)
        if window_entity:
            window_state = get_cached_state(window_entity)
            attrs["window_open"] = window_state.state == STATE_ON if window_state else False

        climate_entity = data.get(CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = get_cached_state(climate_entity)
            if climate_state:
                attrs["climate_mode"] = climate_state.state
                if climate_state.attributes.get("temperature"):
                    t = climate_state.attributes["temperature"]
                    attrs["climate_target_c"] = t
                    t_disp = fmt(t, UNIT_CELSIUS)
                    if t_disp is not None:
                        attrs["climate_target"] = t_disp

        return attrs
