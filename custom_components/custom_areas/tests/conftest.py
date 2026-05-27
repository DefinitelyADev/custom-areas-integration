"""Pytest configuration for Custom Areas tests.

Explicitly registers ``pytest_homeassistant_custom_component`` as a plugin so
that its ``hass`` fixture and helpers (``MockConfigEntry``,
``enable_custom_integrations``) are recognized by pytest-asyncio. The plugin
self-registers via setuptools entry_points, but the auto-discovery is no
longer sufficient under pytest-asyncio 1.x (HA 2025+ cells in the CI matrix);
explicit registration is required for the strict async-fixture semantics.

We also shadow phacc's sync ``enable_custom_integrations`` fixture with an
async-aware version. phacc declares its fixture as ``@pytest.fixture`` (sync)
but depends on the async ``hass`` fixture. Under pytest-asyncio 0.23.x the
chain was bridged transparently. Under pytest-asyncio 1.x it is not — the
sync fixture receives the raw ``async_generator`` from ``hass`` rather than
a resolved ``HomeAssistant`` instance, and the very first attribute access
fails with::

    AttributeError: 'async_generator' object has no attribute 'data'

Defining the fixture as ``@pytest_asyncio.fixture`` puts pytest-asyncio in
charge of the await chain. Tests opt in by declaring
``enable_custom_integrations`` in their parameter list (no autouse — that
would pull ``hass`` into the dependency closure of the synchronous
``MagicMock``-based tests in test_sensor.py / test_sensor_characterization.py
and reproduce the same async-generator bug for them).
"""

import pytest_asyncio
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest_asyncio.fixture
async def enable_custom_integrations(hass: HomeAssistant):
    """Allow Home Assistant to discover the custom_areas integration during tests.

    Async-aware shadow of phacc's same-named fixture; see module docstring
    for the pytest-asyncio compatibility rationale.
    """
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)
    yield
