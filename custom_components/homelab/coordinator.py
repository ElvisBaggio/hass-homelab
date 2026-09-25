"""DataUpdateCoordinator for Homelab integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from .api import HomelabApiClient, HomelabApiError
from .const import STATE_RUNNING, STATE_STOPPED, STATE_UNAVAILABLE
from .models import HomelabComponent, HomelabServiceItem, HomelabSnapshot

_LOGGER = logging.getLogger(__name__)

# Known homelab service registry metadata
KNOWN_SERVICES: dict[str, dict[str, Any]] = {
    "pve": {"name": "Proxmox VE", "group": "Infraestrutura", "icon": "mdi:server", "kind": "host"},
    "homeassistant": {
        "name": "Home Assistant",
        "group": "Casa & automação",
        "icon": "mdi:home-assistant",
        "kind": "guest",
    },
    "hermes": {
        "name": "Hermes",
        "group": "IA & automação",
        "icon": "mdi:robot-outline",
        "kind": "guest",
    },
    "reminder-bot": {
        "name": "Reminder Bot",
        "group": "IA & automação",
        "icon": "mdi:bell-outline",
        "kind": "systemd",
    },
    "cloudflared": {
        "name": "Cloudflare Tunnel",
        "group": "Infraestrutura",
        "icon": "mdi:cloud-lock-outline",
        "kind": "systemd",
    },
    "immich": {
        "name": "Immich",
        "group": "Casa & dados",
        "icon": "mdi:image-multiple-outline",
        "kind": "compose",
        "can_update": True,
    },
    "pihole": {
        "name": "Pi-hole",
        "group": "Infraestrutura",
        "icon": "mdi:pi-hole",
        "kind": "compose",
        "can_update": True,
    },
    "nextcloud": {
        "name": "Nextcloud AIO",
        "group": "Casa & dados",
        "icon": "mdi:cloud-outline",
        "kind": "compose",
        "can_update": True,
    },
    "wallos": {
        "name": "Wallos",
        "group": "Casa & dados",
        "icon": "mdi:wallet-outline",
        "kind": "compose",
        "can_update": True,
    },
    "financeiro-dashboard": {
        "name": "Financeiro Dashboard",
        "group": "Apps",
        "icon": "mdi:finance",
        "kind": "compose",
    },
    "radar-mgc": {
        "name": "Radar MGC",
        "group": "Apps",
        "icon": "mdi:radar",
        "kind": "compose",
    },
    "casa-24": {
        "name": "Casa 24",
        "group": "Apps",
        "icon": "mdi:home-edit-outline",
        "kind": "compose",
    },
    "guitarrig": {
        "name": "GuitarRig",
        "group": "Apps",
        "icon": "mdi:guitar-electric",
        "kind": "compose",
        "can_update": True,
    },
    "portainer": {
        "name": "Portainer",
        "group": "Infraestrutura",
        "icon": "mdi:docker",
        "kind": "container",
    },
    "caddy": {
        "name": "Caddy",
        "group": "Infraestrutura",
        "icon": "mdi:lock-outline",
        "kind": "guest",
    },
    "honcho": {
        "name": "Honcho",
        "group": "IA & automação",
        "icon": "mdi:brain",
        "kind": "compose",
    },
    "omniroute": {
        "name": "OmniRoute",
        "group": "IA & automação",
        "icon": "mdi:transit-connection-variant",
        "kind": "guest",
    },
}


class HomelabDataUpdateCoordinator:
    """Class to manage fetching Homelab data from PVE and Docker."""

    def __init__(
        self,
        hass: Any,
        client: HomelabApiClient,
        update_interval: int = 30,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.client = client
        self.update_interval = timedelta(seconds=update_interval)
        self.data: HomelabSnapshot = HomelabSnapshot()
        self._listeners: list[Any] = []

    async def async_refresh_data(self) -> HomelabSnapshot:
        """Fetch latest data from all configured endpoints and reconcile."""
        services: dict[str, HomelabServiceItem] = {}
        pve_nodes: list[dict[str, Any]] = []

        # 1. Fetch Proxmox VE resources
        try:
            pve_resources = await self.client.async_get_pve_resources()
            for res in pve_resources:
                res_type = res.get("type")
                if res_type == "node":
                    pve_nodes.append(res)
                elif res_type in ("lxc", "qemu"):
                    vmid = res.get("vmid")
                    raw_name = res.get("name", f"guest-{vmid}")
                    service_id = raw_name.lower().replace("_", "-")
                    status_raw = res.get("status", "unknown")
                    state = STATE_RUNNING if status_raw == "running" else STATE_STOPPED

                    meta = KNOWN_SERVICES.get(service_id, {})
                    services[service_id] = HomelabServiceItem(
                        service_id=service_id,
                        name=meta.get("name", raw_name),
                        group=meta.get("group", "Infraestrutura"),
                        icon=meta.get("icon", "mdi:server"),
                        kind="guest",
                        state=state,
                        uptime=int(res.get("uptime", 0)),
                        cpu_percent=round(float(res.get("cpu", 0.0)) * 100, 2),
                        memory_usage_bytes=int(res.get("mem", 0)),
                        memory_limit_bytes=int(res.get("maxmem", 0)),
                        vmid=vmid,
                        node=res.get("node"),
                        can_restart=True,
                    )
        except HomelabApiError as err:
            _LOGGER.warning("Failed to fetch PVE resources: %s", err)

        # 2. Fetch Docker containers from configured Docker hosts
        for docker_host in self.client.docker_hosts:
            try:
                containers = await self.client.async_get_docker_containers(docker_host)
                # Group containers by compose project or individual container
                compose_groups: dict[str, list[dict[str, Any]]] = {}

                for c in containers:
                    labels = c.get("Labels", {})
                    project = labels.get("com.docker.compose.project")
                    if project:
                        compose_groups.setdefault(project.lower(), []).append(c)
                    else:
                        # Standalone container
                        names = c.get("Names", ["/unknown"])
                        c_name = names[0].lstrip("/").lower()
                        compose_groups.setdefault(c_name, []).append(c)

                for group_id, c_list in compose_groups.items():
                    # Determine service item
                    meta = KNOWN_SERVICES.get(group_id, {})
                    components: list[HomelabComponent] = []
                    is_running = any(c.get("State") == "running" for c in c_list)
                    state = STATE_RUNNING if is_running else STATE_STOPPED

                    main_container = c_list[0]
                    for c in c_list:
                        names = c.get("Names", ["/unknown"])
                        clean_name = names[0].lstrip("/")
                        c_state = c.get("State", "unknown")
                        components.append(
                            HomelabComponent(
                                component_id=c.get("Id", "")[:12],
                                name=clean_name,
                                image=c.get("Image", ""),
                                state=c_state,
                                status=c.get("Status", ""),
                                host=docker_host,
                                container_id=c.get("Id"),
                            )
                        )

                    image = main_container.get("Image", "")
                    current_version = image.split(":")[-1] if ":" in image else image

                    has_compose_lbl = bool(
                        c_list and c_list[0].get("Labels", {}).get("com.docker.compose.project")
                    )
                    is_compose = has_compose_lbl or meta.get("kind") == "compose"

                    services[group_id] = HomelabServiceItem(
                        service_id=group_id,
                        name=meta.get("name", group_id.capitalize()),
                        group=meta.get("group", "Casa & dados"),
                        icon=meta.get("icon", "mdi:docker"),
                        kind="compose" if is_compose else "container",
                        state=state,
                        current_version=current_version,
                        can_update=meta.get("can_update", False),
                        can_restart=True,
                        docker_host=docker_host,
                        main_container_id=main_container.get("Id"),
                        components=components,
                    )
            except HomelabApiError as err:
                _LOGGER.warning("Failed to fetch Docker containers from %s: %s", docker_host, err)
                # Mark as unavailable if previously registered
                for _s_id, s_item in list(services.items()):
                    if s_item.docker_host == docker_host:
                        s_item.state = STATE_UNAVAILABLE

        self.data = HomelabSnapshot(
            services=services,
            pve_nodes=pve_nodes,
            last_updated=datetime.now(UTC),
        )
        return self.data
