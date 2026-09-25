"""Homelab integration setup."""

from __future__ import annotations

import logging
from typing import Any

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    """Set up Homelab from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    entry_data = {
        "entry_id": entry.entry_id,
        "data": dict(entry.data),
        "options": dict(getattr(entry, "options", {})),
    }
    hass.data[DOMAIN][entry.entry_id] = entry_data

    # Setup platforms via HA config entry manager if available
    config_entries = getattr(hass, "config_entries", None)
    if config_entries and hasattr(config_entries, "async_forward_entry_setups"):
        await config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    """Unload a Homelab config entry."""
    unload_ok = True
    if hasattr(hass, "config_entries") and hasattr(hass.config_entries, "async_unload_platforms"):
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
