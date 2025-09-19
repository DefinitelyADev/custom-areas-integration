"""Sensor platform for Custom Areas Integration."""

import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, STATE_IDLE, STATE_ON, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

# Try to import unit constants, fall back to local definitions if not available
try:
    from homeassistant.util.unit_conversion import UnitOfEnergy, UnitOfPower
    from homeassistant.util.unit_system import UnitOfTemperature

    UNIT_CELSIUS: str = UnitOfTemperature.CELSIUS
    UNIT_HUMIDITY: str = PERCENTAGE
    UNIT_WATT: str = UnitOfPower.WATT
    UNIT_WATT_HOUR: str = UnitOfEnergy.WATT_HOUR
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
        UNIT_CELSIUS = "°C"  # pyright: ignore[reportAssignmentType]
        UNIT_HUMIDITY = "%"  # pyright: ignore[reportAssignmentType]
        UNIT_WATT = "W"  # pyright: ignore[reportAssignmentType]
        UNIT_WATT_HOUR = "Wh"  # pyright: ignore[reportAssignmentType]

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

    summary_sensor = AreaSummarySensor(coordinator, config_entry)
    entities: list[SensorEntity] = [summary_sensor]

    # Create measurement sensors conditionally
    if config_entry.data.get(CONF_POWER_ENTITY):
        power_sensor = PowerSensor(coordinator, config_entry)
        entities.append(power_sensor)
        summary_sensor.power_sensor = power_sensor

    if config_entry.data.get(CONF_ENERGY_ENTITY):
        energy_sensor = EnergySensor(coordinator, config_entry)
        entities.append(energy_sensor)
        summary_sensor.energy_sensor = energy_sensor

    if config_entry.data.get(CONF_TEMP_ENTITY):
        temperature_sensor = TemperatureSensor(coordinator, config_entry)
        entities.append(temperature_sensor)
        summary_sensor.temperature_sensor = temperature_sensor

    if config_entry.data.get(CONF_HUMIDITY_ENTITY):
        humidity_sensor = HumiditySensor(coordinator, config_entry)
        entities.append(humidity_sensor)
        summary_sensor.humidity_sensor = humidity_sensor

    if config_entry.data.get(CONF_CLIMATE_ENTITY):
        climate_target_sensor = ClimateTargetSensor(coordinator, config_entry)
        entities.append(climate_target_sensor)
        summary_sensor.climate_target_sensor = climate_target_sensor

    async_add_entities(entities)


