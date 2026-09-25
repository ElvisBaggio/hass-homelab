# hass-homelab Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a integração personalizada para Home Assistant (`custom_components/homelab`) baseada no padrão arquitetural do `hass-gl-one`, fornecendo monitoramento assíncrono e controle granular para serviços Proxmox VE e containers Docker do homelab.

**Architecture:** A integração implementa um `DataUpdateCoordinator` central que se comunica de forma assíncrona com a API REST do Proxmox VE e o Docker Socket Proxy (HTTP). Ela mapeia os serviços do homelab em `Devices` dedicados no Home Assistant, expondo entidades de `binary_sensor` (status operacional), `sensor` (uptime/recursos), `update` (notificação de imagens Docker) e `button` (restart seguro).

**Tech Stack:** Python 3.12+, Home Assistant Core (Custom Component API), `aiohttp`, `pytest-homeassistant-custom-component`, `pytest-asyncio`, `ruff`, GitHub Actions (hassfest/pytest).

**Spec:** Padrão arquitetural `equake/hass-gl-one`, catálogo de serviços homelab (`services.registry.json`) e decisões da sessão Grill Me (Setup via UI, 1 dispositivo por serviço, APIs diretas sem SSH root).

## Global Constraints

- Compatibilidade com Home Assistant 2026.1+.
- Totalmente assíncrono: chamadas de rede via `aiohttp` e `asyncio`, sem I/O bloqueante no event loop.
- Tratamento de falhas determinístico: diferenciar serviço parado (`state = off`) de host inacessível (`state = unavailable`).
- Redação de segredos no `diagnostics.py` e logs sanitizados.
- Padrão de código `ruff` e 100% de passagem nos testes unitários `pytest`.

---

### Task 1: Scaffolding do Repositório, Dependências e Setup de Testes

**Files:**
- Create: `pyproject.toml`
- Create: `hacs.json`
- Create: `custom_components/homelab/manifest.json`
- Create: `custom_components/homelab/__init__.py`
- Create: `requirements_test.txt`
- Create: `tests/conftest.py`
- Create: `tests/test_init.py`

**Interfaces:**
- Produces: `async_setup_entry` e `async_unload_entry` no `custom_components/homelab/__init__.py`.

