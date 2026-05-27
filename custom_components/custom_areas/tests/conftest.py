"""Pytest configuration for Custom Areas tests.

Explicitly registers ``pytest_homeassistant_custom_component`` as a plugin so
that its async ``hass`` fixture is recognized by pytest-asyncio. The plugin
self-registers via setuptools entry_points, but the auto-discovery is no
longer sufficient under pytest-asyncio 1.x (HA 2025+ cells in the CI matrix);
explicit registration is required for the strict async-fixture semantics.

The ``auto_enable_custom_integrations`` autouse fixture is required by
``pytest_homeassistant_custom_component`` so that the custom integration
under test (``custom_areas`` in this repo) is actually loaded when the
``hass`` fixture brings up Home Assistant.
"""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to discover custom integrations during tests."""
    yield
