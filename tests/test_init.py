"""Test Homelab integration init/unload."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.homelab import async_setup_entry, async_unload_entry
from custom_components.homelab.const import DOMAIN, PLATFORMS
from custom_components.homelab.models import HomelabSnapshot


@pytest.mark.asyncio
async def test_setup_and_unload_entry(mock_hass, mock_config_entry) -> None:
    """Test full setup and unload of entry."""
    with patch(
        "custom_components.homelab.coordinator.HomelabDataUpdateCoordinator.async_refresh_data",
        new_callable=AsyncMock,
        return_value=HomelabSnapshot(),
    ):
        # Setup
        assert await async_setup_entry(mock_hass, mock_config_entry) is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        assert "coordinator" in mock_hass.data[DOMAIN][mock_config_entry.entry_id]

        mock_hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
            mock_config_entry, PLATFORMS
        )

        # Unload
        assert await async_unload_entry(mock_hass, mock_config_entry) is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        mock_hass.config_entries.async_unload_platforms.assert_awaited_once_with(
            mock_config_entry, PLATFORMS
        )
