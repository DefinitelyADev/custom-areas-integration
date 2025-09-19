"""Test the Custom Areas Integration sensors."""

import sys
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from custom_components.custom_areas.const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_AREA_NAME,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    STATE_ACTIVE,
)
from custom_components.custom_areas.sensor import (
    AreaSensorCoordinator,
    AreaSummarySensor,
    ClimateTargetSensor,
    EnergySensor,
    HumiditySensor,
    PowerSensor,
    TemperatureSensor,
)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_AREA_NAME: "Test Area",
        CONF_POWER_ENTITY: "sensor.power",
        CONF_ENERGY_ENTITY: "sensor.energy",
        CONF_TEMP_ENTITY: "sensor.temperature",
        CONF_HUMIDITY_ENTITY: "sensor.humidity",
        CONF_MOTION_ENTITY: "binary_sensor.motion",
        CONF_WINDOW_ENTITY: "binary_sensor.window",
        CONF_CLIMATE_ENTITY: "climate.thermostat",
        CONF_ACTIVE_THRESHOLD: 50.0,
    }
    return entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant."""
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator(mock_hass, mock_config_entry):
    """Mock coordinator."""
    coordinator = AreaSensorCoordinator(mock_hass, mock_config_entry)
    return coordinator


def test_area_summary_sensor_initialization(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor initialization."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    assert sensor.name == "Test Area"
    assert sensor.unique_id == "custom_area_test_entry_id_summary"
    assert sensor.should_poll is False


def test_area_summary_sensor_state_unknown(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor state when no entities configured."""
    # Configure entry with no entities
    mock_config_entry.data = {CONF_AREA_NAME: "Test Area"}

    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock hass.states.get to return None
    mock_hass.states.get = MagicMock(return_value=None)

    assert sensor.state == STATE_UNKNOWN


