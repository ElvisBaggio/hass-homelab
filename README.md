# hass-homelab

[![Validate Integration](https://github.com/ElvisBaggio/hass-homelab/actions/workflows/validate.yml/badge.svg)](https://github.com/ElvisBaggio/hass-homelab/actions/workflows/validate.yml)
[![HACS Default](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Integração personalizada para o **Home Assistant** que centraliza o monitoramento assíncrono e controle granular dos serviços do Homelab (Proxmox VE + Docker Stacks).

---

## Recursos

- **1 Dispositivo por Serviço:** Cada aplicação (Immich, Nextcloud, Wallos, Pi-hole, Caddy, Hermes, etc.) vira um dispositivo dedicado com área sugerida automática.
- **Entidades Nativas:**
  - `binary_sensor.<id>_status`: Status operacional (`on` = rodando, `off` = parado, `unavailable` = host offline).
  - `sensor.<id>_uptime`, `sensor.<id>_cpu_usage`, `sensor.<id>_memory`: Métricas de consumo e tempo de atividade.
  - `update.<id>`: Notificação de novas imagens e tags Docker para serviços seguros (`safe_by_ha`).
  - `button.<id>_restart`: Botão de reinício atômico (reboot de LXC/VM ou restart de container individual).
- **Descoberta Dinâmica:** Mapeia automaticamente containers Docker standalone, projetos Docker Compose e guests Proxmox VE.
- **Segurança:** Autenticação via PVE API Token e Docker Socket Proxy HTTP (sem SSH root ou sockets expostos). Redação automática de credenciais em diagnósticos.

---

## Instalação

### Via HACS (Recomendado)
1. Abra o **HACS** no Home Assistant.
2. Clique no menu de 3 pontos no canto superior direito e selecione **Custom repositories**.
3. Adicione a URL `https://github.com/ElvisBaggio/hass-homelab` com a categoria **Integration**.
4. Procure por **Homelab** no HACS e clique em **Download**.
5. Reinicie o Home Assistant.

### Manual
1. Copie a pasta `custom_components/homelab` para o diretório `custom_components/` da sua instalação do Home Assistant.
2. Reinicie o Home Assistant.

---

## Configuração

1. No Home Assistant, vá em **Configurações** → **Dispositivos & Serviços** → **Adicionar Integração**.
2. Procure por **Homelab**.
3. Preencha os dados de conexão:
   - **Proxmox Host:** IP ou hostname do host Proxmox (ex: `192.168.1.9`).
   - **PVE API Token ID:** Token ID configurado no PVE (ex: `root@pam!ha`).
   - **PVE API Token Secret:** Token Secret gerado no PVE.
   - **Docker Socket Proxies:** URLs dos proxies Docker HTTP (separadas por vírgula, ex: `http://192.168.1.193:2375`).
   - **Verificar SSL:** Desmarque se o Proxmox usar certificado auto-assinado.

---

## Testes e Desenvolvimento

O repositório inclui suíte completa de testes unitários e linter:

```bash
# Instalar dependências de teste
pip install -r requirements_test.txt

# Executar linter
ruff check .

# Executar suíte de testes
pytest -v
```

---

## Licença

MIT — Elvis Baggio.
