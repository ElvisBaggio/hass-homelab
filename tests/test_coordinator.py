"""Unit tests for Homelab DataUpdateCoordinator and Diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.homelab.api import HomelabApiClient
from custom_components.homelab.coordinator import HomelabDataUpdateCoordinator
from custom_components.homelab.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_coordinator_reconcile_snapshot() -> None:
    """Test coordinator data fetch and snapshot generation."""
    mock_api = MagicMock(spec=HomelabApiClient)
    mock_api.docker_hosts = ["http://192.168.1.193:2375"]

    # Mock PVE resources
    mock_api.async_get_pve_resources = AsyncMock(
        return_value=[
            {
                "id": "lxc/100",
                "vmid": 100,
                "name": "hermes",
                "type": "lxc",
                "status": "running",
                "node": "pve",
                "uptime": 86400,
                "cpu": 0.12,
                "mem": 536870912,
                "maxmem": 2147483648,
            },
            {
                "id": "node/pve",
                "node": "pve",
                "type": "node",
                "status": "online",
                "uptime": 1000000,
                "cpu": 0.08,
                "mem": 8589934592,
                "maxmem": 34359738368,
            },
        ]
    )

    # Mock Docker containers
    mock_api.async_get_docker_containers = AsyncMock(
        return_value=[
            {
                "Id": "c_immich_server_123",
                "Names": ["/immich_server"],
                "Image": "ghcr.io/immich-app/immich-server:v1.115.0",
                "State": "running",
                "Status": "Up 2 days",
                "Labels": {
                    "com.docker.compose.project": "immich",
                    "com.docker.compose.service": "immich-server",
                },
            },
            {
                "Id": "c_immich_postgres_456",
                "Names": ["/immich_postgres"],
                "Image": "tensorchord/pgvecto-rs:pg16-v0.2.1",
                "State": "running",
                "Status": "Up 2 days",
                "Labels": {
                    "com.docker.compose.project": "immich",
                    "com.docker.compose.service": "immich-postgres",
                },
            },
            {
                "Id": "c_wallos_789",
                "Names": ["/wallos"],
                "Image": "bellsoft/liberica-openjdk-alpine:latest",
                "State": "exited",
                "Status": "Exited (0) 4 hours ago",
                "Labels": {
                    "com.docker.compose.project": "wallos",
                    "com.docker.compose.service": "wallos",
                },
            },
        ]
    )

    coordinator = HomelabDataUpdateCoordinator(
        hass=None,
        client=mock_api,
        update_interval=30,
    )

    snapshot = await coordinator.async_refresh_data()

    assert "hermes" in snapshot.services
    hermes = snapshot.services["hermes"]
    assert hermes.state == "running"
    assert hermes.kind == "guest"
    assert hermes.can_restart is True

    assert "immich" in snapshot.services
    immich = snapshot.services["immich"]
    assert immich.state == "running"
    assert immich.kind == "compose"
    assert len(immich.components) == 2  # server + postgres

    assert "wallos" in snapshot.services
    wallos = snapshot.services["wallos"]
    assert wallos.state == "stopped"  # exited = stopped, NOT unavailable
    assert wallos.kind == "compose"


@pytest.mark.asyncio
async def test_diagnostics_sanitization(mock_config_entry) -> None:
    """Test diagnostics dump redacts token secret."""
    mock_hass = MagicMock()
    mock_hass.data = {
        "homelab": {
            mock_config_entry.entry_id: {
                "coordinator": MagicMock(
                    data=MagicMock(
                        to_dict=lambda: {"services": {"hermes": {"state": "running"}}}
                    )
                )
            }
        }
    }

    diag = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)

    assert diag["entry"]["data"]["pve_token_secret"] == "**REDACTED**"
    assert diag["entry"]["data"]["pve_host"] == "192.168.1.9"
    assert "data" in diag
