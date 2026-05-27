"""Pytest configuration for Custom Areas tests.

Explicitly registers ``pytest_homeassistant_custom_component`` as a plugin so
that its async ``hass`` fixture and helpers (``MockConfigEntry``,
``enable_custom_integrations``) are recognized by pytest-asyncio. The plugin
self-registers via setuptools entry_points, but the auto-discovery is no
longer sufficient under pytest-asyncio 1.x (HA 2025+ cells in the CI matrix);
explicit registration is required for the strict async-fixture semantics.

This module deliberately does NOT declare an ``autouse``
``enable_custom_integrations`` wrapper. Doing so pulls the async ``hass``
fixture into the dependency closure of every test, including the synchronous
``MagicMock``-based tests in ``test_sensor.py`` and
``test_sensor_characterization.py``. Under strict pytest-asyncio those sync
tests fail at setup because the async ``hass`` fixture is returned as an
``async_generator`` rather than a resolved instance.

Async tests that actually need the integration to be discoverable via
``hass.config_entries`` (anything calling ``async_setup`` /
``flow.async_init`` / ``flow.async_configure``) should declare
``enable_custom_integrations`` in their parameter list explicitly.
"""

pytest_plugins = "pytest_homeassistant_custom_component"
