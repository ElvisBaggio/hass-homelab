"""Unit tests for Homelab binary_sensor and sensor platforms."""

from __future__ import annotations

import pytest

from custom_components.homelab.binary_sensor import (
    HomelabBinarySensor,
)
from custom_components.homelab.binary_sensor import (
    async_setup_entry as async_setup_binary_sensors,
)
from custom_components.homelab.const import (
    DOMAIN,
    STATE_RUNNING,
    STATE_STOPPED,
    STATE_UNAVAILABLE,
)
from custom_components.homelab.models import (
    HomelabComponent,
    HomelabServiceItem,
    HomelabSnapshot,
)
from custom_components.homelab.sensor import (
    HomelabSensor,
)
from custom_components.homelab.sensor import (
    async_setup_entry as async_setup_sensors,
)


@pytest.fixture
def sample_snapshot() -> HomelabSnapshot:
    """Provide a sample HomelabSnapshot."""
    return HomelabSnapshot(
        services={
            "immich": HomelabServiceItem(
                service_id="immich",
                name="Immich",
                group="Casa & dados",
                icon="mdi:image-multiple",
                kind="compose",
                state=STATE_RUNNING,
                uptime=86400,
                cpu_percent=12.5,
                memory_usage_bytes=1073741824,  # 1024 MB
                current_version="v1.115.0",
                components=[
                    HomelabComponent(
                        component_id="c1",
                        name="immich_server",
                        image="immich-server:v1.115.0",
                        state="running",
                        status="Up",
                    )
                ],
            ),
            "wallos": HomelabServiceItem(
                service_id="wallos",
                name="Wallos",
                group="Casa & dados",
                icon="mdi:wallet",
                kind="compose",
                state=STATE_STOPPED,
                uptime=0,
                cpu_percent=0.0,
                memory_usage_bytes=0,
                current_version="v1.0.0",
            ),
            "dead_service": HomelabServiceItem(
                service_id="dead_service",
                name="Dead Service",
                group="Infraestrutura",
                icon="mdi:alert",
                kind="container",
                state=STATE_UNAVAILABLE,
            ),
        }
    )


def test_binary_sensor_properties(sample_snapshot) -> None:
    """Test binary sensor status and availability."""
    immich_item = sample_snapshot.services["immich"]
    sensor_immich = HomelabBinarySensor(
        entry_id="test_entry",
        service_id="immich",
        service_item=immich_item,
    )

    assert sensor_immich.unique_id == "test_entry_immich_status"
    assert sensor_immich.name == "Immich Status"
    assert sensor_immich.is_on is True
    assert sensor_immich.available is True
    assert sensor_immich.device_info["name"] == "Immich"
    assert sensor_immich.device_info["suggested_area"] == "Casa & dados"

    # Test stopped service
    wallos_item = sample_snapshot.services["wallos"]
    sensor_wallos = HomelabBinarySensor(
        entry_id="test_entry",
        service_id="wallos",
        service_item=wallos_item,
    )
    assert sensor_wallos.is_on is False
    assert sensor_wallos.available is True

    # Test unavailable service
    dead_item = sample_snapshot.services["dead_service"]
    sensor_dead = HomelabBinarySensor(
        entry_id="test_entry",
        service_id="dead_service",
        service_item=dead_item,
    )
    assert sensor_dead.available is False


def test_sensor_metrics_properties(sample_snapshot) -> None:
    """Test sensor metric values."""
    immich_item = sample_snapshot.services["immich"]

    uptime_sensor = HomelabSensor(
        entry_id="test_entry",
        service_id="immich",
        sensor_type="uptime",
        service_item=immich_item,
    )
    assert uptime_sensor.unique_id == "test_entry_immich_uptime"
    assert uptime_sensor.native_value == 86400

    mem_sensor = HomelabSensor(
        entry_id="test_entry",
        service_id="immich",
        sensor_type="memory_mb",
        service_item=immich_item,
    )
    assert mem_sensor.unique_id == "test_entry_immich_memory_mb"
    assert mem_sensor.native_value == 1024.0


@pytest.mark.asyncio
async def test_async_setup_platforms(mock_hass, mock_config_entry, sample_snapshot) -> None:
    """Test setup of binary sensors and sensors platforms."""
    mock_coordinator = type("Coord", (), {"data": sample_snapshot})()
    mock_hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {"coordinator": mock_coordinator}
    }

    added_binary_entities = []
    added_sensor_entities = []

    await async_setup_binary_sensors(
        mock_hass,
        mock_config_entry,
        lambda entities: added_binary_entities.extend(entities),
    )
    assert len(added_binary_entities) == 3  # immich, wallos, dead_service

    await async_setup_sensors(
        mock_hass,
        mock_config_entry,
        lambda entities: added_sensor_entities.extend(entities),
    )
    assert len(added_sensor_entities) >= 3
