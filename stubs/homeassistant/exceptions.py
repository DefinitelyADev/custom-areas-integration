"""Home Assistant exceptions stubs."""

class HomeAssistantError(Exception):
    """Base Home Assistant exception."""
    ...

class ConfigEntryNotReady(HomeAssistantError):
    """Exception raised when a config entry is not ready."""
    ...