- [ ] **Step 1: Criar `pyproject.toml`, `hacs.json` e `requirements_test.txt`**

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
norecursedirs = [".git"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "ASYNC"]
```

```json
// hacs.json
{
  "name": "Homelab Control & Monitoring",
  "render_readme": true,
  "homeassistant": "2026.1.0"
}
```

```text
# requirements_test.txt
pytest-homeassistant-custom-component>=0.13.0
pytest-asyncio>=0.23.0
pytest>=8.0.0
ruff>=0.5.0
```

- [ ] **Step 2: Criar `custom_components/homelab/manifest.json`**

```json
{
  "domain": "homelab",
  "name": "Homelab",
  "codeowners": ["@ElvisBaggio"],
  "config_flow": true,
  "documentation": "https://github.com/ElvisBaggio/hass-homelab",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/ElvisBaggio/hass-homelab/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

- [ ] **Step 3: Escrever teste de ciclo de vida básico em `tests/test_init.py`**

```python
"""Test integration setup and unload."""
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homelab.const import DOMAIN


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Test setting up and unloading the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "pve_host": "192.168.1.9",
            "pve_token_id": "root@pam!ha",
            "pve_token_secret": "test-secret",
            "pve_verify_ssl": False,
            "docker_hosts": ["http://192.168.1.193:2375"],
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data[DOMAIN]
```

- [ ] **Step 4: Implementar `custom_components/homelab/__init__.py` e `const.py` mínimos**

```python
# custom_components/homelab/const.py
"""Constants for the Homelab integration."""
from typing import Final

DOMAIN: Final = "homelab"
CONF_PVE_HOST: Final = "pve_host"
CONF_PVE_TOKEN_ID: Final = "pve_token_id"
CONF_PVE_TOKEN_SECRET: Final = "pve_token_secret"
CONF_PVE_VERIFY_SSL: Final = "pve_verify_ssl"
CONF_DOCKER_HOSTS: Final = "docker_hosts"

DEFAULT_SCAN_INTERVAL: Final = 30
PLATFORMS: Final = ["binary_sensor", "sensor", "update", "button"]
```

```python
# custom_components/homelab/__init__.py
"""Homelab integration setup."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homelab from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"entry_data": entry.data}

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Homelab config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
```

- [ ] **Step 5: Executar testes e validar setup**

Executar: `pytest tests/test_init.py -v`

---

### Task 2: Cliente Assíncrono de API (Proxmox VE + Docker Socket Proxy)

**Files:**
- Create: `custom_components/homelab/api.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: `aiohttp.ClientSession`.
- Produces: `HomelabApiClient` com métodos `async_get_pve_nodes()`, `async_get_pve_resources()`, `async_get_docker_containers(host)`, `async_restart_docker_container(host, container_id)` e `async_reboot_pve_guest(node, guest_type, vmid)`.

- [ ] **Step 1: Escrever testes unitários para o `HomelabApiClient`**

```python
"""Tests for Homelab API client."""
import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.homelab.api import HomelabApiClient


@pytest.mark.asyncio
async def test_get_pve_resources() -> None:
    """Test fetching PVE cluster resources."""
    async with aiohttp.ClientSession() as session:
        client = HomelabApiClient(
            pve_host="192.168.1.9",
            pve_token_id="root@pam!ha",
            pve_token_secret="secret",
            pve_verify_ssl=False,
            session=session,
        )

        with aioresponses() as m:
            m.get(
                "https://192.168.1.9:8006/api2/json/cluster/resources",
                payload={"data": [{"vmid": 100, "name": "hermes", "type": "lxc", "status": "running"}]},
            )

            resources = await client.async_get_pve_resources()
            assert len(resources) == 1
            assert resources[0]["name"] == "hermes"
            assert resources[0]["status"] == "running"
```

- [ ] **Step 2: Implementar `custom_components/homelab/api.py`**

Implementar classe assíncrona robusta com tratamento de timeouts, autenticação `PVEAPIToken` e requisições para Docker Socket Proxy.

- [ ] **Step 3: Executar testes de API**

Executar: `pytest tests/test_api.py -v`

---

### Task 3: Config Flow e Options Flow (Setup via UI)

**Files:**
- Create: `custom_components/homelab/config_flow.py`
- Create: `custom_components/homelab/strings.json`
- Create: `tests/test_config_flow.py`

**Interfaces:**
- Produces: `HomelabConfigFlow` e `HomelabOptionsFlow`.

- [ ] **Step 1: Escrever testes de validação de formulário e fluxo de erro**

```python
"""Test Homelab config flow."""
from unittest.mock import patch
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.homelab.const import DOMAIN


async def test_user_form_success(hass: HomeAssistant) -> None:
    """Test successful user step in config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch("custom_components.homelab.api.HomelabApiClient.async_validate_connection", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "pve_host": "192.168.1.9",
                "pve_token_id": "root@pam!ha",
                "pve_token_secret": "my-secret",
                "pve_verify_ssl": False,
                "docker_hosts": ["http://192.168.1.193:2375"],
            },
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["title"] == "Homelab (192.168.1.9)"
```

- [ ] **Step 2: Implementar `config_flow.py` e `strings.json`**
- [ ] **Step 3: Executar testes de config flow**

Executar: `pytest tests/test_config_flow.py -v`

---

### Task 4: DataUpdateCoordinator e Diagnósticos

**Files:**
- Create: `custom_components/homelab/coordinator.py`
- Create: `custom_components/homelab/models.py`
- Create: `custom_components/homelab/diagnostics.py`
- Create: `tests/test_coordinator.py`

**Interfaces:**
- Produces: `HomelabDataUpdateCoordinator` contendo `HomelabSnapshot` (serviços reconciliados do PVE + Docker).
- Produces: `async_get_config_entry_diagnostics` com redação de tokens e endereços privados.

- [ ] **Step 1: Escrever teste de agregação do coordinator**
- [ ] **Step 2: Implementar `coordinator.py` com polling seguro assíncrono**
- [ ] **Step 3: Implementar `diagnostics.py`**
- [ ] **Step 4: Executar testes do coordinator**

Executar: `pytest tests/test_coordinator.py -v`

---

### Task 5: Plataformas `binary_sensor` e `sensor` (Dispositivos por Serviço)

**Files:**
- Create: `custom_components/homelab/entity.py`
- Create: `custom_components/homelab/binary_sensor.py`
- Create: `custom_components/homelab/sensor.py`
- Create: `tests/test_sensors.py`

**Interfaces:**
- Produces: `HomelabEntity` (base com `device_info`), `HomelabBinarySensor` e `HomelabSensor`.

- [ ] **Step 1: Escrever testes para as entidades de monitoramento**
- [ ] **Step 2: Implementar classes base e plataformas**
- [ ] **Step 3: Executar testes de sensores**

Executar: `pytest tests/test_sensors.py -v`

---

### Task 6: Plataformas `update` e `button` (Ações de Controle Seguro)

**Files:**
- Create: `custom_components/homelab/update.py`
- Create: `custom_components/homelab/button.py`
- Create: `tests/test_controls.py`

**Interfaces:**
- Produces: `HomelabUpdateEntity` (para apps com tag/update disponível) e `HomelabRestartButton` (para restart atômico).

- [ ] **Step 1: Escrever testes para botões e updates**
- [ ] **Step 2: Implementar plataformas com checagem de permissão `safe_by_ha`**
- [ ] **Step 3: Executar testes de controle**

Executar: `pytest tests/test_controls.py -v`

---

### Task 7: CI Workflows, Documentação e Validação Final

**Files:**
- Create: `.github/workflows/validate.yml`
- Create: `README.md`
- Create: `HANDOFF.md`

- [ ] **Step 1: Configurar workflow de validação do GitHub (`hassfest` + `ruff` + `pytest`)**
- [ ] **Step 2: Criar README.md completo com guia de instalação HACS e configuração**
- [ ] **Step 3: Executar suíte completa de testes e linter**

Executar:
```bash
ruff check .
pytest --cov=custom_components.homelab tests/
```
