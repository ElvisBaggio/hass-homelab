# Arquitetura — hass-homelab

## Visão Geral
A integração `hass-homelab` implementa o padrão arquitetural de Custom Components do Home Assistant (inspirado na referência `equake/hass-gl-one`) para centralizar a observabilidade e o ciclo de vida dos serviços do homelab em dispositivos nativos no Home Assistant.

## Fluxo de Dados e Componentes

```
┌────────────────────────────────────────────────────────┐
│                     Home Assistant                     │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │           HomelabDataUpdateCoordinator         │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │                            │
│         ┌─────────────────┼─────────────────┐          │
│         ▼                 ▼                 ▼          │
│   binary_sensor        sensor            update        │
│   (status on/off)     (uptime/cpu)    (image tags)     │
│                           │                            │
│                           ▼                            │
│                         button                         │
│                    (restart seguro)                    │
└───────────────────────────┬────────────────────────────┘
                            │ aiohttp (assíncrono)
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
┌───────────────────┐                 ┌──────────────────┐
│  Proxmox VE API   │                 │ Docker Socket    │
│  (Token Auth)     │                 │ Proxy (HTTP)     │
│  LXC 100..112     │                 │ LXC 107 / Stacks │
└───────────────────┘                 └──────────────────┘
```

## Diretrizes de Design
1. **Zero Polling Bloqueante:** Toda a comunicação é feita de forma não-bloqueante no event loop do Home Assistant usando `aiohttp`.
2. **Separação de Falhas:**
   - Container/LXC parado propositalmente: `binary_sensor` = `off`, `device` = `available`.
   - Host Proxmox ou Docker Socket inacessível: `binary_sensor` = `unavailable`, `device` = `unavailable`.
3. **Agrupamento Semântico:** Stacks Compose (ex: Immich Server + Postgres + Redis) são agrupadas no dispositivo `Immich`, evitando poluição de entidades soltas no Home Assistant.
4. **Segurança e Redação:** Tokens de API e senhas são automaticamente mascarados nas saídas de diagnóstico (`diagnostics.py`).
