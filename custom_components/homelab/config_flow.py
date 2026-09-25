"""Config Flow and Options Flow for Homelab integration."""

from __future__ import annotations

import logging
from typing import Any

from .api import HomelabApiClient, HomelabAuthError, HomelabConnectionError
from .const import (
    CONF_DOCKER_HOSTS,
    CONF_PVE_HOST,
    CONF_PVE_PORT,
    CONF_PVE_TOKEN_ID,
    CONF_PVE_TOKEN_SECRET,
    CONF_PVE_VERIFY_SSL,
    CONF_SCAN_INTERVAL,
    DEFAULT_PVE_PORT,
    DEFAULT_PVE_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def parse_docker_hosts(hosts_raw: Any) -> list[str]:
    """Parse comma/newline separated string or list of docker hosts."""
    if isinstance(hosts_raw, list):
        return [h.strip() for h in hosts_raw if h and h.strip()]
    if isinstance(hosts_raw, str):
        parts = [p.strip() for p in hosts_raw.replace("\n", ",").split(",") if p.strip()]
        return parts
    return []


class HomelabConfigFlow:
    """Handle a config flow for Homelab."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize config flow."""
        self.context: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pve_host = user_input.get(CONF_PVE_HOST, "").strip()
            pve_port = int(user_input.get(CONF_PVE_PORT, DEFAULT_PVE_PORT))
            pve_token_id = user_input.get(CONF_PVE_TOKEN_ID)
            pve_token_secret = user_input.get(CONF_PVE_TOKEN_SECRET)
            pve_verify_ssl = bool(user_input.get(CONF_PVE_VERIFY_SSL, DEFAULT_PVE_VERIFY_SSL))
            docker_hosts = parse_docker_hosts(user_input.get(CONF_DOCKER_HOSTS, ""))

            client = HomelabApiClient(
                pve_host=pve_host,
                pve_port=pve_port,
                pve_token_id=pve_token_id,
                pve_token_secret=pve_token_secret,
                pve_verify_ssl=pve_verify_ssl,
                docker_hosts=docker_hosts,
            )

            try:
                await client.async_validate_connection()
            except HomelabAuthError:
                errors["base"] = "invalid_auth"
            except HomelabConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception in config flow")
                errors["base"] = "unknown"
            else:
                return {
                    "type": "create_entry",
                    "title": f"Homelab ({pve_host})",
                    "data": {
                        CONF_PVE_HOST: pve_host,
                        CONF_PVE_PORT: pve_port,
                        CONF_PVE_TOKEN_ID: pve_token_id,
                        CONF_PVE_TOKEN_SECRET: pve_token_secret,
                        CONF_PVE_VERIFY_SSL: pve_verify_ssl,
                        CONF_DOCKER_HOSTS: docker_hosts,
                    },
                }

        return {
            "type": "form",
            "step_id": "user",
            "data_schema": {
                CONF_PVE_HOST: str,
                CONF_PVE_PORT: int,
                CONF_PVE_TOKEN_ID: str,
                CONF_PVE_TOKEN_SECRET: str,
                CONF_PVE_VERIFY_SSL: bool,
                CONF_DOCKER_HOSTS: str,
            },
            "errors": errors,
        }

    @staticmethod
    def async_get_options_flow(config_entry: Any) -> HomelabOptionsFlow:
        """Get options flow handler."""
        return HomelabOptionsFlow(config_entry)


class HomelabOptionsFlow:
    """Handle options flow for Homelab."""

    def __init__(self, config_entry: Any) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Manage options."""
        if user_input is not None:
            scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
            docker_hosts = parse_docker_hosts(user_input.get(CONF_DOCKER_HOSTS, []))

            return {
                "type": "create_entry",
                "title": "",
                "data": {
                    CONF_SCAN_INTERVAL: scan_interval,
                    CONF_DOCKER_HOSTS: docker_hosts,
                },
            }

        current_options = getattr(self.config_entry, "options", {})
        current_data = getattr(self.config_entry, "data", {})

        current_hosts = current_options.get(
            CONF_DOCKER_HOSTS, current_data.get(CONF_DOCKER_HOSTS, [])
        )
        if isinstance(current_hosts, list):
            current_hosts_str = ", ".join(current_hosts)
        else:
            current_hosts_str = str(current_hosts)

        return {
            "type": "form",
            "step_id": "init",
            "data_schema": {
                CONF_SCAN_INTERVAL: current_options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
                CONF_DOCKER_HOSTS: current_hosts_str,
            },
            "errors": {},
        }
