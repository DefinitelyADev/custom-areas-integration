"""Sensor platform for Custom Areas Integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    STATE_IDLE,
    STATE_ON,
    STATE_UNKNOWN,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

if TYPE_CHECKING:
    from homeassistant.helpers.event import EventStateChangedData

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


def get_numeric_state(hass: HomeAssistant, entity_id: str) -> float | None:
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


def _get_option(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Read a config value with options-take-precedence-over-data semantics.

    `entry.options` is populated by the options flow when an existing entry
    is reconfigured. Original entries have `entry.options == {}`, so they
    transparently keep reading from `entry.data` — no migration needed.
    """
    if key in entry.options:
        return entry.options[key]
    return entry.data.get(key, default)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    summary_sensor = AreaSummarySensor(coordinator, config_entry)
    entities: list[SensorEntity] = [summary_sensor]

    # Create measurement sensors conditionally. Each tuple is
    # (config_key, suffix, name_suffix, default_unit, source_attribute,
    #  summary_attr) where summary_attr is the AreaSummarySensor attribute
    # name kept for backward compatibility.
    measurement_specs = (
        (CONF_POWER_ENTITY, "power", "Power", UnitOfPower.WATT, None, "power_sensor"),
        (CONF_ENERGY_ENTITY, "energy", "Energy", UnitOfEnergy.WATT_HOUR, None, "energy_sensor"),
        (CONF_TEMP_ENTITY, "temperature", "Temperature", UnitOfTemperature.CELSIUS, None, "temperature_sensor"),
        (CONF_HUMIDITY_ENTITY, "humidity", "Humidity", PERCENTAGE, None, "humidity_sensor"),
        (
            CONF_CLIMATE_ENTITY,
            "climate_target",
            "Climate Target",
            UnitOfTemperature.CELSIUS,
            "temperature",
            "climate_target_sensor",
        ),
    )

    for config_key, suffix, name_suffix, default_unit, source_attribute, summary_attr in measurement_specs:
        if _get_option(config_entry, config_key):
            measurement_sensor = AreaMeasurementSensor(
                coordinator,
                config_entry,
                config_key=config_key,
                suffix=suffix,
                name_suffix=name_suffix,
                default_unit=default_unit,
                source_attribute=source_attribute,
            )
            entities.append(measurement_sensor)
            setattr(summary_sensor, summary_attr, measurement_sensor)

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
            entity_id = _get_option(self.config_entry, key)
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
            self._listeners.append(listener)
            _LOGGER.debug("Successfully registered state change listener")

    @callback
    def _handle_state_change(self, _: Event[EventStateChangedData]) -> None:
        """Handle state change events."""
        # Update all registered sensors
        for sensor in self._sensors:
            sensor.async_schedule_update_ha_state()
        return

    def register_sensor(self, sensor: SensorEntity) -> None:
        """Register a sensor."""
        self._sensors.append(sensor)

    def shutdown(self):
        """Clean up listeners.

        Synchronous despite the surrounding HA `async_*` convention — this
        method only calls listener-removal callbacks, no awaitables.
        """
        for listener in self._listeners:
            listener()


