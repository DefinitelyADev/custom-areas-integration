# Type stubs for homeassistant.components.sensor
from typing import Any, Dict, Optional
from ...core import HomeAssistant
from ...helpers.entity import DeviceInfo

class SensorEntity:
    """Basic SensorEntity stub."""

    hass: HomeAssistant
    _attr_name: Optional[str]
    _attr_unique_id: Optional[str]
    _attr_should_poll: bool
    _attr_device_info: Optional[DeviceInfo]

    def __init__(self) -> None: ...

    @property
    def name(self) -> Optional[str]: ...
    @property
    def unique_id(self) -> Optional[str]: ...
    @property
    def should_poll(self) -> bool: ...
    @property
    def device_info(self) -> Optional[DeviceInfo]: ...

    @property
    def state(self) -> Any: ...
    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]: ...
    @property
    def icon(self) -> Optional[str]: ...

    async def async_schedule_update_ha_state(self, force_refresh: bool = False) -> None: ...

__all__ = ["SensorEntity"]
