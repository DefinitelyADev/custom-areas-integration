"""Test the Rooms sensors."""

import sys
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from custom_components.rooms.const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_ENERGY_ENTITY,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_UNKNOWN,
)
from custom_components.rooms.sensor import RoomSensorCoordinator, RoomSummarySensor


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_ROOM_NAME: "Test Room",
        CONF_POWER_ENTITY: "sensor.power",
        CONF_ENERGY_ENTITY: "sensor.energy",
        CONF_TEMP_ENTITY: "sensor.temperature",
        CONF_MOTION_ENTITY: "binary_sensor.motion",
        CONF_WINDOW_ENTITY: "binary_sensor.window",
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
    coordinator = RoomSensorCoordinator(mock_hass, mock_config_entry)
    return coordinator


def test_room_summary_sensor_initialization(
    mock_coordinator, mock_config_entry, mock_hass
):
    """Test room summary sensor initialization."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    assert sensor.name == "Test Room"
    assert sensor.unique_id == "test_entry_id_summary"
    assert sensor.should_poll is False


def test_room_summary_sensor_state_unknown(
    mock_coordinator, mock_config_entry, mock_hass
):
    """Test room summary sensor state when no entities configured."""
    # Configure entry with no entities
    mock_config_entry.data = {CONF_ROOM_NAME: "Test Room"}

    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock hass.states.get to return None
    mock_hass.states.get = MagicMock(return_value=None)

    assert sensor.state == STATE_UNKNOWN


def test_room_summary_sensor_state_idle(mock_coordinator, mock_config_entry, mock_hass):
    """Test room summary sensor state when entities exist but no activity."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
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


def test_room_summary_sensor_state_active_motion(
    mock_coordinator, mock_config_entry, mock_hass
):
    """Test room summary sensor state when motion detected."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
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


def test_room_summary_sensor_state_active_power(
    mock_coordinator, mock_config_entry, mock_hass
):
    """Test room summary sensor state when power above threshold."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
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


def test_room_summary_sensor_attributes(mock_coordinator, mock_config_entry, mock_hass):
    """Test room summary sensor attributes."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    # Mock states
    power_state = MagicMock()
    power_state.state = "25.5"

    energy_state = MagicMock()
    energy_state.state = "150.0"

    temp_state = MagicMock()
    temp_state.state = "22.3"

    motion_state = MagicMock()
    motion_state.state = STATE_ON

    def mock_get(entity_id):
        if entity_id == "sensor.power":
            return power_state
        elif entity_id == "sensor.energy":
            return energy_state
        elif entity_id == "sensor.temperature":
            return temp_state
        elif entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    attrs = sensor.extra_state_attributes

    assert attrs["power_w"] == 25.5
    assert attrs["power_w_unit"] == "W"
    assert attrs["energy_wh"] == 150.0
    assert attrs["energy_wh_unit"] == "Wh"
    assert attrs["temperature_c"] == 22.3
    assert attrs["temperature_c_unit"] == "°C"
    assert attrs["occupied"] is True


def test_room_summary_sensor_icon(mock_coordinator, mock_config_entry, mock_hass):
    """Test room summary sensor icon selection."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
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

    assert sensor.icon == "mdi:home"

    # Test motion icon
    motion_state.state = STATE_ON
    assert sensor.icon == "mdi:motion-sensor"

    # Test window icon (takes precedence over motion)
    window_state.state = STATE_ON
    assert sensor.icon == "mdi:window-open-variant"


def test_unit_constant_fallbacks(monkeypatch):
    """Test unit constant import fallbacks work correctly."""
    from custom_components.rooms import sensor

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
    from custom_components.rooms import sensor

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


def test_sensor_functionality_with_fallback_units(
    mock_coordinator, mock_config_entry, mock_hass
):
    """Test that sensor works correctly even with fallback unit constants."""
    sensor_instance = RoomSummarySensor(mock_coordinator, mock_config_entry)
    sensor_instance.hass = mock_hass

    # Mock states
    power_state = MagicMock()
    power_state.state = "100.0"

    energy_state = MagicMock()
    energy_state.state = "500.0"

    temp_state = MagicMock()
    temp_state.state = "25.5"

    def mock_get(entity_id):
        if entity_id == "sensor.power":
            return power_state
        elif entity_id == "sensor.energy":
            return energy_state
        elif entity_id == "sensor.temperature":
            return temp_state
        return None

    mock_hass.states.get = mock_get

    # Test that attributes are generated correctly regardless of which
    # unit constants are used
    attrs = sensor_instance.extra_state_attributes

    assert attrs["power_w"] == 100.0
    assert "power_w_unit" in attrs
    assert attrs["energy_wh"] == 500.0
    assert "energy_wh_unit" in attrs
    assert attrs["temperature_c"] == 25.5
    assert "temperature_c_unit" in attrs

    # Verify unit values are strings (regardless of which fallback was used)
    assert isinstance(attrs["power_w_unit"], str)
    assert isinstance(attrs["energy_wh_unit"], str)
    assert isinstance(attrs["temperature_c_unit"], str)
