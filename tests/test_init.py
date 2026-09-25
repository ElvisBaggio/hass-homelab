"""Test Homelab integration init/unload."""

import pytest

from custom_components.homelab import async_setup_entry, async_unload_entry
from custom_components.homelab.const import DOMAIN, PLATFORMS


@pytest.mark.asyncio
async def test_setup_and_unload_entry(mock_hass, mock_config_entry) -> None:
    """Test full setup and unload of entry."""
    # Setup
    assert await async_setup_entry(mock_hass, mock_config_entry) is True
    assert DOMAIN in mock_hass.data
    assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
    assert (
        mock_hass.data[DOMAIN][mock_config_entry.entry_id]["data"]["pve_host"]
        == "192.168.1.9"
    )

    mock_hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        mock_config_entry, PLATFORMS
    )

    # Unload
    assert await async_unload_entry(mock_hass, mock_config_entry) is True
    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
    mock_hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        mock_config_entry, PLATFORMS
    )
