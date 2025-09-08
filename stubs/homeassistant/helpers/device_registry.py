"""Home Assistant device registry helpers stubs."""

from typing import Any, Optional

from ..core import HomeAssistant


def async_get(hass: HomeAssistant) -> "DeviceRegistry":
    """Get the device registry."""
    ...


class DeviceRegistry:
    """Device registry for managing devices."""

    async def async_get_device(self, identifiers: Any) -> Optional[Any]:
        """Get device by identifiers."""
        ...

    def async_get_or_create(
        self,
        *,
        config_entry_id: str,
        identifiers: Any,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        name: Optional[str] = None,
        sw_version: Optional[str] = None,
        hw_version: Optional[str] = None,
        via_device: Optional[Any] = None,
        connections: Optional[Any] = None,
    ) -> Any:
        """Get or create a device."""
        ...
