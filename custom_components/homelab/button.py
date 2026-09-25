"""Button platform for Homelab service control actions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .const import DOMAIN
from .entity import HomelabEntity
from .models import HomelabServiceItem

_LOGGER = logging.getLogger(__name__)


class HomelabRestartButton(HomelabEntity):
    """Button to safely trigger a restart of a Homelab service."""

    def __init__(
        self,
        entry_id: str,
        service_id: str,
        service_item: HomelabServiceItem,
        coordinator: Any,
    ) -> None:
        """Initialize the restart button."""
        super().__init__(entry_id, service_id, service_item)
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_{service_id}_restart"
        self._attr_name = f"{service_item.name} Restart"
        self._attr_device_class = "restart"
        self._attr_icon = "mdi:restart"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return self._attr_unique_id

    @property
    def name(self) -> str:
        """Return entity name."""
        return self._attr_name

    @property
    def available(self) -> bool:
        """Button is available if service can be restarted and host is reachable."""
        return super().available and self.service_item.can_restart

    async def async_press(self) -> None:
        """Handle button press to restart container or PVE guest."""
        client = getattr(self.coordinator, "client", None)
        if not client:
            _LOGGER.error("API client not available on coordinator")
            return

        item = self.service_item
        if item.kind == "guest" and item.vmid and item.node:
            _LOGGER.info("Rebooting PVE guest %s (%s)", item.name, item.vmid)
            # Default to lxc guest unless vmid is QEMU
            guest_type = "qemu" if item.extra_attributes.get("is_qemu") else "lxc"
            await client.async_reboot_pve_guest(item.node, guest_type, item.vmid)
        elif item.docker_host and item.main_container_id:
            _LOGGER.info("Restarting Docker container %s (%s)", item.name, item.main_container_id)
            await client.async_restart_docker_container(
                item.docker_host, item.main_container_id
            )
        else:
            _LOGGER.warning("Service %s does not support direct restart", item.name)
            return

        # Trigger coordinator data refresh
        if hasattr(self.coordinator, "async_refresh_data"):
            await self.coordinator.async_refresh_data()


async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities: Callable[[list[HomelabRestartButton]], None],
) -> None:
    """Set up restart buttons from config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    if not coordinator or not hasattr(coordinator, "data"):
        return

    entities: list[HomelabRestartButton] = []
    for service_id, item in coordinator.data.services.items():
        if item.can_restart:
            entities.append(
                HomelabRestartButton(
                    entry_id=entry.entry_id,
                    service_id=service_id,
                    service_item=item,
                    coordinator=coordinator,
                )
            )

    async_add_entities(entities)
