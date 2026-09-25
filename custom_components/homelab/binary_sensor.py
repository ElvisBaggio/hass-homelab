"""Binary sensor platform for Homelab integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .const import DOMAIN, STATE_RUNNING
from .entity import HomelabEntity
from .models import HomelabServiceItem


class HomelabBinarySensor(HomelabEntity):
    """Binary sensor representing service operational status."""

    def __init__(
        self,
        entry_id: str,
        service_id: str,
        service_item: HomelabServiceItem,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry_id, service_id, service_item)
        self._attr_unique_id = f"{entry_id}_{service_id}_status"
        self._attr_name = f"{service_item.name} Status"
        self._attr_device_class = "running"
        self._attr_icon = service_item.icon

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return self._attr_unique_id

    @property
    def name(self) -> str:
        """Return entity name."""
        return self._attr_name

    @property
    def is_on(self) -> bool:
        """Return True if service is currently running."""
        return self.service_item.state == STATE_RUNNING

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "kind": self.service_item.kind,
            "group": self.service_item.group,
            "components_count": len(self.service_item.components),
            "state_raw": self.service_item.state,
        }


async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities: Callable[[list[HomelabBinarySensor]], None],
) -> None:
    """Set up binary sensors from config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    if not coordinator or not hasattr(coordinator, "data"):
        return

    entities: list[HomelabBinarySensor] = []
    for service_id, item in coordinator.data.services.items():
        entities.append(
            HomelabBinarySensor(
                entry_id=entry.entry_id,
                service_id=service_id,
                service_item=item,
            )
        )

    async_add_entities(entities)
