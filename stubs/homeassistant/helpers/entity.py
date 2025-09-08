"""Home Assistant entity helpers stubs."""

from typing import Any, Dict, Optional, Union

class DeviceInfo:
    """Device information for entities."""

    def __init__(
        self,
        *,
        identifiers: Optional[Any] = None,
        connections: Optional[Any] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        name: Optional[str] = None,
        sw_version: Optional[str] = None,
        via_device: Optional[Any] = None,
        configuration_url: Optional[str] = None,
        entry_type: Optional[str] = None,
        hw_version: Optional[str] = None,
        serial_number: Optional[str] = None,
    ) -> None:
        """Initialize device info."""
        ...

class Entity:
    """Base entity class."""

    entity_id: str
    name: Optional[str]
    state: Any
    device_info: Optional[Union[DeviceInfo, Dict[str, Any]]]
    unique_id: Optional[str]
    should_poll: bool
    available: bool

    def __init__(self) -> None:
        """Initialize the entity."""
        ...

    async def async_update_ha_state(self, force_refresh: bool = False) -> None:
        """Update Home Assistant with current state of entity."""
        ...

    def schedule_update_ha_state(self, force_refresh: bool = False) -> None:
        """Schedule an update ha state change task."""
        ...
