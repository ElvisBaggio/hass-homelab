"""Homelab integration setup."""

from __future__ import annotations

import logging
from typing import Any

from .api import HomelabApiClient
from .const import (
    CONF_DOCKER_HOSTS,
    CONF_PVE_HOST,
    CONF_PVE_PORT,
    CONF_PVE_TOKEN_ID,
    CONF_PVE_TOKEN_SECRET,
    CONF_PVE_VERIFY_SSL,
    CONF_SCAN_INTERVAL,
    DEFAULT_PVE_PORT,
    DEFAULT_PVE_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import HomelabDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    """Set up Homelab from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    data = entry.data
    options = getattr(entry, "options", {})

    pve_host = data.get(CONF_PVE_HOST)
    pve_port = data.get(CONF_PVE_PORT, DEFAULT_PVE_PORT)
    pve_token_id = data.get(CONF_PVE_TOKEN_ID)
    pve_token_secret = data.get(CONF_PVE_TOKEN_SECRET)
    pve_verify_ssl = data.get(CONF_PVE_VERIFY_SSL, DEFAULT_PVE_VERIFY_SSL)
    docker_hosts = options.get(CONF_DOCKER_HOSTS, data.get(CONF_DOCKER_HOSTS, []))
    scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = getattr(hass, "http_client_session", None)
    client = HomelabApiClient(
        pve_host=pve_host,
        pve_port=pve_port,
        pve_token_id=pve_token_id,
        pve_token_secret=pve_token_secret,
        pve_verify_ssl=pve_verify_ssl,
        docker_hosts=docker_hosts,
        session=session,
    )

    coordinator = HomelabDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=scan_interval,
    )

    # Initial data fetch
    await coordinator.async_refresh_data()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Setup platforms via HA config entry manager if available
    config_entries = getattr(hass, "config_entries", None)
    if config_entries and hasattr(config_entries, "async_forward_entry_setups"):
        await config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    """Unload a Homelab config entry."""
    unload_ok = True
    config_entries = getattr(hass, "config_entries", None)
    if config_entries and hasattr(config_entries, "async_unload_platforms"):
        unload_ok = await config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
