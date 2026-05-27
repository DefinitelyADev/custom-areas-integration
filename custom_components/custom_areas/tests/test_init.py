"""Tests for the Custom Areas integration lifecycle (`__init__.py`).

Exercises ``async_setup_entry``, ``async_unload_entry``, and
``async_reload_entry`` against the real Home Assistant fixture so the
deliberate ``ConfigEntryNotReady`` re-raise, the coordinator/device-registry
side effects, and the unload teardown all behave as documented.
"""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.custom_areas.const import CONF_AREA_NAME, CONF_MOTION_ENTITY, CONF_POWER_ENTITY, DOMAIN


def _make_entry(area_name: str = "Living Room") -> MockConfigEntry:
    """Build a MockConfigEntry with a stable shape used across these tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=area_name,
        data={
            CONF_AREA_NAME: area_name,
            CONF_POWER_ENTITY: "sensor.lr_power",
            CONF_MOTION_ENTITY: "binary_sensor.lr_motion",
        },
        unique_id=area_name,
    )


async def test_async_setup_entry_happy_path(hass: HomeAssistant, enable_custom_integrations) -> None:
    """A valid entry sets up, stores the coordinator, and creates a device."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()

    # Coordinator is stored in hass.data under the integration domain.
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator is not None

    # Device registry has an entry for this config entry.
    device_reg = dr.async_get(hass)
    device = device_reg.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert device is not None
    assert device.name == "Area: Living Room"
    assert device.manufacturer == "Areas Integration"


async def test_async_setup_entry_reraises_as_config_entry_not_ready(hass: HomeAssistant, enable_custom_integrations) -> None:
    """When the coordinator's first refresh raises, setup must re-raise ConfigEntryNotReady.

    ``__init__.py`` deliberately catches the broad ``Exception``, logs, and
    re-raises as ``ConfigEntryNotReady`` so HA can retry setup on a backoff.
    AGENTS.md / CLAUDE.md both call this out as load-bearing.
    """
    entry = _make_entry("Bedroom")
    entry.add_to_hass(hass)

    target = "custom_components.custom_areas.sensor.AreaSensorCoordinator.async_config_entry_first_refresh"
    with patch(target, side_effect=RuntimeError("boom")):
        # `async_setup` swallows ConfigEntryNotReady internally; call the
        # module's async_setup_entry directly so the re-raise is visible.
        from custom_components.custom_areas import async_setup_entry

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_async_unload_entry_clears_data_and_shuts_down(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Unload removes the coordinator from hass.data and calls shutdown."""
    entry = _make_entry("Kitchen")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    # Spy on the shutdown method without changing its behaviour.
    with patch.object(coordinator, "shutdown", wraps=coordinator.shutdown) as shutdown_spy:
        assert await hass.config_entries.async_unload(entry.entry_id) is True
        await hass.async_block_till_done()

    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    assert shutdown_spy.call_count == 1


async def test_async_reload_entry_replaces_coordinator(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Reloading the entry unloads then re-sets-up, producing a fresh coordinator."""
    entry = _make_entry("Office")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()

    original = hass.data[DOMAIN][entry.entry_id]
    original_id = id(original)

    assert await hass.config_entries.async_reload(entry.entry_id) is True
    await hass.async_block_till_done()

    refreshed = hass.data[DOMAIN][entry.entry_id]
    assert id(refreshed) != original_id