class AreaSummarySensor(SensorEntity):
    """Area summary sensor."""

    def __init__(self, coordinator: AreaSensorCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        # Display name comes from the `name` property below (so it tolerates
        # entry renames). `_attr_name` is intentionally not set — the property
        # would override it anyway.
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_summary"
        self._attr_should_poll = False

        # References to measurement sensors. Attribute names kept (`power_sensor`
        # etc.) for backward compatibility; the concrete type is now the
        # parameterized AreaMeasurementSensor.
        self.power_sensor: "AreaMeasurementSensor | None" = None
        self.energy_sensor: "AreaMeasurementSensor | None" = None
        self.temperature_sensor: "AreaMeasurementSensor | None" = None
        self.humidity_sensor: "AreaMeasurementSensor | None" = None
        self.climate_target_sensor: "AreaMeasurementSensor | None" = None

        # Register with coordinator
        coordinator.register_sensor(self)

        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {_get_option(config_entry, CONF_AREA_NAME)}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor (display name without area_ prefix)."""
        area_name = _get_option(self.config_entry, CONF_AREA_NAME, "")
        return str(area_name) if area_name else ""

    @property
    def suggested_object_id(self) -> str | None:
        """Suggest object_id so entity_id gets a area_ prefix.

        Home Assistant will slugify this into the final object_id.
        """
        area_name = str(_get_option(self.config_entry, CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}" if area_name else None

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        # Check motion first
        motion_entity = _get_option(self.config_entry, CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            if motion_state and motion_state.state == STATE_ON:
                return STATE_ACTIVE

        # Check power threshold
        power_entity = _get_option(self.config_entry, CONF_POWER_ENTITY)
        active_threshold = _get_option(self.config_entry, CONF_ACTIVE_THRESHOLD, DEFAULT_ACTIVE_THRESHOLD)
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
            _get_option(self.config_entry, CONF_POWER_ENTITY),
            _get_option(self.config_entry, CONF_ENERGY_ENTITY),
            _get_option(self.config_entry, CONF_TEMP_ENTITY),
            _get_option(self.config_entry, CONF_HUMIDITY_ENTITY),
            _get_option(self.config_entry, CONF_MOTION_ENTITY),
            _get_option(self.config_entry, CONF_WINDOW_ENTITY),
            _get_option(self.config_entry, CONF_CLIMATE_ENTITY),
        ]

        if any(entity for entity in core_entities if entity):
            return str(STATE_IDLE)

        return str(STATE_UNKNOWN)

    @property
    def icon(self) -> str:
        """Return the icon."""
        # Check window first
        window_entity = _get_option(self.config_entry, CONF_WINDOW_ENTITY)
        if window_entity:
            window_state = self.hass.states.get(window_entity)
            if window_state and window_state.state == STATE_ON:
                return ICON_WINDOW_OPEN

        # Check motion
        motion_entity = _get_option(self.config_entry, CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            if motion_state and motion_state.state == STATE_ON:
                return ICON_MOTION

        # Return configured icon or default
        icon_value = _get_option(self.config_entry, CONF_ICON, DEFAULT_ICON)
        return str(icon_value) if icon_value is not None else DEFAULT_ICON

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs: dict[str, Any] = {}

        # Binary sensor attributes (motion, window, climate mode)
        motion_entity = _get_option(self.config_entry, CONF_MOTION_ENTITY)
        if motion_entity:
            motion_state = self.hass.states.get(motion_entity)
            attrs["occupied"] = motion_state.state == STATE_ON if motion_state else False

        window_entity = _get_option(self.config_entry, CONF_WINDOW_ENTITY)
        if window_entity:
            window_state = self.hass.states.get(window_entity)
            attrs["window_open"] = window_state.state == STATE_ON if window_state else False

        climate_entity = _get_option(self.config_entry, CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = self.hass.states.get(climate_entity)
            if climate_state:
                attrs["climate_mode"] = climate_state.state

        # Measurement attributes — ship both a numeric (`*_w`, `*_wh`, `*_c`, `*_pct`)
        # and stringified-with-unit form per the documented contract (README.md,
        # docs/api.md). Pair each numeric/string emission so the contract is
        # grep-able from a single block.
        power_entity = _get_option(self.config_entry, CONF_POWER_ENTITY)
        if power_entity:
            power_value = get_numeric_state(self.hass, power_entity)
            if power_value is not None:
                power_state = self.hass.states.get(power_entity)
                unit = power_state.attributes.get("unit_of_measurement") if power_state else UnitOfPower.WATT
                attrs["power_w"] = power_value
                attrs["power"] = f"{power_value} {unit}"

        energy_entity = _get_option(self.config_entry, CONF_ENERGY_ENTITY)
        if energy_entity:
            energy_value = get_numeric_state(self.hass, energy_entity)
            if energy_value is not None:
                energy_state = self.hass.states.get(energy_entity)
                unit = energy_state.attributes.get("unit_of_measurement") if energy_state else UnitOfEnergy.WATT_HOUR
                attrs["energy_wh"] = energy_value
                attrs["energy"] = f"{energy_value} {unit}"

        temp_entity = _get_option(self.config_entry, CONF_TEMP_ENTITY)
        if temp_entity:
            temp_value = get_numeric_state(self.hass, temp_entity)
            if temp_value is not None:
                temp_state = self.hass.states.get(temp_entity)
                unit = temp_state.attributes.get("unit_of_measurement") if temp_state else UnitOfTemperature.CELSIUS
                attrs["temperature_c"] = temp_value
                attrs["temperature"] = f"{temp_value} {unit}"

        humidity_entity = _get_option(self.config_entry, CONF_HUMIDITY_ENTITY)
        if humidity_entity:
            humidity_value = get_numeric_state(self.hass, humidity_entity)
            if humidity_value is not None:
                humidity_state = self.hass.states.get(humidity_entity)
                unit = humidity_state.attributes.get("unit_of_measurement") if humidity_state else PERCENTAGE
                attrs["humidity_pct"] = humidity_value
                attrs["humidity"] = f"{humidity_value} {unit}"

        climate_entity = _get_option(self.config_entry, CONF_CLIMATE_ENTITY)
        if climate_entity:
            climate_state = self.hass.states.get(climate_entity)
            if climate_state and climate_state.attributes.get("temperature"):
                try:
                    target_value = float(climate_state.attributes["temperature"])
                    unit = climate_state.attributes.get("unit_of_measurement") or UnitOfTemperature.CELSIUS
                    attrs["climate_target_c"] = target_value
                    attrs["climate_target"] = f"{target_value} {unit}"
                except (ValueError, TypeError):
                    pass

        return attrs


class AreaMeasurementSensor(SensorEntity):
    """Parameterized measurement sensor.

    Replaces the five near-identical PowerSensor / EnergySensor /
    TemperatureSensor / HumiditySensor / ClimateTargetSensor classes
    that differed only by config key, suffix, default unit, and (for
    ClimateTarget) the fact that the reading is on `state.attributes`
    rather than `state.state`.

    Behavior is byte-identical to the originals — guarded by
    test_sensor_characterization.py.
    """

    def __init__(
        self,
        coordinator: "AreaSensorCoordinator",
        config_entry: ConfigEntry,
        config_key: str,
        suffix: str,
        name_suffix: str,
        default_unit: str,
        source_attribute: str | None = None,
    ) -> None:
        """Initialize a measurement sensor.

        Args:
            coordinator: The shared area coordinator (fanned-out updates).
            config_entry: The HA config entry backing this area.
            config_key: Key in entry.data/options pointing at the source
                entity_id (e.g. CONF_POWER_ENTITY).
            suffix: Used in unique_id and object_id (e.g. "power").
            name_suffix: Used in display name (e.g. "Power").
            default_unit: Fallback unit_of_measurement when the source
                entity doesn't expose one.
            source_attribute: When None, read the source's `state.state`
                and parse as float. When set, read
                `state.attributes[source_attribute]` instead. The latter
                is the ClimateTarget shape (`source_attribute="temperature"`).
        """
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._config_key = config_key
        self._suffix = suffix
        self._default_unit = default_unit
        self._source_attribute = source_attribute

        area_name = str(_get_option(config_entry, CONF_AREA_NAME, ""))
        self._attr_name = f"{area_name} {name_suffix}"
        self._attr_unique_id = f"custom_area_{config_entry.entry_id}_{suffix}"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Area: {_get_option(config_entry, CONF_AREA_NAME)}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )
        coordinator.register_sensor(self)

    @property
    def suggested_object_id(self) -> str | None:
        """Suggest object_id (HA slugifies this for the final entity_id)."""
        area_name = str(_get_option(self.config_entry, CONF_AREA_NAME, "")).strip()
        return f"custom_area_{area_name}_{self._suffix}" if area_name else None

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor.

        For non-climate sensors (`source_attribute is None`): the parsed
        float of the source entity's `state.state`.
        For climate_target (`source_attribute == "temperature"`): the
        parsed float of `state.attributes["temperature"]`. Returns None
        when the attribute is falsy, missing, or non-numeric — preserving
        the pre-refactor behaviour exactly (including the "0.0 → None"
        edge case that fell out of `if attributes.get(...)`).
        """
        entity_id = _get_option(self.config_entry, self._config_key)
        if not entity_id:
            return None

        if self._source_attribute is None:
            return get_numeric_state(self.hass, entity_id)

        state = self.hass.states.get(entity_id)
        if state and state.attributes.get(self._source_attribute):
            try:
                return float(state.attributes[self._source_attribute])
            except (ValueError, TypeError):
                pass
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement.

        Returns the source entity's `unit_of_measurement` attribute when
        present; otherwise falls back to `default_unit`.
        """
        entity_id = _get_option(self.config_entry, self._config_key)
        if entity_id:
            state = self.hass.states.get(entity_id)
            if state and state.attributes.get("unit_of_measurement"):
                return state.attributes["unit_of_measurement"]  # type: ignore[no-any-return]
        return self._default_unit
