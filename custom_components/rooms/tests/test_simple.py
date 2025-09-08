from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.rooms.config_flow import RoomsConfigFlow


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    return hass


@pytest.mark.asyncio
async def test_async(mock_hass):
    flow = RoomsConfigFlow()
    flow.hass = mock_hass
    flow.context = {}
    assert True


def test_simple():
    assert True
