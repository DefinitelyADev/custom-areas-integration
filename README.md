# Rooms Integration for Home Assistant

A custom integration for Home Assistant that creates composite "Room" sensors with UI configuration.

## Features

- **UI Configuration**: Add rooms through Home Assistant's UI with an intuitive config flow
- **Composite Sensors**: Each room creates a summary sensor that combines multiple entity states
- **Real-time Updates**: Uses event-driven updates instead of polling for instant state changes
- **Device Registry**: Creates proper devices in Home Assistant's device registry

## Documentation

📖 **Complete Documentation**: [docs/](docs/)

- **[API Reference](docs/api.md)** - Entity states, attributes, and configuration schema
- **[Configuration Examples](docs/examples.md)** - Real-world setup examples and use cases
- **[Developer Guide](docs/developer.md)** - Architecture overview and development setup
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

## Disclaimer (The Vibe Clause)

This project is proudly *vibe coded*. It was started because it felt like a good idea at the time, and it will continue evolving based on equal parts usefulness, curiosity, and whatever soundtrack is playing. That means:

- Some abstractions may appear only after their third sibling arrives
- Refactors can materialize suddenly (like motion-triggered automation)
- Tests occasionally chase features (they do catch up)
- Naming conventions are consistent... with the mood of the day

If you demand immaculate enterprise architecture, you are lovingly invited to open a PR. If you enjoy useful sensors, good intentions, and iterative polish: welcome. It works, it's helpful, and it will continue to vibe forward. 🚀

Not affiliated with Home Assistant — just vibing on top of it.

## Installation

### HACS Installation (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots (⋮) in the top right
   - Select "Custom repositories"
   - Add: `https://github.com/DefinitelyADev/room-entity`
   - Category: Integration
3. Search for "Rooms" in HACS and install it
4. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/rooms/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

## Configuration

### Adding a Room

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Rooms" and select it
3. Configure your room:
   - **Room Name**: Display name for the room
   - **Power Sensor**: Optional sensor for power consumption
   - **Energy Sensor**: Optional sensor for energy consumption
   - **Temperature Sensor**: Optional temperature sensor
   - **Humidity Sensor**: Optional humidity sensor
   - **Motion Sensor**: Optional motion detection sensor
   - **Window Sensor**: Optional window/door sensor
   - **Climate Entity**: Optional climate control entity
   - **Active Power Threshold**: Power level (in watts) above which the room is considered "active"

## Usage

### Summary Sensor

Each room creates a summary sensor with these states:
- **active**: Room is currently active (motion detected OR power above threshold)
- **idle**: Room has configured entities but is not active
- **unknown**: No entities configured for the room

The summary sensor includes these attributes:
- `power_w` (numeric) and `power` (string with unit, e.g. "28.6 W")
- `energy_wh` (numeric) and `energy` (string with unit, e.g. "12.3 Wh")
- `temperature_c` (numeric) and `temperature` (string with unit, e.g. "21.5 °C")
- `humidity_pct` (numeric) and `humidity` (string with unit, e.g. "45 %")
- `occupied`: Motion detection status
- `window_open`: Window/door status
- `climate_mode`: Current climate mode
   - `climate_target_c` (numeric) and `climate_target` (string with unit)

## State Logic

The room state is determined by this priority:
1. If motion sensor is ON → **active**
2. If power consumption > active threshold → **active**
3. If any core entities exist but conditions 1-2 are false → **idle**
4. If no entities configured → **unknown**

## Icons

The summary sensor icon changes based on room status:
- Window open: `mdi:window-open-variant`
- Motion detected: `mdi:motion-sensor`
- Default: `mdi:home`

## Device Registry

Each room creates a device in Home Assistant's device registry, allowing you to:
- Group all room sensors together
- View device information
- Manage device settings

## Requirements

- Home Assistant 2024.1.0 or later
- Python 3.10 or later
- Entities must exist before configuring the room

## Troubleshooting

### Common Issues

1. **"Entity not found" error**: Ensure all selected entities exist and are available
2. **Sensor not updating**: Check that source entities are publishing state changes

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.rooms: debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

### Automated Checks

- **Tests**: Run on Python 3.10, 3.11, and 3.12
- **Validation**: Custom validation of manifest, translations, and structure
- **Type Checking**: Pyright type checking
- **Linting**: Black formatting, isort import sorting, and flake8 linting
- **HACS Validation**: Ensures compatibility with HACS
- **Pre-commit**: Code quality checks on pull requests

### Workflows

- `ci.yml`: Main CI pipeline triggered on push/PR
- `pre-commit.yml`: Code quality checks
- `manual-validation.yml`: Manual validation triggers

### Local Development

Run all checks locally:

```bash
pip install -r requirements-dev.txt
python check_all.py
```

Or run individual checks:

```bash
python validate.py          # Custom validation
python run_tests.py         # Unit tests
pyright                    # Type checking
black --check custom_components/rooms/    # Code formatting
isort --check-only custom_components/rooms/  # Import sorting
flake8 custom_components/rooms/           # Linting
```

### Pre-commit Setup

Install pre-commit hooks for automatic code quality:

```bash
pip install pre-commit
pre-commit install
```

## License

This integration is licensed under the Apache License 2.0.

## Author

**Tsakiridis Ilias**
GitHub: [@DefinitelyADev](https://github.com/DefinitelyADev)
Location: Greece
