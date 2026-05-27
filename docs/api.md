# API Documentation

## Overview

Each configured area produces a **summary sensor** plus zero to five **measurement sensors**,
depending on which source entities you configure. All entity IDs start with
`custom_area_<area_name>` (the area name is slugified by Home Assistant — spaces become
underscores, etc.).

| Sensor | Entity ID pattern | Created when |
|---|---|---|
| Summary | `sensor.custom_area_<area_name>` | Always |
| Power | `sensor.custom_area_<area_name>_power` | `power_entity` configured |
| Energy | `sensor.custom_area_<area_name>_energy` | `energy_entity` configured |
| Temperature | `sensor.custom_area_<area_name>_temperature` | `temp_entity` configured |
| Humidity | `sensor.custom_area_<area_name>_humidity` | `humidity_entity` configured |
| Climate target | `sensor.custom_area_<area_name>_climate_target` | `climate_entity` configured |

## Summary Sensor (`sensor.custom_area_<area_name>`)

The summary sensor aggregates all configured source entities into a single composite
entity for dashboards and automations. Its state, attributes, and icon are all derived
from the underlying source entities at access time — there is no internal cached state.

### States

| State | Description |
|-------|-------------|
| `active` | Area is currently active (motion detected OR power above threshold) |
| `idle` | Area has configured entities but is not active |
| `unknown` | No entities configured for the area |

### Attributes

Numeric attributes ship in **two forms**: a typed numeric attribute (e.g. `power_w`)
useful for automations and templates, and a stringified-with-unit attribute (e.g.
`power: "28.6 W"`) useful for direct display in cards. Both are always emitted together
when the corresponding source entity is configured and has a valid numeric state.

| Attribute | Type | Description |
|-----------|------|-------------|
| `power_w` | float | Current power consumption (numeric) |
| `power` | string | Power, formatted with unit (e.g., `28.6 W`) |
| `energy_wh` | float | Current energy (numeric) |
| `energy` | string | Energy, formatted with unit (e.g., `12.3 Wh`) |
| `temperature_c` | float | Current temperature (numeric) |
| `temperature` | string | Temperature, formatted with unit (e.g., `21.5 °C`) |
| `humidity_pct` | float | Current humidity percentage (numeric) |
| `humidity` | string | Humidity, formatted with unit (e.g., `45 %`) |
| `climate_target_c` | float | Target temperature (numeric) |
| `climate_target` | string | Target temperature, formatted with unit (e.g., `21 °C`) |
| `occupied` | boolean | Motion detection status |
| `window_open` | boolean | Window/door status |
| `climate_mode` | string | Current climate mode (from the climate entity's state) |

### State Priority

The summary sensor's state follows this order (first match wins):

1. **Motion ON** → `active`
2. **Power > `active_threshold`** → `active`
3. **Any core entity configured** → `idle`
4. **Else** → `unknown`

### Icon Priority

The icon also follows a strict priority order:

1. **Window open** → `mdi:window-open-variant`
2. **Motion detected** → `mdi:motion-sensor`
3. **Configured `icon` (or default `mdi:texture-box`)**

## Measurement Sensors

One measurement sensor is created per configured measurement source entity. Each
measurement sensor is a **passthrough** — its `native_value` mirrors the source
entity's state (or, for `climate_target`, the source entity's `temperature` attribute).
The unit of measurement is taken from the source entity when available, otherwise it
falls back to the listed default.

| Sensor | Source attribute | Default unit |
|---|---|---|
| Power | `state.state` of `power_entity` | `W` |
| Energy | `state.state` of `energy_entity` | `Wh` |
| Temperature | `state.state` of `temp_entity` | `°C` |
| Humidity | `state.state` of `humidity_entity` | `%` |
| Climate target | `state.attributes["temperature"]` of `climate_entity` | `°C` |

Measurement sensors expose no additional attributes — they are intentionally minimal
so that Home Assistant's built-in formatting, statistics, and long-term history can
treat them as first-class numeric sensors.

## Device Registry

Each area creates a single device in Home Assistant's device registry. All sensors for
the area (summary + measurements) are attached to the same device.

### Device Properties
- **Name**: `Area: <area_name>`
- **Manufacturer**: `Areas Integration`
- **Model**: `Area Sensor`
- **Identifiers**: `{(custom_areas, config_entry.entry_id)}`

## Events

The integration listens for state change events on all configured source entities and
updates every sensor for the area immediately — no polling. When any tracked source
entity changes state, the coordinator schedules an update for every registered sensor;
each sensor then recomputes its state and attributes lazily on the next property access.

### Tracked Events
- State changes on power sensors
- State changes on energy sensors
- State changes on temperature sensors
- State changes on humidity sensors
- State changes on motion sensors
- State changes on window/door sensors
- State changes on climate entities

## Configuration Schema

### Required Fields
- `area_name` (string) — Display name for the area; also drives the entity_id suffix.

### Optional Fields
- `power_entity` (entity ID, sensor domain) — Power consumption sensor (W).
- `energy_entity` (entity ID, sensor domain) — Energy consumption sensor (Wh).
- `temp_entity` (entity ID, sensor domain) — Temperature sensor (°C).
- `humidity_entity` (entity ID, sensor domain) — Humidity sensor (%).
- `motion_entity` (entity ID, binary_sensor domain) — Motion detection sensor.
- `window_entity` (entity ID, binary_sensor domain) — Window/door sensor.
- `climate_entity` (entity ID, climate domain) — Climate control entity.
- `active_threshold` (float, watts) — Power threshold for the `active` state. Default: `50.0`.
- `icon` (mdi icon string) — Fallback icon when neither window nor motion drives the icon. Default: `mdi:texture-box`.

## State Logic

The area state follows this priority order:

1. **Motion Detection**: If motion sensor is ON → `active`
2. **Power Threshold**: If power consumption > active threshold → `active`
3. **Entity Presence**: If any core entities exist but conditions 1-2 are false → `idle`
4. **No Entities**: If no entities configured → `unknown`

## Icon Logic

The summary sensor icon changes based on area status:

1. **Window Open**: If window sensor is ON → `mdi:window-open-variant`
2. **Motion Detected**: If motion sensor is ON → `mdi:motion-sensor`
3. **Default**: `mdi:texture-box`
