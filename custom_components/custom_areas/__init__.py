"""Custom Areas Integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import CONF_AREA_NAME, DOMAIN
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
            name=f"Area: {entry.data.get(CONF_AREA_NAME, 'Unknown')}",
            manufacturer="Areas Integration",
            model="Area Sensor",
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.add_update_listener(async_reload_entry)

        return True

    except Exception as ex:
        # HA itself logs ConfigEntryNotReady with context and retries setup
        # on a backoff. Emit one structured warning (exc_info=ex includes the
        # traceback) and let HA handle the retry messaging. Use `warning`
        # rather than `error` since setup retries are routine on restart.
        _LOGGER.warning("Setup failed for %s: %s", entry.title, ex, exc_info=ex)
        raise ConfigEntryNotReady from ex


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading areas integration for %s", entry.title)

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.shutdown()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
