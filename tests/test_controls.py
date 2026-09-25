"""Unit tests for Homelab update and button platforms."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.homelab.button import (
    HomelabRestartButton,
)
from custom_components.homelab.button import (
    async_setup_entry as async_setup_buttons,
)
from custom_components.homelab.const import DOMAIN, STATE_RUNNING
from custom_components.homelab.models import (
    HomelabComponent,
    HomelabServiceItem,
    HomelabSnapshot,
)
from custom_components.homelab.update import (
    HomelabUpdateEntity,
)
from custom_components.homelab.update import (
    async_setup_entry as async_setup_updates,
)


@pytest.fixture
def sample_snapshot_controls() -> HomelabSnapshot:
    """Provide sample services for control platforms."""
    return HomelabSnapshot(
        services={
            "immich": HomelabServiceItem(
                service_id="immich",
                name="Immich",
                group="Casa & dados",
                icon="mdi:image-multiple",
                kind="compose",
                state=STATE_RUNNING,
                current_version="v1.115.0",
                available_version="v1.116.0",
                can_update=True,
                can_restart=True,
                docker_host="http://192.168.1.193:2375",
                main_container_id="c_immich_server_123",
                components=[
                    HomelabComponent(
                        component_id="c1",
                        name="immich_server",
                        image="immich-server:v1.115.0",
                        state="running",
                        status="Up",
                        host="http://192.168.1.193:2375",
                        container_id="c_immich_server_123",
                    )
                ],
            ),
            "hermes": HomelabServiceItem(
                service_id="hermes",
                name="Hermes",
                group="IA & automação",
                icon="mdi:robot",
                kind="guest",
                state=STATE_RUNNING,
                vmid=100,
                node="pve",
                can_restart=True,
            ),
        }
    )


@pytest.mark.asyncio
async def test_button_restart_docker(sample_snapshot_controls) -> None:
    """Test restarting a docker service via button."""
    mock_api = MagicMock()
    mock_api.async_restart_docker_container = AsyncMock(return_value=True)

    mock_coordinator = MagicMock()
    mock_coordinator.client = mock_api
    mock_coordinator.async_refresh_data = AsyncMock()

    immich_item = sample_snapshot_controls.services["immich"]
    button = HomelabRestartButton(
        entry_id="test_entry",
        service_id="immich",
        service_item=immich_item,
        coordinator=mock_coordinator,
    )

    assert button.unique_id == "test_entry_immich_restart"
    assert button.name == "Immich Restart"

    await button.async_press()
    mock_api.async_restart_docker_container.assert_awaited_once_with(
        "http://192.168.1.193:2375", "c_immich_server_123"
    )
    mock_coordinator.async_refresh_data.assert_awaited_once()


@pytest.mark.asyncio
async def test_button_restart_pve_guest(sample_snapshot_controls) -> None:
    """Test rebooting a PVE guest via button."""
    mock_api = MagicMock()
    mock_api.async_reboot_pve_guest = AsyncMock(return_value=True)

    mock_coordinator = MagicMock()
    mock_coordinator.client = mock_api
    mock_coordinator.async_refresh_data = AsyncMock()

    hermes_item = sample_snapshot_controls.services["hermes"]
    button = HomelabRestartButton(
        entry_id="test_entry",
        service_id="hermes",
        service_item=hermes_item,
        coordinator=mock_coordinator,
    )

    await button.async_press()
    mock_api.async_reboot_pve_guest.assert_awaited_once_with("pve", "lxc", 100)


def test_update_entity_properties(sample_snapshot_controls) -> None:
    """Test update entity properties."""
    immich_item = sample_snapshot_controls.services["immich"]
    update_entity = HomelabUpdateEntity(
        entry_id="test_entry",
        service_id="immich",
        service_item=immich_item,
    )

    assert update_entity.unique_id == "test_entry_immich_update"
    assert update_entity.installed_version == "v1.115.0"
    assert update_entity.latest_version == "v1.116.0"
    assert update_entity.title == "Immich"


@pytest.mark.asyncio
async def test_async_setup_control_platforms(
    mock_hass, mock_config_entry, sample_snapshot_controls
) -> None:
    """Test platform setup for buttons and updates."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = sample_snapshot_controls
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator}
    }

    buttons = []
    updates = []

    await async_setup_buttons(mock_hass, mock_config_entry, lambda ents: buttons.extend(ents))
    assert len(buttons) == 2  # immich and hermes both have can_restart=True

    await async_setup_updates(mock_hass, mock_config_entry, lambda ents: updates.extend(ents))
    assert len(updates) == 1  # immich only has can_update=True
