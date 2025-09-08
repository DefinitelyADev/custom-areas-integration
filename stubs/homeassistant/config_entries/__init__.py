# Type stubs for homeassistant.config_entries
from typing import Any, Awaitable, Callable, Dict, Optional

from ..core import HomeAssistant
from ..data_entry_flow import FlowResult


class ConfigEntry:
    """Configuration entry for Home Assistant integrations."""

    entry_id: str
    title: str
    domain: str
    data: Dict[str, Any]
    options: Dict[str, Any]
    unique_id: Optional[str]
    version: int

    def __init__(
        self,
        *,
        entry_id: str,
        title: str,
        domain: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        unique_id: Optional[str] = None,
        version: int = 1,
    ) -> None:
        """Initialize config entry."""
        ...

    async def async_on_unload(
        self, func: Optional[Callable[[], Awaitable[None]]]
    ) -> None:
        """Register a callback to be called when the entry is unloaded."""
        ...

    def add_update_listener(self, listener: Callable[..., Awaitable[None]]) -> None:
        """Add an update listener."""
        ...


class ConfigFlow:
    """Base class for config flows."""

    hass: HomeAssistant
    context: Dict[str, Any]

    def __init__(self) -> None:
        """Initialize config flow."""
        ...

    def __init_subclass__(cls, domain: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize subclass with domain."""
        ...

    async def async_set_unique_id(self, unique_id: str) -> None:
        """Set unique ID for the config flow."""
        ...

    def _abort_if_unique_id_configured(
        self, updates: Optional[Dict[str, Any]] = None
    ) -> Optional[FlowResult]:
        """Abort if unique ID is already configured."""
        ...

    async def async_create_entry(
        self,
        title: str,
        data: Dict[str, Any],
        description: Optional[str] = None,
        description_placeholders: Optional[Dict[str, str]] = None,
    ) -> FlowResult:
        """Create a config entry."""
        ...

    async def async_show_form(
        self,
        step_id: str,
        data_schema: Optional[Any] = None,
        errors: Optional[Dict[str, str]] = None,
        description_placeholders: Optional[Dict[str, str]] = None,
    ) -> FlowResult:
        """Show form for the current step."""
        ...


class ConfigEntriesFlowManager:
    """Manager for config entries flow."""

    async def async_forward_entry_setups(
        self, entry: ConfigEntry, platforms: Any
    ) -> None:
        ...

    async def async_unload_platforms(self, entry: ConfigEntry, platforms: Any) -> bool:
        ...


# Re-export for convenience
__all__ = ["ConfigEntry", "ConfigFlow", "ConfigEntriesFlowManager"]
