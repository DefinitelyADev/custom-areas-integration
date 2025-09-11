"""Custom Areas Integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .sensor import AreaSensorCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up areas from a config entry."""
    _LOGGER.info("Setting up areas integration for %s", entry.title)

    try:
        coordinator = AreaSensorCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Create device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Area: {entry.data.get('area_name', 'Unknown')}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.add_update_listener(async_reload_entry)

        return True

    except Exception as ex:
        _LOGGER.error("Error setting up areas integration: %s", ex)
        _LOGGER.error("Exception type: %s", type(ex).__name__)
        import traceback

        _LOGGER.error("Full traceback: %s", traceback.format_exc())
        raise ConfigEntryNotReady from ex


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading areas integration for %s", entry.title)

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.async_shutdown()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
