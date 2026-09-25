# AGENTS.md — hass-homelab

> Contexto e regras operacionais para o desenvolvimento da integração `hass-homelab`.

## Visão Geral
Integração customizada para Home Assistant (`custom_components/homelab`) para monitoramento assíncrono e controle seguro de containers Docker e nós Proxmox VE no homelab.

## Diretrizes Técnicas
- **Linguagem:** Python 3.12+ com tipagem estrita (`mypy` / `ruff`).
- **Arquitetura:** Baseada no padrão `hass-gl-one` (ConfigFlow, DataUpdateCoordinator assíncrono, Device por serviço, plataformas `binary_sensor`, `sensor`, `update`, `button`).
- **Comunicação:** Assíncrona via `aiohttp` direto na API Proxmox VE (API Token) e Docker Socket Proxy (HTTP local). Zero chamadas de subprocess/SSH bloqueantes.
- **Segurança:** Segredos e tokens nunca devem ser expostos em logs ou diagnósticos. Ações destrutivas não são expostas ao HA sem autorização estrita (`safe_by_ha`).
- **Testes:** Cobertura abrangente com `pytest-homeassistant-custom-component` e `aioresponses`.

## Convenções de Git e Assinatura
- Commits seguem conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`).
- Branches de desenvolvimento: `hermes/<feature>`.
- `main` apenas para releases e trabalho validado por testes.
