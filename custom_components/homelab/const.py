"""Constants for the Homelab integration."""

from typing import Final

DOMAIN: Final = "homelab"

# Configuration keys
CONF_PVE_HOST: Final = "pve_host"
CONF_PVE_PORT: Final = "pve_port"
CONF_PVE_TOKEN_ID: Final = "pve_token_id"
CONF_PVE_TOKEN_SECRET: Final = "pve_token_secret"
CONF_PVE_VERIFY_SSL: Final = "pve_verify_ssl"
CONF_DOCKER_HOSTS: Final = "docker_hosts"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_PVE_PORT: Final = 8006
DEFAULT_PVE_VERIFY_SSL: Final = False
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# Platforms
PLATFORMS: Final = ["binary_sensor", "sensor", "update", "button"]

# Service states
STATE_RUNNING: Final = "running"
STATE_STOPPED: Final = "stopped"
STATE_UNAVAILABLE: Final = "unavailable"
