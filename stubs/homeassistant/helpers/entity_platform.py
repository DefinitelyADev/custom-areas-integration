"""Home Assistant entity platform helpers stubs."""

from typing import Any, Awaitable, Callable, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

AddEntitiesCallback = Callable[[List[Any]], Awaitable[None]]


class EntityPlatform:
    """Entity platform for managing entities."""

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        logger: Any,
        domain: str,
        platform_name: str,
        platform: Any,
        scan_interval: Any,
        entity_namespace: Optional[str],
    ) -> None:
        """Initialize entity platform."""
        ...

    async def async_add_entities(
        self,
        new_entities: List[Any],
        update_before_add: bool = False,
    ) -> None:
        """Add entities to the platform."""
        ...
