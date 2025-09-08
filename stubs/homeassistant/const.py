# Type stubs for homeassistant.const
from typing import Final

# Common constants used in HA
STATE_ON: Final[str] = "on"
STATE_OFF: Final[str] = "off"
PERCENTAGE: Final[str] = "%"

# Temperature units
TEMP_CELSIUS: Final[str] = "°C"
TEMP_FAHRENHEIT: Final[str] = "°F"

# Power units
POWER_WATT: Final[str] = "W"

# Energy units
ENERGY_WATT_HOUR: Final[str] = "Wh"
ENERGY_KILO_WATT_HOUR: Final[str] = "kWh"

__all__ = [
    "STATE_ON",
    "STATE_OFF",
    "PERCENTAGE",
    "TEMP_CELSIUS",
    "TEMP_FAHRENHEIT",
    "POWER_WATT",
    "ENERGY_WATT_HOUR",
    "ENERGY_KILO_WATT_HOUR",
]
