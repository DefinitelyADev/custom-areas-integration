# Developer Documentation

## Architecture Overview

The Custom Areas Integration follows Home Assistant's standard custom integration architecture.

### Core Files

```
custom_components/custom_areas/
├── __init__.py          # async_setup_entry / unload / reload, device registration
├── config_flow.py       # UI configuration flow (AreasConfigFlow)
├── sensor.py            # Coordinator + sensor entity implementations
├── const.py             # CONF_* keys, defaults, and shared constants
├── manifest.json        # Integration metadata
├── strings.json         # UI strings for config flow
└── translations/
    └── en.json          # English translations
```

### Key Classes

#### `AreaSensorCoordinator`
- **Purpose**: Owns the state-change listeners for the area's configured source entities
  and fans out updates to every sensor registered against it.
- **Responsibilities**:
  - Subscribes to source-entity state changes via `async_track_state_change_event`.
  - Keeps an internal list of registered sensors and schedules a Home Assistant state
    update on each of them when any source entity changes.
  - Manages listener cleanup at shutdown.

#### `AreaSummarySensor`
- **Purpose**: Composite sensor entity representing the area's aggregate state.
- **Responsibilities**:
  - Computes `native_value` (state), `icon`, and `extra_state_attributes` on demand by
    reading the configured source entities at access time — no internal cached state.
  - Honors the documented state priority (motion > power threshold > entity presence)
    and icon priority (window > motion > configured/default).
  - Ships every numeric attribute in two forms: a typed numeric (`power_w`, etc.) and a
    stringified-with-unit form (`power: "28.6 W"`).

#### Measurement sensors
- One passthrough sensor per configured measurement source (power, energy, temperature,
  humidity, climate target). Each mirrors the source entity's `state.state` (or, for
  climate target, the `state.attributes["temperature"]`), with the unit forwarded from
  the source entity when available and a sensible default otherwise. They share the
  same device registry entry as the summary sensor.

## Code Flow

### Setup Process
1. `async_setup_entry()` registers the device in Home Assistant's device registry.
2. `AreaSensorCoordinator` is created and subscribes to state-change events on each
   configured source entity.
3. The summary sensor and each enabled measurement sensor are instantiated and
   `register_sensor()`ed with the coordinator.
4. Entities are added to Home Assistant via `async_add_entities`.

### State Update Process
1. A tracked source entity emits a state-change event.
2. The coordinator's listener fires; it schedules a Home Assistant state update on
   every registered sensor.
3. When Home Assistant reads each sensor's properties, the sensor recomputes its state
   and attributes lazily from the current state of the configured source entities.

## Development Setup

### Prerequisites
- Python 3.13+
- Home Assistant development environment
- Git

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/DefinitelyADev/room-entity.git
   cd room-entity
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run validation**:
   ```bash
   python validate.py
   ```

5. **Run tests**:
   ```bash
   python run_tests.py
   ```

6. **Full local gate**:
   ```bash
   python check_all.py   # validate + tests + pyright + black + isort + flake8 + pre-commit
   ```

### Testing

Tests live inside the integration package at
`custom_components/custom_areas/tests/`. The project uses a hybrid approach:

- **Unit tests** use `MagicMock(spec=HomeAssistant)` for fast, isolated coverage of
  sensor and coordinator logic.
- **Integration tests** use the real `hass` fixture from
  `pytest-homeassistant-custom-component` to exercise the integration end-to-end against
  the actual Home Assistant state machine.

Run tests with:
```bash
python -m pytest custom_components/custom_areas/tests/
```

### Code Quality

The project uses several tools — all enforced via pre-commit and CI:

- **black** — code formatter (line length **120**, not 88)
- **isort** — import sorter (profile=black)
- **flake8** — linter
- **ruff** — linter (additional checks)
- **mypy** — type checker
- **pyright** — type checker (basic mode)

Run all quality checks:
```bash
python check_all.py
```

## Configuration Flow

### Flow Steps
1. **User Step** (`async_step_user`): Collects all configuration fields in a single
   form. Schema validation is handled by voluptuous; entity pickers are filtered by
   domain via `EntitySelector`.
2. **Validation**: Ensures the area name is unique across existing entries via
   `async_set_unique_id` + `_abort_if_unique_id_configured`. The `icon` field is
   defaulted to `mdi:texture-box` when not provided.
3. **Entry Creation**: Creates the config entry with the user's data.

> **Options flow**: planned. Changing settings on an existing area today requires
> deleting and recreating the entry.

### Entity Selection
The config flow uses Home Assistant's `EntitySelector` for each entity type:
- Sensors (power, energy, temperature, humidity): `sensor` domain
- Binary sensors (motion, window): `binary_sensor` domain
- Climate: `climate` domain

### Validation Rules
- Area name must be unique across all area configurations.
- Active threshold must be a non-negative number.

## State Management

### Event-Driven Updates
The integration uses Home Assistant's event system for real-time updates:
- No polling — instant response to state changes
- Efficient resource usage
- Reliable state synchronization via `async_track_state_change_event`

### State Calculation Logic
```python
def determine_area_state(self) -> str:
    # Priority: Motion > Power Threshold > Entity Presence > Unknown
    if motion_detected:
        return STATE_ACTIVE
    if power_above_threshold:
        return STATE_ACTIVE
    if has_entities:
        return STATE_IDLE
    return STATE_UNKNOWN
```

### Attribute Collection
Attributes are collected with error handling:
- Numeric values use `get_numeric_state()` with fallbacks
- Boolean values use direct state comparison
- Climate attributes include both `climate_mode` (string) and `climate_target_c` / `climate_target` (numeric + stringified form)

## Error Handling

### Setup Failures
- `__init__.py` deliberately re-raises setup errors as `ConfigEntryNotReady` so that
  Home Assistant retries setup on its standard backoff. Preserve this pattern.

### State Conversion
- Invalid numeric states log debug messages and are skipped (the attribute is omitted
  rather than set to a bad value).
- Missing entities are gracefully handled.
- Type conversion errors are caught and logged.

### Listener Management
- Listeners are properly cleaned up on shutdown by the coordinator.
- The coordinator manages listener lifecycle to prevent memory leaks and duplicate
  listeners.

## Performance Considerations

### Event Filtering
- Only tracks configured entities — uses specific entity IDs rather than wildcards.
- Minimizes event processing overhead.

### Memory Management
- The coordinator cleans up its listeners on shutdown.
- No persistent state storage beyond the config entry.
- Lightweight entity implementation: sensors compute lazily on property access.

## Future Enhancements

For the latest planned work, see the [CHANGELOG](../CHANGELOG.md) and the project's
issue tracker.
