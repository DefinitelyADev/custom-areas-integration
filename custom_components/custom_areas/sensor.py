"""Sensor platform for Custom Areas Integration."""

import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, STATE_IDLE, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
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
        from homeassistant.const import ENERGY_WATT_HOUR  # pyright: ignore[reportAttributeAccessIssue]
        from homeassistant.const import POWER_WATT  # pyright: ignore[reportAttributeAccessIssue]
        from homeassistant.const import TEMP_CELSIUS  # pyright: ignore[reportAttributeAccessIssue]

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
    CONF_AREA_NAME,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_ICON,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_ACTIVE_THRESHOLD,
    DEFAULT_ICON,
    DOMAIN,
    ICON_MOTION,
    ICON_WINDOW_OPEN,
    STATE_ACTIVE,
)

_LOGGER = logging.getLogger(__name__)


def get_numeric_state(hass: HomeAssistant, entity_id: str) -> Optional[float]:
    """Get numeric state from entity.

    Returns the parsed float value, or None if the entity doesn't exist
    or the state cannot be converted to a float.
    """
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state:
        try:
            return float(state.state)
        except (ValueError, TypeError) as err:
            _LOGGER.debug(
                "Failed to convert state %s for entity %s: %s",
                state.state,
                entity_id,
                err,
            )
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = [AreaSummarySensor(coordinator, config_entry)]

    # Add individual measurement sensors if corresponding entities are configured
    data = config_entry.data

    if data.get(CONF_POWER_ENTITY):
        entities.append(AreaPowerSensor(coordinator, config_entry))

    if data.get(CONF_ENERGY_ENTITY):
        entities.append(AreaEnergySensor(coordinator, config_entry))

    if data.get(CONF_TEMP_ENTITY):
        entities.append(AreaTemperatureSensor(coordinator, config_entry))

    if data.get(CONF_HUMIDITY_ENTITY):
        entities.append(AreaHumiditySensor(coordinator, config_entry))

    if data.get(CONF_CLIMATE_ENTITY):
        entities.append(AreaClimateTargetSensor(coordinator, config_entry))

    async_add_entities(entities)


class AreaSensorCoordinator:
    """Coordinator for area sensors."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.config_entry = config_entry
        self._listeners: list[Callable[..., Any]] = []
        self._summary_sensor: Optional["AreaSummarySensor"] = None
        self._measurement_sensors: list["AreaMeasurementSensor"] = []

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
        # Extract data from event
        event_data = event.data
        entity_id = event_data.get("entity_id")

        # Update summary sensor
        if self._summary_sensor:
            old_state = event_data.get("old_state")
            new_state = event_data.get("new_state")

            _LOGGER.debug("State change for %s: %s -> %s", entity_id, old_state, new_state)

            self._summary_sensor.async_schedule_update_ha_state()  # pyright: ignore[reportUnusedCoroutine]

        # Update relevant measurement sensors (only those affected by the changed entity)
        if entity_id:
            for sensor in self._measurement_sensors:
                sensor_entity_id = sensor.config_entry.data.get(sensor.entity_config_key)
                if sensor_entity_id == entity_id:
                    sensor.async_schedule_update_ha_state()  # pyright: ignore[reportUnusedCoroutine]
        return

    def register_summary_sensor(self, sensor: "AreaSummarySensor") -> None:
        """Register the summary sensor."""
        self._summary_sensor = sensor

    def register_measurement_sensor(self, sensor: "AreaMeasurementSensor") -> None:
        """Register a measurement sensor."""
        self._measurement_sensors.append(sensor)

    def async_shutdown(self):
        """Clean up listeners."""
        for listener in self._listeners:
            listener()


class AreaSummarySensor(SensorEntity):
    """Area summary sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        # Display name (friendly): just the area name
        self._attr_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_summary"
        self._attr_should_poll = False

        # Register with coordinator
        coordinator.register_summary_sensor(self)

        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor (display name without area_ prefix)."""
        area_name = self.config_entry.data.get(CONF_AREA_NAME, "")
        return str(area_name) if area_name else ""

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id so entity_id gets a area_ prefix.

        Home Assistant will slugify this into the final object_id.
        """
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}" if area_name else None

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
            return str(STATE_IDLE)

        return str(STATE_UNKNOWN)

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
        icon_value = data.get(CONF_ICON, DEFAULT_ICON)
        return str(icon_value) if icon_value is not None else DEFAULT_ICON

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

        # Binary sensor attributes (motion, window, climate mode)
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

        return attrs


class AreaMeasurementSensor(SensorEntity):
    """Base class for area measurement sensors."""

    def __init__(
        self,
        coordinator: AreaSensorCoordinator,
        config_entry: ConfigEntry,
        measurement_type: str,
        entity_config_key: str,
        unit: str,
    ) -> None:
        """Initialize a measurement sensor for a specific area and measurement type."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.measurement_type = measurement_type
        self.entity_config_key = entity_config_key

        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} {measurement_type}"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_{measurement_type.lower().replace(' ', '_')}"
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit

        # Register with coordinator
        coordinator.register_measurement_sensor(self)

        # Set up device info (same device as summary sensor)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id with area prefix."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        measurement_type = self.measurement_type.lower().replace(" ", "_")
        return f"custom_area_{area_name}_{measurement_type}" if area_name else None

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        entity_id = self.config_entry.data.get(self.entity_config_key)
        if not entity_id:
            return None
        return get_numeric_state(self.hass, entity_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        entity_id = self.config_entry.data.get(self.entity_config_key)
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        return state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)


class AreaPowerSensor(AreaMeasurementSensor):
    """Area power sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator, config_entry, "Power", CONF_POWER_ENTITY, UNIT_WATT)
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT


class AreaEnergySensor(AreaMeasurementSensor):
    """Area energy sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, config_entry, "Energy", CONF_ENERGY_ENTITY, UNIT_WATT_HOUR)
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING


class AreaTemperatureSensor(AreaMeasurementSensor):
    """Area temperature sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, config_entry, "Temperature", CONF_TEMP_ENTITY, UNIT_CELSIUS)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT


class AreaHumiditySensor(AreaMeasurementSensor):
    """Area humidity sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, config_entry, "Humidity", CONF_HUMIDITY_ENTITY, PERCENTAGE)
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT


class AreaClimateTargetSensor(AreaMeasurementSensor):
    """Area climate target temperature sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the climate target temperature sensor."""
        super().__init__(coordinator, config_entry, "Climate Target", CONF_CLIMATE_ENTITY, UNIT_CELSIUS)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the climate target temperature."""
        entity_id = self.config_entry.data.get(self.entity_config_key)
        if not entity_id:
            return None

        climate_state = self.hass.states.get(entity_id)
        if climate_state and climate_state.attributes.get("temperature"):
            try:
                return float(climate_state.attributes["temperature"])
            except (ValueError, TypeError):
                pass
        return None
