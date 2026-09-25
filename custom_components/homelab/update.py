"""Update platform for Homelab services."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .const import DOMAIN
from .entity import HomelabEntity
from .models import HomelabServiceItem

_LOGGER = logging.getLogger(__name__)


class HomelabUpdateEntity(HomelabEntity):
    """Entity representing software update status for Homelab services."""

    def __init__(
        self,
        entry_id: str,
        service_id: str,
        service_item: HomelabServiceItem,
    ) -> None:
        """Initialize the update entity."""
        super().__init__(entry_id, service_id, service_item)
        self._attr_unique_id = f"{entry_id}_{service_id}_update"
        self._attr_title = service_item.name
        self._attr_icon = "mdi:update"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return self._attr_unique_id

    @property
    def title(self) -> str:
        """Return update entity title."""
        return self._attr_title

    @property
    def installed_version(self) -> str | None:
        """Return current installed version."""
        return self.service_item.current_version

    @property
    def latest_version(self) -> str | None:
        """Return latest available version."""
        return self.service_item.available_version or self.service_item.current_version

    @property
    def release_summary(self) -> str | None:
        """Return release summary if available."""
        avail = self.service_item.available_version
        curr = self.service_item.current_version
        if avail and avail != curr:
            return f"New image available: {avail}"
        return None


async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities: Callable[[list[HomelabUpdateEntity]], None],
) -> None:
    """Set up update entities from config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    if not coordinator or not hasattr(coordinator, "data"):
        return

    entities: list[HomelabUpdateEntity] = []
    for service_id, item in coordinator.data.services.items():
        if item.can_update:
            entities.append(
                HomelabUpdateEntity(
                    entry_id=entry.entry_id,
                    service_id=service_id,
                    service_item=item,
                )
            )

    async_add_entities(entities)
