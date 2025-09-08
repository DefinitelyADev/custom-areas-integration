# Changelog

All notable changes to the Rooms integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
