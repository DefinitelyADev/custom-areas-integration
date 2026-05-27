"""Shared synchronous helpers for the Custom Areas test suite."""

from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS


def enable_custom_integrations(hass: HomeAssistant) -> None:
    """Allow Home Assistant to discover the custom_areas integration during a test.

    Mirrors what ``pytest_homeassistant_custom_component``'s same-named fixture
    does, but called inline from inside an async test body rather than wired
    as a fixture dependency. The fixture form fails under modern
    pytest-asyncio: phacc declares ``enable_custom_integrations`` as
    ``@pytest.fixture`` (sync) depending on the async ``hass`` fixture, and
    pytest-asyncio only auto-awaits ``hass`` when it is a *direct* test
    dependency. As a *transitive* dependency through another fixture, ``hass``
    arrives in the sync fixture body as a raw ``async_generator`` and the
    first attribute access fails with::

        AttributeError: 'async_generator' object has no attribute 'data'

    Calling this helper from inside the async test instead — where ``hass``
    is the resolved HomeAssistant instance — avoids the bridging problem
    entirely.
    """
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)
