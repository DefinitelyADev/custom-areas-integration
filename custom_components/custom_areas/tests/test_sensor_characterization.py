"""Characterization tests for the measurement sensor classes.

These tests pin the public surface (unique_id, name, suggested_object_id,
device_info, native_value, native_unit_of_measurement) of the five
measurement sensor classes so the M1 refactor (collapsing the five
near-identical classes into a single parameterized `AreaMeasurementSensor`)
can be proven byte-identical.

If any case here regresses after the M1 refactor, revert M1 — do NOT patch
this file to match the new behaviour. That would defeat the gate.

`EXPECTED_SENSOR_SURFACE` at the top is the explicit, grep-able contract.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.custom_areas.const import (
    CONF_AREA_NAME,
    CONF_CLIMATE_ENTITY,
    CONF_ENERGY_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TEMP_ENTITY,
    DOMAIN,
)
from custom_components.custom_areas.sensor import AreaMeasurementSensor, AreaSensorCoordinator

# Per-sensor specs. Construction now goes through `AreaMeasurementSensor` for
# every type — pre-M1 each spec named its dedicated class here (PowerSensor,
# EnergySensor, ...). The collapse to a single parameterized class is the
# refactor under test; the *assertions* about output strings, device_info,
# native_value, and native_unit are unchanged from the pre-M1 snapshot.
EXPECTED_SENSOR_SURFACE: dict[str, dict[str, Any]] = {
    "power": {
        "config_key": CONF_POWER_ENTITY,
        "entity_id": "sensor.power",
        "unique_id_suffix": "power",
        "name_suffix": "Power",
        "default_unit": UnitOfPower.WATT,
        "source_attribute": None,
    },
    "energy": {
        "config_key": CONF_ENERGY_ENTITY,
        "entity_id": "sensor.energy",
        "unique_id_suffix": "energy",
        "name_suffix": "Energy",
        "default_unit": UnitOfEnergy.WATT_HOUR,
        "source_attribute": None,
    },
    "temperature": {
        "config_key": CONF_TEMP_ENTITY,
        "entity_id": "sensor.temperature",
        "unique_id_suffix": "temperature",
        "name_suffix": "Temperature",
        "default_unit": UnitOfTemperature.CELSIUS,
        "source_attribute": None,
    },
    "humidity": {
        "config_key": CONF_HUMIDITY_ENTITY,
        "entity_id": "sensor.humidity",
        "unique_id_suffix": "humidity",
        "name_suffix": "Humidity",
        "default_unit": PERCENTAGE,
        "source_attribute": None,
    },
    "climate_target": {
        "config_key": CONF_CLIMATE_ENTITY,
        "entity_id": "climate.thermostat",
        "unique_id_suffix": "climate_target",
        "name_suffix": "Climate Target",
        "default_unit": UnitOfTemperature.CELSIUS,
        "source_attribute": "temperature",
    },
}


# Parametrize tests across all 5 sensor types so any post-M1 divergence
# shows up as a single failing case in the test report.
SENSOR_IDS = list(EXPECTED_SENSOR_SURFACE.keys())


@pytest.fixture
def mock_config_entry():
    """Mock config entry covering all five measurement sources.

    `entry.options` is set to `{}` so the options-take-precedence helper in
    `sensor._get_option` walks through to `entry.data`. Older HA versions
    don't expose `options` on `ConfigEntry`'s class-level spec.
    """
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_AREA_NAME: "Test Area",
        CONF_POWER_ENTITY: "sensor.power",
        CONF_ENERGY_ENTITY: "sensor.energy",
        CONF_TEMP_ENTITY: "sensor.temperature",
        CONF_HUMIDITY_ENTITY: "sensor.humidity",
        CONF_CLIMATE_ENTITY: "climate.thermostat",
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant with a controllable states registry."""
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator(mock_hass, mock_config_entry):
    """Coordinator backed by the mocked hass + config entry."""
    return AreaSensorCoordinator(mock_hass, mock_config_entry)


