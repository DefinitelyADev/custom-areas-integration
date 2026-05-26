# Documentation Index

Welcome to the Custom Areas Integration documentation! This comprehensive documentation covers everything you need to know about installing, configuring, and extending the Custom Areas Integration for Home Assistant.

## 📖 Documentation Overview

### For Users
- **[README.md](../README.md)** - Main project documentation with installation and usage instructions
- **[examples.md](examples.md)** - Configuration examples and use cases
- **[api.md](api.md)** - Complete API reference for entities and attributes

### For Developers
- **[developer.md](developer.md)** - Architecture overview and development guide
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes

## 🚀 Quick Start

1. **Installation**: Follow the [HACS installation](../README.md#hacs-installation-recommended) guide
2. **Configuration**: See [Configuration Examples](examples.md) for common setups
3. **Usage**: Check the [Usage section](../README.md#usage) for sensor details

## 📋 Key Features

- ✅ **UI Configuration** - Easy setup through Home Assistant's interface
- ✅ **Composite Sensors** - Summary sensor (plus per-measurement passthroughs) representing multiple area aspects
- ✅ **Real-time Updates** - Event-driven updates, no polling required
- ✅ **Device Registry** - Proper integration with Home Assistant's device system
- ✅ **Flexible Configuration** - Support for power, energy, temperature, humidity, motion, windows, and climate entities

## 🏗️ Architecture

The integration consists of:
- **Config Flow** - Handles UI configuration and validation
- **Sensor Coordinator** - Manages state updates and event listeners
- **Area Sensor** - Main entity providing area state and attributes
- **Device Registry** - Creates proper device entries

## 🔧 Development

### Prerequisites
- Python 3.13+
- Home Assistant development environment
- Git

### Getting Started
```bash
git clone https://github.com/DefinitelyADev/room-entity.git
cd room-entity
pip install -r requirements-dev.txt
python check_all.py
```

### Testing
```bash
python run_tests.py              # Unit tests
python validate.py              # Custom validation
pyright                        # Type checking
```

## 📊 State Logic

Area states are determined by priority:
1. **Motion Detected** → `active`
2. **Power > Threshold** → `active`
3. **Entities Configured** → `idle`
4. **No Entities** → `unknown`

## 🎯 Use Cases

- **Living Areas** - Motion + temperature monitoring
- **Offices** - Power consumption + motion detection
- **Kitchens** - Multi-sensor monitoring (power, humidity, temperature)
- **Bedrooms** - Climate control + occupancy detection
- **Bathrooms** - Humidity + motion for ventilation

## 🤝 Contributing

We welcome contributions! See the [Contributing section](../README.md#contributing) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run validation: `python check_all.py`
5. Submit a pull request

## 📝 Support

- **Issues**: [GitHub Issues](https://github.com/DefinitelyADev/room-entity/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DefinitelyADev/room-entity/discussions)
- **Documentation**: This documentation and README.md

## 📈 Roadmap

Future enhancements may include:
- Area hierarchies and grouping
- Enhanced energy monitoring
- Historical analytics
- Advanced automation templates
- Mobile optimizations

---

*This integration is proudly "vibe coded" - balancing functionality with maintainable, iterative development.*