def test_area_summary_sensor_state_idle(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor state when entities exist but no activity."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock states for entities
    power_state = MagicMock()
    power_state.state = "10.0"  # Below threshold

    motion_state = MagicMock()
    motion_state.state = STATE_OFF

    def mock_get(entity_id):
        if entity_id == "sensor.power":
            return power_state
        elif entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.state == STATE_IDLE


def test_area_summary_sensor_state_active_motion(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor state when motion detected."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock motion state as ON
    motion_state = MagicMock()
    motion_state.state = STATE_ON

    def mock_get(entity_id):
        if entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.state == STATE_ACTIVE


def test_area_summary_sensor_state_active_power(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor state when power above threshold."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock power state above threshold
    power_state = MagicMock()
    power_state.state = "75.0"  # Above 50.0 threshold

    motion_state = MagicMock()
    motion_state.state = STATE_OFF

    def mock_get(entity_id):
        if entity_id == "sensor.power":
            return power_state
        elif entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.state == STATE_ACTIVE


def test_area_summary_sensor_attributes(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor attributes."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Create and assign measurement sensors
    power_sensor = PowerSensor(mock_coordinator, mock_config_entry)
    power_sensor.hass = mock_hass
    setattr(power_sensor, "_attr_unit_of_measurement", "W")
    sensor.power_sensor = power_sensor

    energy_sensor = EnergySensor(mock_coordinator, mock_config_entry)
    energy_sensor.hass = mock_hass
    setattr(energy_sensor, "_attr_unit_of_measurement", "Wh")
    sensor.energy_sensor = energy_sensor

    temperature_sensor = TemperatureSensor(mock_coordinator, mock_config_entry)
    temperature_sensor.hass = mock_hass
    setattr(temperature_sensor, "_attr_unit_of_measurement", "°C")
    sensor.temperature_sensor = temperature_sensor

    humidity_sensor = HumiditySensor(mock_coordinator, mock_config_entry)
    humidity_sensor.hass = mock_hass
    setattr(humidity_sensor, "_attr_unit_of_measurement", "%")
    sensor.humidity_sensor = humidity_sensor

    climate_target_sensor = ClimateTargetSensor(mock_coordinator, mock_config_entry)
    climate_target_sensor.hass = mock_hass
    setattr(climate_target_sensor, "_attr_unit_of_measurement", "°C")
    sensor.climate_target_sensor = climate_target_sensor

    # Mock states
    motion_state = MagicMock()
    motion_state.state = STATE_ON

    window_state = MagicMock()
    window_state.state = STATE_OFF

    climate_state = MagicMock()
    climate_state.state = "heat"
    climate_state.attributes = {"temperature": 21.5, "unit_of_measurement": "°C"}

    power_state = MagicMock()
    power_state.state = "25.5"
    power_state.attributes = {"unit_of_measurement": "W"}

    energy_state = MagicMock()
    energy_state.state = "150.0"
    energy_state.attributes = {"unit_of_measurement": "Wh"}

    temp_state = MagicMock()
    temp_state.state = "22.3"
    temp_state.attributes = {"unit_of_measurement": "°C"}

    humidity_state = MagicMock()
    humidity_state.state = "65.0"
    humidity_state.attributes = {"unit_of_measurement": "%"}

    def mock_get(entity_id):
        if entity_id == "binary_sensor.motion":
            return motion_state
        elif entity_id == "binary_sensor.window":
            return window_state
        elif entity_id == "climate.thermostat":
            return climate_state
        elif entity_id == "sensor.power":
            return power_state
        elif entity_id == "sensor.energy":
            return energy_state
        elif entity_id == "sensor.temperature":
            return temp_state
        elif entity_id == "sensor.humidity":
            return humidity_state
        return None

    mock_hass.states.get = mock_get

    attrs = sensor.extra_state_attributes

    # Binary sensor attributes
    assert attrs["occupied"] is True
    assert attrs["window_open"] is False
    assert attrs["climate_mode"] == "heat"

    # Measurement attributes should now be present as strings with units
    assert attrs["power"] == "25.5 W"
    assert attrs["energy"] == "150.0 Wh"
    assert attrs["temperature"] == "22.3 °C"
    assert attrs["humidity"] == "65.0 %"
    assert attrs["climate_target"] == "21.5 °C"


def test_area_summary_sensor_icon(mock_coordinator, mock_config_entry, mock_hass):
    """Test area summary sensor icon selection."""
    sensor = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Test default icon
    motion_state = MagicMock()
    motion_state.state = STATE_OFF

    window_state = MagicMock()
    window_state.state = STATE_OFF

    def mock_get(entity_id):
        if entity_id == "binary_sensor.motion":
            return motion_state
        elif entity_id == "binary_sensor.window":
            return window_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.icon == "mdi:texture-box"

    # Test motion icon
    motion_state.state = STATE_ON
    assert sensor.icon == "mdi:motion-sensor"

    # Test window icon (takes precedence over motion)
    window_state.state = STATE_ON
    assert sensor.icon == "mdi:window-open-variant"


def test_unit_constant_fallbacks(monkeypatch):
    """Test unit constant import fallbacks work correctly."""
    from custom_components.custom_areas import sensor

    # Mock sys.modules to simulate missing modules
    original_modules = dict(sys.modules)

    # Remove the modules we want to test as missing
    modules_to_remove = [
        "homeassistant.util.unit_system",
        "homeassistant.util.unit_conversion",
        "homeassistant.const",
    ]

    for module in modules_to_remove:
        sys.modules.pop(module, None)

    try:
        # Reload the module to test the import logic
        import importlib

        importlib.reload(sensor)

        # Verify constants are set to expected fallback values
        assert sensor.UNIT_CELSIUS == "°C"
        assert sensor.UNIT_WATT == "W"
        assert sensor.UNIT_WATT_HOUR == "Wh"

    finally:
        # Restore original modules
        sys.modules.update(original_modules)


def test_unit_constants_with_deprecated_fallback(monkeypatch):
    """Test that deprecated constants are used when new ones fail."""
    from custom_components.custom_areas import sensor

    # Mock only the new unit system modules as missing
    original_modules = dict(sys.modules)

    modules_to_remove = [
        "homeassistant.util.unit_system",
        "homeassistant.util.unit_conversion",
    ]

    for module in modules_to_remove:
        sys.modules.pop(module, None)

    try:
        # Reload to test fallback to deprecated constants
        import importlib

        importlib.reload(sensor)

        # Should use deprecated constants (which will show deprecation
        # warnings but work)
        assert sensor.UNIT_CELSIUS is not None
        assert sensor.UNIT_WATT is not None
        assert sensor.UNIT_WATT_HOUR is not None

        # The deprecated constants have the same string values as our fallbacks
        # This is expected and correct behavior
        assert sensor.UNIT_CELSIUS == "°C"
        assert sensor.UNIT_WATT == "W"
        assert sensor.UNIT_WATT_HOUR == "Wh"

    finally:
        # Restore original modules
        sys.modules.update(original_modules)


def test_sensor_functionality_with_fallback_units(mock_coordinator, mock_config_entry, mock_hass):
    """Test that summary sensor works correctly with simplified attributes."""
    sensor_instance = AreaSummarySensor(mock_coordinator, mock_config_entry)
    sensor_instance.hass = mock_hass

    # Mock states - only binary sensors for summary sensor
    motion_state = MagicMock()
    motion_state.state = STATE_ON

    def mock_get(entity_id):
        if entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    # Test that only appropriate attributes are generated for summary sensor
    attrs = sensor_instance.extra_state_attributes

    # Only binary sensor attributes should be present
    assert attrs["occupied"] is True

    # Numeric measurement attributes should no longer be in summary sensor
    assert "power_w" not in attrs
    assert "energy_wh" not in attrs
    assert "temperature_c" not in attrs

    # Display attributes should no longer be in summary sensor
    assert "power" not in attrs
    assert "energy" not in attrs
    assert "temperature" not in attrs
