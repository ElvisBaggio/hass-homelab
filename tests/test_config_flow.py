"""Unit tests for Homelab Config Flow and Options Flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.homelab.api import HomelabAuthError, HomelabConnectionError
from custom_components.homelab.config_flow import HomelabConfigFlow, HomelabOptionsFlow
from custom_components.homelab.const import (
    CONF_DOCKER_HOSTS,
    CONF_PVE_HOST,
    CONF_PVE_PORT,
    CONF_PVE_TOKEN_ID,
    CONF_PVE_TOKEN_SECRET,
    CONF_PVE_VERIFY_SSL,
    CONF_SCAN_INTERVAL,
)


@pytest.mark.asyncio
async def test_config_flow_show_form() -> None:
    """Test initial display of config flow form."""
    flow = HomelabConfigFlow()
    result = await flow.async_step_user(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_config_flow_success() -> None:
    """Test successful config flow submission."""
    flow = HomelabConfigFlow()
    user_input = {
        CONF_PVE_HOST: "192.168.1.9",
        CONF_PVE_PORT: 8006,
        CONF_PVE_TOKEN_ID: "root@pam!ha",
        CONF_PVE_TOKEN_SECRET: "my-secret",
        CONF_PVE_VERIFY_SSL: False,
        CONF_DOCKER_HOSTS: "http://192.168.1.193:2375, http://192.168.1.107:2375",
    }

    with patch(
        "custom_components.homelab.api.HomelabApiClient.async_validate_connection",
        new_callable=AsyncMock,
    ) as mock_validate:
        mock_validate.return_value = True
        result = await flow.async_step_user(user_input=user_input)

        assert result["type"] == "create_entry"
        assert result["title"] == "Homelab (192.168.1.9)"
        assert result["data"][CONF_PVE_HOST] == "192.168.1.9"
        assert result["data"][CONF_DOCKER_HOSTS] == [
            "http://192.168.1.193:2375",
            "http://192.168.1.107:2375",
        ]


@pytest.mark.asyncio
async def test_config_flow_auth_error() -> None:
    """Test auth error in config flow."""
    flow = HomelabConfigFlow()
    user_input = {
        CONF_PVE_HOST: "192.168.1.9",
        CONF_PVE_PORT: 8006,
        CONF_PVE_TOKEN_ID: "root@pam!bad",
        CONF_PVE_TOKEN_SECRET: "bad",
        CONF_PVE_VERIFY_SSL: False,
        CONF_DOCKER_HOSTS: "",
    }

    with patch(
        "custom_components.homelab.api.HomelabApiClient.async_validate_connection",
        side_effect=HomelabAuthError("Invalid token"),
    ):
        result = await flow.async_step_user(user_input=user_input)
        assert result["type"] == "form"
        assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_config_flow_connection_error() -> None:
    """Test connection error in config flow."""
    flow = HomelabConfigFlow()
    user_input = {
        CONF_PVE_HOST: "192.168.1.99",
        CONF_PVE_PORT: 8006,
        CONF_PVE_TOKEN_ID: "root@pam!ha",
        CONF_PVE_TOKEN_SECRET: "sec",
        CONF_PVE_VERIFY_SSL: False,
        CONF_DOCKER_HOSTS: "",
    }

    with patch(
        "custom_components.homelab.api.HomelabApiClient.async_validate_connection",
        side_effect=HomelabConnectionError("Connection timeout"),
    ):
        result = await flow.async_step_user(user_input=user_input)
        assert result["type"] == "form"
        assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_options_flow_success(mock_config_entry) -> None:
    """Test options flow update."""
    options_flow = HomelabOptionsFlow(mock_config_entry)

    # Show form
    result = await options_flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    # Submit update
    update_input = {
        CONF_SCAN_INTERVAL: 60,
        CONF_DOCKER_HOSTS: "http://192.168.1.193:2375",
    }
    result2 = await options_flow.async_step_init(user_input=update_input)
    assert result2["type"] == "create_entry"
    assert result2["data"][CONF_SCAN_INTERVAL] == 60
    assert result2["data"][CONF_DOCKER_HOSTS] == ["http://192.168.1.193:2375"]
