"""Async API Client for Proxmox VE and Docker Socket Proxy."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class HomelabApiError(Exception):
    """Base exception for Homelab API errors."""


class HomelabAuthError(HomelabApiError):
    """Authentication failure exception."""


class HomelabConnectionError(HomelabApiError):
    """Network connection failure exception."""


class HomelabApiClient:
    """API client interacting with Proxmox VE API and Docker Socket Proxy."""

    def __init__(
        self,
        pve_host: str,
        pve_port: int = 8006,
        pve_token_id: str | None = None,
        pve_token_secret: str | None = None,
        pve_verify_ssl: bool = False,
        docker_hosts: list[str] | None = None,
        session: aiohttp.ClientSession | None = None,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the API client."""
        self.pve_host = pve_host
        self.pve_port = pve_port
        self.pve_token_id = pve_token_id
        self.pve_token_secret = pve_token_secret
        self.pve_verify_ssl = pve_verify_ssl
        self.docker_hosts = docker_hosts or []
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

    @property
    def _pve_base_url(self) -> str:
        """Return base URL for Proxmox VE API."""
        return f"https://{self.pve_host}:{self.pve_port}/api2/json"

    @property
    def _pve_headers(self) -> dict[str, str]:
        """Return authorization headers for Proxmox VE."""
        if self.pve_token_id and self.pve_token_secret:
            return {"Authorization": f"PVEAPIToken={self.pve_token_id}={self.pve_token_secret}"}
        return {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create active ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def async_validate_connection(self) -> bool:
        """Validate connection to PVE and all configured Docker hosts."""
        session = await self._get_session()

        # Check PVE
        try:
            url = f"{self._pve_base_url}/version"
            async with session.get(
                url,
                headers=self._pve_headers,
                ssl=self.pve_verify_ssl,
                timeout=self._timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise HomelabAuthError(f"PVE authentication failed: {resp.status}")
                if resp.status != 200:
                    raise HomelabConnectionError(f"PVE responded with status {resp.status}")
        except (TimeoutError, aiohttp.ClientError) as err:
            raise HomelabConnectionError(f"Failed to connect to PVE host: {err}") from err

        # Check Docker hosts
        for host in self.docker_hosts:
            ping_url = f"{host.rstrip('/')}/_ping"
            try:
                async with session.get(ping_url, timeout=self._timeout) as resp:
                    if resp.status != 200:
                        raise HomelabConnectionError(f"Docker host {host} returned {resp.status}")
            except (TimeoutError, aiohttp.ClientError) as err:
                msg = f"Failed to connect to Docker host {host}: {err}"
                raise HomelabConnectionError(msg) from err

        return True

    async def async_get_pve_resources(self) -> list[dict[str, Any]]:
        """Fetch all cluster resources (nodes, VMs, LXCs, storages)."""
        session = await self._get_session()
        url = f"{self._pve_base_url}/cluster/resources"
        try:
            async with session.get(
                url,
                headers=self._pve_headers,
                ssl=self.pve_verify_ssl,
                timeout=self._timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise HomelabAuthError("PVE token rejected")
                if resp.status != 200:
                    raise HomelabApiError(f"PVE cluster/resources failed: {resp.status}")
                data = await resp.json()
                return data.get("data", [])
        except (TimeoutError, aiohttp.ClientError) as err:
            raise HomelabConnectionError(f"Connection error fetching PVE resources: {err}") from err

    async def async_reboot_pve_guest(self, node: str, guest_type: str, vmid: int) -> bool:
        """Reboot a PVE guest (qemu or lxc)."""
        session = await self._get_session()
        url = f"{self._pve_base_url}/nodes/{node}/{guest_type}/{vmid}/status/reboot"
        try:
            async with session.post(
                url,
                headers=self._pve_headers,
                ssl=self.pve_verify_ssl,
                timeout=self._timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise HomelabAuthError("PVE token rejected")
                return resp.status == 200
        except (TimeoutError, aiohttp.ClientError) as err:
            raise HomelabConnectionError(f"Error rebooting guest {vmid}: {err}") from err

    async def async_get_docker_containers(self, docker_host: str) -> list[dict[str, Any]]:
        """Fetch all containers from a Docker host."""
        session = await self._get_session()
        url = f"{docker_host.rstrip('/')}/containers/json?all=1"
        try:
            async with session.get(url, timeout=self._timeout) as resp:
                if resp.status != 200:
                    raise HomelabApiError(f"Docker containers query failed: {resp.status}")
                return await resp.json()
        except (TimeoutError, aiohttp.ClientError) as err:
            msg = f"Connection error querying Docker host {docker_host}: {err}"
            raise HomelabConnectionError(msg) from err

    async def async_restart_docker_container(self, docker_host: str, container_id: str) -> bool:
        """Restart a specific Docker container."""
        session = await self._get_session()
        url = f"{docker_host.rstrip('/')}/containers/{container_id}/restart"
        try:
            async with session.post(url, timeout=self._timeout) as resp:
                return resp.status in (200, 204)
        except (TimeoutError, aiohttp.ClientError) as err:
            msg = f"Error restarting container {container_id}: {err}"
            raise HomelabConnectionError(msg) from err
