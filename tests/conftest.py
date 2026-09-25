"""Fixtures for Homelab integration tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class MockConfigEntry:
    """Mock Home Assistant ConfigEntry."""

    def __init__(
        self,
        domain: str,
        data: dict,
        options: dict | None = None,
        entry_id: str = "mock_entry_id",
        title: str = "Homelab",
    ) -> None:
        self.domain = domain
        self.data = data
        self.options = options or {}
        self.entry_id = entry_id
        self.title = title


class MockHass:
    """Mock Home Assistant core instance."""

    def __init__(self) -> None:
        self.data = {}
        self.config_entries = MagicMock()
        self.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        self.config_entries.async_unload_platforms = AsyncMock(return_value=True)


@pytest.fixture
def mock_hass() -> MockHass:
    """Provide a mock HomeAssistant instance."""
    return MockHass()


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Provide a mock ConfigEntry instance."""
    return MockConfigEntry(
        domain="homelab",
        data={
            "pve_host": "192.168.1.9",
            "pve_port": 8006,
            "pve_token_id": "root@pam!ha",
            "pve_token_secret": "mock_secret",
            "pve_verify_ssl": False,
            "docker_hosts": ["http://192.168.1.193:2375"],
        },
        options={"scan_interval": 30},
        entry_id="test_entry_123",
        title="Homelab (192.168.1.9)",
    )
