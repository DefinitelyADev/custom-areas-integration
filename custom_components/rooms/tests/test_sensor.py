"""Test the Rooms sensors."""
import pytest
from unittest.mock import MagicMock, AsyncMock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant

from custom_components.rooms.const import (
    CONF_ACTIVE_THRESHOLD,
    CONF_MOTION_ENTITY,
    CONF_POWER_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ENTITY,
    CONF_WINDOW_ENTITY,
    DOMAIN,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_UNKNOWN,
)
from custom_components.rooms.sensor import RoomSummarySensor, RoomSensorCoordinator


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_ROOM_NAME: "Test Room",
        CONF_POWER_ENTITY: "sensor.power",
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


def test_room_summary_sensor_initialization(mock_coordinator, mock_config_entry, mock_hass):
    """Test room summary sensor initialization."""
    sensor = RoomSummarySensor(mock_coordinator, mock_config_entry)
    sensor.hass = mock_hass

    assert sensor.name == "Test Room"
    assert sensor.unique_id == "test_entry_id_summary"
    assert sensor.should_poll is False


def test_room_summary_sensor_state_unknown(mock_coordinator, mock_config_entry, mock_hass):
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


def test_room_summary_sensor_state_active_motion(mock_coordinator, mock_config_entry, mock_hass):
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


def test_room_summary_sensor_state_active_power(mock_coordinator, mock_config_entry, mock_hass):
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

    temp_state = MagicMock()
    temp_state.state = "22.3"

    motion_state = MagicMock()
    motion_state.state = STATE_ON

    def mock_get(entity_id):
        if entity_id == "sensor.power":
            return power_state
        elif entity_id == "sensor.temperature":
            return temp_state
        elif entity_id == "binary_sensor.motion":
            return motion_state
        return None

    mock_hass.states.get = mock_get

    attrs = sensor.extra_state_attributes

    assert attrs["power_w"] == 25.5
    assert attrs["temperature_c"] == 22.3
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
