"""Constants for the Rooms integration."""

DOMAIN = "rooms"
CONF_ROOM_NAME = "room_name"
CONF_POWER_ENTITY = "power_entity"
CONF_ENERGY_ENTITY = "energy_entity"
CONF_TEMP_ENTITY = "temp_entity"
CONF_HUMIDITY_ENTITY = "humidity_entity"
CONF_MOTION_ENTITY = "motion_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_ACTIVE_THRESHOLD = "active_threshold"

# Default values
DEFAULT_ACTIVE_THRESHOLD = 50.0

# State values
STATE_ACTIVE = "active"
STATE_IDLE = "idle"
STATE_UNKNOWN = "unknown"

# Icons
ICON_HOME = "mdi:home"
ICON_MOTION = "mdi:motion-sensor"
ICON_WINDOW_OPEN = "mdi:window-open-variant"
