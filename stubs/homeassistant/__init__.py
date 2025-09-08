# Type stubs for Home Assistant modules
# This provides basic type information for Pylance/Pyright

from typing import Any

from . import config_entries

__all__ = ["config_entries"]
    async def async_forward_entry_setups(self, entry: ConfigEntry, platforms: Any) -> None: ...
    async def async_unload_platforms(self, entry: ConfigEntry, platforms: Any) -> bool: ...

# Export the classes
__all__ = ["ConfigEntry", "ConfigFlow", "ConfigEntriesFlowManager"]