class AreaSensorCoordinator:
    """Coordinator for area sensors."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.config_entry = config_entry
        self._listeners: list[Callable[..., Any]] = []
        self._sensors: list[SensorEntity] = []

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
        # Update all registered sensors
        for sensor in self._sensors:
            sensor.async_schedule_update_ha_state()  # pyright: ignore[reportUnusedCoroutine]
        return

    def register_sensor(self, sensor: SensorEntity) -> None:
        """Register a sensor."""
        self._sensors.append(sensor)

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

        # References to measurement sensors
        self.power_sensor: Optional["PowerSensor"] = None
        self.energy_sensor: Optional["EnergySensor"] = None
        self.temperature_sensor: Optional["TemperatureSensor"] = None
        self.humidity_sensor: Optional["HumiditySensor"] = None
        self.climate_target_sensor: Optional["ClimateTargetSensor"] = None

        # Register with coordinator
        coordinator.register_sensor(self)

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

        # Measurement attributes
        power_entity = data.get(CONF_POWER_ENTITY)
        if power_entity:
            power_value = get_numeric_state(self.hass, power_entity)
            if power_value is not None:
                power_state = self.hass.states.get(power_entity)
                unit = power_state.attributes.get("unit_of_measurement") if power_state else UNIT_WATT
                attrs["power"] = f"{power_value} {unit}"

        energy_entity = data.get(CONF_ENERGY_ENTITY)
        if energy_entity:
            energy_value = get_numeric_state(self.hass, energy_entity)
            if energy_value is not None:
                energy_state = self.hass.states.get(energy_entity)
                unit = energy_state.attributes.get("unit_of_measurement") if energy_state else UNIT_WATT_HOUR
                attrs["energy"] = f"{energy_value} {unit}"

        temp_entity = data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            temp_value = get_numeric_state(self.hass, temp_entity)
            if temp_value is not None:
                temp_state = self.hass.states.get(temp_entity)
                unit = temp_state.attributes.get("unit_of_measurement") if temp_state else UNIT_CELSIUS
                attrs["temperature"] = f"{temp_value} {unit}"

        humidity_entity = data.get(CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            humidity_value = get_numeric_state(self.hass, humidity_entity)
            if humidity_value is not None:
                humidity_state = self.hass.states.get(humidity_entity)
                unit = humidity_state.attributes.get("unit_of_measurement") if humidity_state else UNIT_HUMIDITY
                attrs["humidity"] = f"{humidity_value} {unit}"

        climate_entity = data.get(CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = self.hass.states.get(climate_entity)
            if climate_state and climate_state.attributes.get("temperature"):
                try:
                    target_value = float(climate_state.attributes["temperature"])
                    unit = climate_state.attributes.get("unit_of_measurement") or UNIT_CELSIUS
                    attrs["climate_target"] = f"{target_value} {unit}"
                except (ValueError, TypeError):
                    pass

        return attrs


class PowerSensor(SensorEntity):
    """Power measurement sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} Power"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_power"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_power" if area_name else None

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        power_entity = self.config_entry.data.get(CONF_POWER_ENTITY)
        if power_entity:
            return get_numeric_state(self.hass, power_entity)
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        power_entity = self.config_entry.data.get(CONF_POWER_ENTITY)
        if power_entity:
            state = self.hass.states.get(power_entity)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return UNIT_WATT


class EnergySensor(SensorEntity):
    """Energy measurement sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} Energy"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_energy"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_energy" if area_name else None

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        energy_entity = self.config_entry.data.get(CONF_ENERGY_ENTITY)
        if energy_entity:
            return get_numeric_state(self.hass, energy_entity)
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        energy_entity = self.config_entry.data.get(CONF_ENERGY_ENTITY)
        if energy_entity:
            state = self.hass.states.get(energy_entity)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return UNIT_WATT_HOUR


class TemperatureSensor(SensorEntity):
    """Temperature measurement sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} Temperature"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_temperature"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_temperature" if area_name else None

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        temp_entity = self.config_entry.data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            return get_numeric_state(self.hass, temp_entity)
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        temp_entity = self.config_entry.data.get(CONF_TEMP_ENTITY)
        if temp_entity:
            state = self.hass.states.get(temp_entity)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return UNIT_CELSIUS


class HumiditySensor(SensorEntity):
    """Humidity measurement sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} Humidity"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_humidity"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_humidity" if area_name else None

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        humidity_entity = self.config_entry.data.get(CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            return get_numeric_state(self.hass, humidity_entity)
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        humidity_entity = self.config_entry.data.get(CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            state = self.hass.states.get(humidity_entity)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return UNIT_HUMIDITY


class ClimateTargetSensor(SensorEntity):
    """Climate target temperature sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        area_name = str(config_entry.data.get(CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} Climate Target"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_climate_target"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {config_entry.data[CONF_AREA_NAME]}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> Optional[str]:
        """Suggest object_id."""
        area_name = str(self.config_entry.data.get(CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_climate_target" if area_name else None

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        climate_entity = self.config_entry.data.get(CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = self.hass.states.get(climate_entity)
            if climate_state and climate_state.attributes.get("temperature"):
                try:
                    return float(climate_state.attributes["temperature"])
                except (ValueError, TypeError):
                    pass
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        climate_entity = self.config_entry.data.get(CONF_CLIMATE_ENTITY)
        if climate_entity:
            state = self.hass.states.get(climate_entity)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return UNIT_CELSIUS
