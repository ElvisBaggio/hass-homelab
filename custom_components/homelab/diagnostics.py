"""Diagnostics support for Homelab integration."""

from __future__ import annotations

from typing import Any

from .const import CONF_PVE_TOKEN_SECRET, DOMAIN

TO_REDACT = {
    CONF_PVE_TOKEN_SECRET,
    "password",
    "secret",
    "token",
    "api_key",
    "access_token",
}


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive fields from dictionary."""
    redacted: dict[str, Any] = {}
    for key, val in data.items():
        if key in TO_REDACT:
            redacted[key] = "**REDACTED**"
        elif isinstance(val, dict):
            redacted[key] = _redact_dict(val)
        elif isinstance(val, list):
            redacted[key] = [
                _redact_dict(item) if isinstance(item, dict) else item
                for item in val
            ]
        else:
            redacted[key] = val
    return redacted


async def async_get_config_entry_diagnostics(
    hass: Any,
    entry: Any,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    coordinator_data = (
        coordinator.data.to_dict()
        if coordinator and hasattr(coordinator, "data") and hasattr(coordinator.data, "to_dict")
        else {}
    )

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "domain": entry.domain,
            "title": getattr(entry, "title", "Homelab"),
            "data": _redact_dict(dict(entry.data)),
            "options": _redact_dict(dict(getattr(entry, "options", {}))),
        },
        "data": coordinator_data,
    }
