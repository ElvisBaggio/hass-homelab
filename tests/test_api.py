"""Unit tests for Homelab API Client."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import aiohttp
import pytest

from custom_components.homelab.api import (
    HomelabApiClient,
    HomelabAuthError,
)


class MockResponse:
    """Mock aiohttp response context manager."""

    def __init__(self, status: int, data: Any = None, text_data: str = "") -> None:
        self.status = status
        self._data = data
        self._text_data = text_data

    async def __aenter__(self) -> MockResponse:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def json(self) -> Any:
        return self._data

    async def text(self) -> str:
        return self._text_data


@pytest.mark.asyncio
async def test_get_pve_resources_success() -> None:
    """Test fetching PVE cluster resources with token auth."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.get.return_value = MockResponse(
        status=200,
        data={
            "data": [
                {
                    "id": "lxc/100",
                    "vmid": 100,
                    "name": "hermes",
                    "type": "lxc",
                    "status": "running",
                    "node": "pve",
                    "uptime": 123456,
                    "cpu": 0.05,
                    "mem": 1073741824,
                    "maxmem": 4294967296,
                }
            ]
        },
    )

    client = HomelabApiClient(
        pve_host="192.168.1.9",
        pve_port=8006,
        pve_token_id="root@pam!ha",
        pve_token_secret="test-secret",
        pve_verify_ssl=False,
        session=mock_session,
    )

    resources = await client.async_get_pve_resources()
    assert len(resources) == 1
    assert resources[0]["name"] == "hermes"
    assert resources[0]["vmid"] == 100
    assert resources[0]["status"] == "running"


@pytest.mark.asyncio
async def test_get_pve_resources_auth_error() -> None:
    """Test PVE 401 unauthorized raises HomelabAuthError."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.get.return_value = MockResponse(status=401)

    client = HomelabApiClient(
        pve_host="192.168.1.9",
        pve_token_id="root@pam!invalid",
        pve_token_secret="bad",
        session=mock_session,
    )

    with pytest.raises(HomelabAuthError):
        await client.async_get_pve_resources()


@pytest.mark.asyncio
async def test_get_docker_containers() -> None:
    """Test fetching Docker containers from socket proxy."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.get.return_value = MockResponse(
        status=200,
        data=[
            {
                "Id": "c1234567890",
                "Names": ["/immich_server"],
                "Image": "ghcr.io/immich-app/immich-server:v1.115.0",
                "State": "running",
                "Status": "Up 3 days",
                "Labels": {
                    "com.docker.compose.project": "immich",
                    "com.docker.compose.service": "immich-server",
                },
            }
        ],
    )

    client = HomelabApiClient(
        pve_host="192.168.1.9",
        docker_hosts=["http://192.168.1.193:2375"],
        session=mock_session,
    )

    containers = await client.async_get_docker_containers("http://192.168.1.193:2375")
    assert len(containers) == 1
    assert containers[0]["Names"][0] == "/immich_server"
    assert containers[0]["State"] == "running"


@pytest.mark.asyncio
async def test_restart_docker_container() -> None:
    """Test restarting a Docker container."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False
    mock_session.post.return_value = MockResponse(status=204)

    client = HomelabApiClient(pve_host="192.168.1.9", session=mock_session)

    success = await client.async_restart_docker_container(
        "http://192.168.1.193:2375", "c123"
    )
    assert success is True


@pytest.mark.asyncio
async def test_validate_connection_success() -> None:
    """Test validating connection to both PVE and Docker."""
    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.closed = False

    def side_effect_get(url: str, *args: Any, **kwargs: Any) -> MockResponse:
        if "version" in url:
            return MockResponse(status=200, data={"data": {"version": "8.2.4"}})
        if "_ping" in url:
            return MockResponse(status=200, text_data="OK")
        return MockResponse(status=404)

    mock_session.get.side_effect = side_effect_get

    client = HomelabApiClient(
        pve_host="192.168.1.9",
        pve_token_id="root@pam!ha",
        pve_token_secret="sec",
        docker_hosts=["http://192.168.1.193:2375"],
        session=mock_session,
    )

    is_valid = await client.async_validate_connection()
    assert is_valid is True
