"""Sensor platform for Homelab integration metrics."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .const import DOMAIN
from .entity import HomelabEntity
from .models import HomelabServiceItem

SENSOR_TYPES = {
    "uptime": {
        "name_suffix": "Uptime",
        "icon": "mdi:timer-outline",
        "unit": "s",
        "device_class": "duration",
        "value_fn": lambda item: item.uptime,
    },
    "cpu_percent": {
        "name_suffix": "CPU Usage",
        "icon": "mdi:cpu-64-bit",
        "unit": "%",
        "device_class": None,
        "value_fn": lambda item: item.cpu_percent,
    },
    "memory_mb": {
        "name_suffix": "Memory",
        "icon": "mdi:memory",
        "unit": "MB",
        "device_class": "data_size",
        "value_fn": lambda item: (
            round(item.memory_usage_bytes / (1024 * 1024), 1)
            if item.memory_usage_bytes > 0
            else 0.0
        ),
    },
}


class HomelabSensor(HomelabEntity):
    """Sensor exposing Homelab service metrics."""

    def __init__(
        self,
        entry_id: str,
        service_id: str,
        sensor_type: str,
        service_item: HomelabServiceItem,
    ) -> None:
        """Initialize the metric sensor."""
        super().__init__(entry_id, service_id, service_item)
        self.sensor_type = sensor_type
        config = SENSOR_TYPES.get(sensor_type, {})
        self._attr_unique_id = f"{entry_id}_{service_id}_{sensor_type}"
        self._attr_name = f"{service_item.name} {config.get('name_suffix', sensor_type)}"
        self._attr_icon = config.get("icon", "mdi:gauge")
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_device_class = config.get("device_class")
        self._value_fn = config.get("value_fn", lambda item: None)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return self._attr_unique_id

    @property
    def name(self) -> str:
        """Return entity name."""
        return self._attr_name

    @property
    def native_value(self) -> Any:
        """Return current metric value."""
        return self._value_fn(self.service_item)


async def async_setup_entry(
    hass: Any,
    entry: Any,
    async_add_entities: Callable[[list[HomelabSensor]], None],
) -> None:
    """Set up metric sensors from config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    if not coordinator or not hasattr(coordinator, "data"):
        return

    entities: list[HomelabSensor] = []
    for service_id, item in coordinator.data.services.items():
        for s_type in SENSOR_TYPES:
            entities.append(
                HomelabSensor(
                    entry_id=entry.entry_id,
                    service_id=service_id,
                    sensor_type=s_type,
                    service_item=item,
                )
            )

    async_add_entities(entities)
