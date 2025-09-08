"""Home Assistant event helpers stubs."""

from typing import Any, Awaitable, Callable, Optional

from homeassistant.core import Event, HomeAssistant


async def async_track_state_change_event(
    hass: HomeAssistant,
    entity_ids: Any,
    action: Callable[[Event], Awaitable[None]],
) -> Callable[[], None]:
    """Track state change events for entities."""
    ...
