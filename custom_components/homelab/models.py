"""Data models for Homelab integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class HomelabComponent:
    """Sub-component of a service (e.g. database, worker container)."""

    component_id: str
    name: str
    image: str
    state: str
    status: str
    host: str | None = None
    container_id: str | None = None


@dataclass
class HomelabServiceItem:
    """Represents a monitored and controllable Homelab service."""

    service_id: str
    name: str
    group: str
    icon: str
    kind: str  # host, guest, compose, container, systemd, external
    state: str  # running, stopped, unavailable
    uptime: int = 0  # seconds
    cpu_percent: float = 0.0
    memory_usage_bytes: int = 0
    memory_limit_bytes: int = 0
    current_version: str | None = None
    available_version: str | None = None
    can_update: bool = False
    can_restart: bool = True
    vmid: int | None = None
    node: str | None = None
    docker_host: str | None = None
    main_container_id: str | None = None
    components: list[HomelabComponent] = field(default_factory=list)
    extra_attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert service item to dictionary."""
        return asdict(self)


@dataclass
class HomelabSnapshot:
    """Complete snapshot of Homelab state."""

    services: dict[str, HomelabServiceItem] = field(default_factory=dict)
    pve_nodes: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "services": {k: v.to_dict() for k, v in self.services.items()},
            "pve_nodes": self.pve_nodes,
            "last_updated": self.last_updated.isoformat(),
        }
