# Type stubs for homeassistant.core
from typing import Any, Dict, Optional, Protocol, Callable, Awaitable
from datetime import datetime

class Event:
    """Basic Event stub."""
    event_type: str
    data: Dict[str, Any]
    time_fired: Optional[datetime]
    context: Any

class State:
    """Basic State stub."""
    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: datetime
    last_updated: datetime
    context: Any

class HomeAssistant:
    """Basic HomeAssistant stub."""
    data: Dict[str, Any]
    states: Any  # State machine
    config_entries: Any  # ConfigEntriesFlowManager
    loop: Any  # Event loop

    def __init__(self) -> None: ...

    def async_create_task(self, coro: Awaitable[Any]) -> Any:
        """Create a task from a coroutine."""
        ...

class callback:
    """Decorator for callback functions."""
    def __init__(self, func: Callable) -> None: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

__all__ = ["Event", "State", "HomeAssistant", "callback"]
