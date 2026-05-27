"""Pytest configuration for Custom Areas tests.

Explicitly registers ``pytest_homeassistant_custom_component`` as a plugin so
its ``hass`` fixture and helpers (``MockConfigEntry``) are discoverable. The
plugin self-registers via setuptools entry_points, but auto-discovery is not
sufficient under pytest-asyncio 1.x (HA 2025+ cells in the CI matrix);
explicit registration is required for strict async-fixture semantics.

We intentionally do NOT wire phacc's ``enable_custom_integrations`` as a
fixture (autouse or opt-in). pytest-asyncio in all supported versions only
auto-awaits the async ``hass`` fixture when it is a *direct* test
dependency, not when reached transitively through another fixture's
parameter list. phacc declares ``enable_custom_integrations`` as
``@pytest.fixture`` (sync) but depends on async ``hass``; reaching ``hass``
through it produces an unawaited ``async_generator`` and the first
attribute access fails. Tests that need the integration to be discoverable
call ``_helpers.enable_custom_integrations(hass)`` inline at the top of
the test body where ``hass`` is the resolved HomeAssistant.
"""

pytest_plugins = "pytest_homeassistant_custom_component"
