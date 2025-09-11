# Developer Documentation

## Architecture Overview

The Custom Areas Integration follows Home Assistant's standard custom integration architecture with the following components:

### Core Files

```
custom_components/custom_areas/
├── __init__.py          # Integration setup and lifecycle
├── config_flow.py       # UI configuration flow
├── sensor.py           # Sensor entity implementation
├── const.py            # Constants and configuration keys
├── manifest.json       # Integration metadata
├── strings.json        # UI strings for config flow
└── translations/
    └── en.json         # English translations
```

### Key Classes

#### `RoomSensorCoordinator`
- **Purpose**: Coordinates state updates between entities
- **Responsibilities**:
  - Sets up event listeners for all configured entities
  - Handles state change events
  - Manages cleanup of listeners
  - Registers the summary sensor for updates

#### `RoomSummarySensor`
- **Purpose**: Main sensor entity that represents room state
- **Responsibilities**:
  - Calculates room state based on entity conditions
  - Provides state attributes with sensor data
  - Determines appropriate icon based on room status
  - Handles device registry integration

## Code Flow

### Setup Process
1. `async_setup_entry()` creates coordinator and sensor entities
2. Coordinator sets up state change listeners for all configured entities
3. Sensor registers itself with the coordinator
4. Entities are added to Home Assistant

### State Update Process
1. Entity state change triggers event
2. Coordinator receives event and schedules sensor update
3. Sensor recalculates state and attributes
4. Home Assistant updates the entity state

## Development Setup

### Prerequisites
- Python 3.10+
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

4. **Run tests**:
   ```bash
   python run_tests.py
   ```

5. **Run validation**:
   ```bash
   python validate.py
   ```

### Testing

The project includes comprehensive tests covering:

- **Unit Tests**: Core functionality and state logic
- **Config Flow Tests**: UI configuration validation
- **Integration Tests**: End-to-end functionality

Run tests with:
```bash
python -m pytest custom_components/custom_areas/tests/
```

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pyright**: Type checking

Run all quality checks:
```bash
python check_all.py
```

## Configuration Flow

### Flow Steps
1. **User Step**: Collects all configuration data in a single form
2. **Validation**: Ensures room name uniqueness
3. **Entry Creation**: Creates config entry with user data

### Entity Selection
The config flow uses Home Assistant's `EntitySelector` for each entity type:
- Sensors: `sensor` domain
- Binary sensors: `binary_sensor` domain
- Climate: `climate` domain

### Validation Rules
- Room name must be unique across all room configurations
- All selected entities must exist in Home Assistant
- Active threshold must be a non-negative number

## State Management

### Event-Driven Updates
The integration uses Home Assistant's event system for real-time updates:
- No polling - instant response to state changes
- Efficient resource usage
- Reliable state synchronization

### State Calculation Logic
```python
def determine_room_state(self) -> str:
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
- Numeric values use `_get_numeric_state()` with fallbacks
- Boolean values use direct state comparison
- Climate attributes include both mode and target temperature

## Error Handling

### State Conversion
- Invalid numeric states log debug messages and use defaults
- Missing entities are gracefully handled
- Type conversion errors are caught and logged

### Listener Management
- Listeners are properly cleaned up on shutdown
- Coordinator manages listener lifecycle
- Prevents memory leaks and duplicate listeners

## Performance Considerations

### Caching
- State lookups are cached within attribute calculation
- Reduces redundant state access
- Improves performance with multiple attributes

### Event Filtering
- Only tracks configured entities
- Uses specific entity IDs rather than wildcards
- Minimizes event processing overhead

### Memory Management
- Coordinator properly cleans up listeners
- No persistent state storage beyond config entries
- Lightweight entity implementation

## Future Enhancements

### Potential Features
- Multiple room types with different logic
- Room groups and hierarchies
- Historical state tracking
- Automation integration
- Energy monitoring dashboards

### Architecture Improvements
- Async state calculation
- Configurable state priorities
- Plugin system for custom logic
- Enhanced error reporting
