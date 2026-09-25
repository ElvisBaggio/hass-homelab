"""Base entity for Homelab integration."""

from __future__ import annotations

from typing import Any

from .const import DOMAIN, STATE_UNAVAILABLE
from .models import HomelabServiceItem


class HomelabEntity:
    """Base entity class for Homelab services."""

    def __init__(
        self,
        entry_id: str,
        service_id: str,
        service_item: HomelabServiceItem,
    ) -> None:
        """Initialize Homelab base entity."""
        self.entry_id = entry_id
        self.service_id = service_id
        self.service_item = service_item

    @property
    def device_info(self) -> dict[str, Any]:
        """Return Home Assistant device info grouping entities per service."""
        sw_version = self.service_item.current_version
        if not sw_version and self.service_item.vmid:
            sw_version = f"PVE VMID {self.service_item.vmid}"

        return {
            "identifiers": {(DOMAIN, f"{self.entry_id}_{self.service_id}")},
            "name": self.service_item.name,
            "manufacturer": "Homelab",
            "model": f"{self.service_item.kind.capitalize()} Service",
            "sw_version": sw_version,
            "suggested_area": self.service_item.group,
        }

    @property
    def available(self) -> bool:
        """Return True if service/host is reachable."""
        return self.service_item.state != STATE_UNAVAILABLE

    def update_service_item(self, item: HomelabServiceItem) -> None:
        """Update service item state from coordinator refresh."""
        self.service_item = item