def _make_sensor(spec: dict[str, Any], mock_coordinator, mock_config_entry, mock_hass):
    """Instantiate AreaMeasurementSensor for a given spec and wire `hass`."""
    sensor = AreaMeasurementSensor(
        mock_coordinator,
        mock_config_entry,
        config_key=spec["config_key"],
        suffix=spec["unique_id_suffix"],
        name_suffix=spec["name_suffix"],
        default_unit=spec["default_unit"],
        source_attribute=spec["source_attribute"],
    )
    sensor.hass = mock_hass
    return sensor


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_unique_id(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """unique_id follows the `custom_area_<entry_id>_<suffix>` pattern."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    expected = f"custom_area_test_entry_id_{spec['unique_id_suffix']}"
    assert sensor.unique_id == expected


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_attr_name(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """_attr_name follows the `<Area Name> <Name Suffix>` pattern."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    expected = f"Test Area {spec['name_suffix']}"
    assert sensor._attr_name == expected


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_suggested_object_id(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """suggested_object_id returns `custom_area_<area_name>_<suffix>`.

    The area name is stripped but not slugified by the property itself —
    Home Assistant slugifies the result when computing the final entity_id.
    The characterization here captures the property's raw return value.
    """
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    expected = f"custom_area_Test Area_{spec['unique_id_suffix']}"
    assert sensor.suggested_object_id == expected


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_device_info_identifiers(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """device_info["identifiers"] anchors the sensor to the area device."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    assert sensor.device_info is not None
    # DeviceInfo is a TypedDict with optional keys; subscript suppresses are
    # for pyright since the integration always sets these.
    assert sensor.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}  # pyright: ignore[reportTypedDictNotRequiredAccess]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_device_info_name(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """device_info["name"] follows the `Area: <area_name>` pattern."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    assert sensor.device_info is not None
    assert sensor.device_info["name"] == "Area: Test Area"  # pyright: ignore[reportTypedDictNotRequiredAccess]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_device_info_manufacturer(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """device_info["manufacturer"] is the constant `Areas Integration`."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    assert sensor.device_info is not None
    assert sensor.device_info["manufacturer"] == "Areas Integration"  # pyright: ignore[reportTypedDictNotRequiredAccess]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_device_info_model(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """device_info["model"] is the constant `Area Sensor`."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    assert sensor.device_info is not None
    assert sensor.device_info["model"] == "Area Sensor"  # pyright: ignore[reportTypedDictNotRequiredAccess]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_native_unit_uses_source_entity_unit(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """native_unit_of_measurement returns the source entity's unit when set."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    # Source entity reports its own unit.
    source_state = MagicMock()
    source_state.state = "1.0"
    source_state.attributes = {"unit_of_measurement": "custom-unit", "temperature": 1.0}

    def mock_get(entity_id):
        if entity_id == spec["entity_id"]:
            return source_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.native_unit_of_measurement == "custom-unit"


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_native_unit_falls_back_when_attribute_missing(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """Falls back to `default_unit` when source entity has no unit attribute."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    source_state = MagicMock()
    source_state.state = "1.0"
    source_state.attributes = {"temperature": 1.0}  # no unit_of_measurement

    def mock_get(entity_id):
        if entity_id == spec["entity_id"]:
            return source_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.native_unit_of_measurement == spec["default_unit"]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_native_unit_falls_back_when_entity_missing(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """Falls back to `default_unit` when the source entity doesn't exist."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    mock_hass.states.get = MagicMock(return_value=None)

    assert sensor.native_unit_of_measurement == spec["default_unit"]


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_native_value_parses_source(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """native_value returns the parsed float of the source reading.

    For non-climate sensors: parsed `state.state`.
    For climate_target:     parsed `state.attributes["temperature"]`.
    """
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    source_state = MagicMock()
    source_state.state = "25.5"
    source_state.attributes = {"unit_of_measurement": "X", "temperature": 25.5}

    def mock_get(entity_id):
        if entity_id == spec["entity_id"]:
            return source_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.native_value == 25.5


@pytest.mark.parametrize("sensor_id", SENSOR_IDS)
def test_native_value_none_when_entity_missing(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """native_value is None when the source entity doesn't exist."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    mock_hass.states.get = MagicMock(return_value=None)

    assert sensor.native_value is None


@pytest.mark.parametrize("sensor_id", ["power", "energy", "temperature", "humidity"])
def test_native_value_none_for_non_numeric_state(sensor_id, mock_coordinator, mock_config_entry, mock_hass):
    """native_value is None when the source state isn't a float (non-climate)."""
    spec = EXPECTED_SENSOR_SURFACE[sensor_id]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    source_state = MagicMock()
    source_state.state = "not-a-number"
    source_state.attributes = {}

    def mock_get(entity_id):
        if entity_id == spec["entity_id"]:
            return source_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.native_value is None


def test_climate_target_native_value_none_when_temperature_attr_missing(mock_coordinator, mock_config_entry, mock_hass):
    """ClimateTarget returns None when the `temperature` attribute is absent."""
    spec = EXPECTED_SENSOR_SURFACE["climate_target"]
    sensor = _make_sensor(spec, mock_coordinator, mock_config_entry, mock_hass)

    source_state = MagicMock()
    source_state.state = "heat"
    source_state.attributes = {}  # no temperature attr

    def mock_get(entity_id):
        if entity_id == spec["entity_id"]:
            return source_state
        return None

    mock_hass.states.get = mock_get

    assert sensor.native_value is None
