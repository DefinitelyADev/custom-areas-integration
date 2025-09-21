# Changelog

All notable changes to the Rooms integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-09-22

### Fixed
- Updated CI workflow tag patterns to restrict triggers to version tags matching `vX.X.X` or `vX.X.X-<short-commit-hash>`
- Fixed Codecov action input to use 'files' instead of 'file'
- Fixed workflow permissions to resolve code scanning alerts

## [1.2.0] - 2025-09-22

### Added
- Individual measurement sensors: `AreaPowerSensor`, `AreaEnergySensor`, `AreaTemperatureSensor`, `AreaHumiditySensor`, `AreaClimateTargetSensor`
- Proper `native_unit_of_measurement` for each measurement sensor following Home Assistant standards
- Better separation of concerns: summary sensor for state, individual sensors for measurements

### Fixed
- Allows users to control precision and formatting through Home Assistant's built-in sensor features
- Follows Home Assistant sensor design principles

## [1.0.0] - 2025-09-09

### Added
- First stable release

## [0.0.3] - 2025-09-09

### Fixed
- Ensure entity_id keeps `room_` prefix using `suggested_object_id` while keeping the display name clean (just the room name). Existing entities may need a manual rename or re-add to pick up the new object_id.

## [0.0.2] - 2025-09-09

### Changed
- Attributes now include display-friendly values with units embedded (e.g., `power: "28.6 W"`, `temperature: "21.5 °C"`).
- Removed separate unit attributes (`*_unit`) to simplify dashboards.
- Kept numeric attributes for automations: `power_w`, `energy_wh`, `temperature_c`, `humidity_pct`, `climate_target_c`.

### Fixed
- Config flow now correctly awaits async methods (`async_create_entry`, `async_show_form`) to satisfy type checking.

## [0.0.1] - 2025-09-08

### Added
- Initial public release
- UI configuration flow for easy setup
- Composite room sensors with multiple entity support
- Real-time state updates using event-driven architecture
- Device registry integration
- Comprehensive state attributes (power, energy, temperature, humidity, etc.)
- Dynamic icon changes based on room status
- Configurable active power thresholds
- Support for motion, window, and climate entity integration
- Event-driven updates (no polling)
- Robust error handling for invalid sensor states
- State caching for performance optimization
- Proper cleanup of event listeners
- Type-safe implementation with comprehensive type hints
- Full test coverage with unit and integration tests
- CI/CD pipeline with automated validation
- Code quality tools (Black, isort, flake8, pyright)
- Compatible with Home Assistant 2024.1.0+
- Python 3.10+ support
- Memory-efficient implementation
- Clean separation of concerns with coordinator pattern

### Fixed
- Dependency conflict in requirements-dev.txt between pytest-asyncio and pytest-homeassistant-custom-component
