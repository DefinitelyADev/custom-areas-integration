"""Tests for the Custom Areas config flow.

These tests exercise the real Home Assistant config-entries machinery via the
`hass` fixture provided by ``pytest-homeassistant-custom-component``, rather
than ``MagicMock``. This is intentional: the unit tests in ``test_sensor.py``
cover sensor behaviour at the property level, while these tests prove the
config flow actually integrates with HA's flow manager (set_unique_id,
abort-on-duplicate, schema validation).
"""

import pytest
import voluptuous as vol
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.custom_areas.const import (
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
    DEFAULT_ICON,
    DOMAIN,
)


async def test_user_flow_happy_path(hass: HomeAssistant) -> None:
    """Submitting a valid form creates a ConfigEntry with the expected title and data."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    user_input = {
        CONF_AREA_NAME: "Living Room",
        CONF_POWER_ENTITY: "sensor.lr_power",
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room"
    assert result["data"][CONF_AREA_NAME] == "Living Room"
    assert result["data"][CONF_POWER_ENTITY] == "sensor.lr_power"


async def test_user_flow_duplicate_area_name_aborts(hass: HomeAssistant) -> None:
    """A second submission with the same area_name aborts as already_configured."""
    # First entry — success.
    first = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    first = await hass.config_entries.flow.async_configure(
        first["flow_id"],
        {CONF_AREA_NAME: "Living Room", CONF_POWER_ENTITY: "sensor.lr_power"},
    )
    assert first["type"] == FlowResultType.CREATE_ENTRY

    # Second entry with the same area_name — abort.
    second = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    second = await hass.config_entries.flow.async_configure(
        second["flow_id"],
        {CONF_AREA_NAME: "Living Room", CONF_POWER_ENTITY: "sensor.other_power"},
    )
    assert second["type"] == FlowResultType.ABORT
    assert second["reason"] == "already_configured"


async def test_user_flow_optional_fields_omitted(hass: HomeAssistant) -> None:
    """Only area_name supplied — entry is created and optional refs are absent from data."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_AREA_NAME: "Bedroom"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bedroom"

    data = result["data"]
    assert data[CONF_AREA_NAME] == "Bedroom"

    # Optional entity references should not be present when omitted.
    for key in (
        CONF_POWER_ENTITY,
        CONF_ENERGY_ENTITY,
        CONF_TEMP_ENTITY,
        CONF_HUMIDITY_ENTITY,
        CONF_MOTION_ENTITY,
        CONF_WINDOW_ENTITY,
        CONF_CLIMATE_ENTITY,
        CONF_ACTIVE_THRESHOLD,
    ):
        assert key not in data, f"Unexpected optional key {key!r} in entry.data"


async def test_user_flow_icon_default_applied(hass: HomeAssistant) -> None:
    """When icon is omitted, the flow defaults it to DEFAULT_ICON (mdi:texture-box).

    See ``config_flow.py:49-50`` — the icon default is applied at config time
    so the value is persisted in ``entry.data``.
    """
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_AREA_NAME: "Kitchen"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ICON] == DEFAULT_ICON
    assert DEFAULT_ICON == "mdi:texture-box"


async def test_user_flow_negative_threshold_rejected(hass: HomeAssistant) -> None:
    """active_threshold=-5 is rejected by the voluptuous schema (vol.Range(min=0))."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    # The schema in async_step_user validates input before async_configure
    # returns; an invalid value raises MultipleInvalid up through the flow.
    with pytest.raises(vol.Invalid):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_AREA_NAME: "Garage", CONF_ACTIVE_THRESHOLD: -5},
        )
