# Tesla Inventory Monitor

Agente que monitoriza o inventário online da Tesla (a mesma API usada pela
página https://www.tesla.com/pt_PT/inventory/new/my) e envia uma notificação
para o Telegram e/ou WhatsApp assim que aparecer uma unidade nova que
corresponda às características que definires (modelo, trim, cor, interior,
jantes, preço, Autopilot/FSD, etc.).

> ⚠️ A API de inventário da Tesla não é oficial nem documentada — é a mesma
> que o site usa internamente. Pode mudar sem aviso. Se os filtros deixarem
> de funcionar, usa `python main.py --dump-raw dump.json` para veres a
> resposta bruta e ajustares `tesla_monitor/filters.py` aos nomes de campos
> atuais.

## Como funciona

1. `main.py` lê `config.yaml` (critérios de pesquisa + canais de notificação).
2. Consulta a API de inventário da Tesla para o modelo/mercado configurado.
3. Filtra os veículos devolvidos pelos teus critérios (`filters:` no config).
4. Compara com `state/seen_vehicles.json` para saber quais são **novos**.
5. Envia uma mensagem por cada veículo novo que corresponda aos critérios,
   via Telegram e/ou WhatsApp.
6. Guarda o novo estado para não notificar o mesmo veículo duas vezes.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita o `.env` com as tuas credenciais (ver instruções dentro do próprio
ficheiro para Telegram e WhatsApp) e o `config.yaml` com as características
do carro que procuras.

## Configurar o Telegram (recomendado, mais simples)

1. No Telegram, fala com **@BotFather**, envia `/newbot` e segue as
   instruções. Vais receber um `TELEGRAM_BOT_TOKEN`.
2. Envia qualquer mensagem ao teu novo bot (para "abrires" a conversa).
3. Abre no browser:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   e copia o valor de `message.chat.id` — é o teu `TELEGRAM_CHAT_ID`.
4. Preenche ambos no `.env`.

## Configurar o WhatsApp (opcional, via CallMeBot)

Usa o serviço gratuito [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/)
para notificações pessoais de WhatsApp, sem precisar de conta Twilio/Meta
Business:

1. Adiciona o número `+34 644 59 71 65` aos teus contactos.
2. Envia-lhe a mensagem exata: `I allow callmebot to send me messages`.
3. Vais receber uma `apikey` por WhatsApp — coloca-a no `.env` junto com o
   teu número (`WHATSAPP_PHONE`, formato internacional, ex: `351912345678`).
4. Em `config.yaml`, muda `notify.whatsapp_callmebot.enabled` para `true`.

## Definir os critérios de pesquisa

No `config.yaml`, a secção `tesla:` define o que procurar (modelo, mercado,
código postal, novo/usado), e `filters:` define as características
específicas da unidade. Exemplos:

```yaml
tesla:
  model: my        # my=Model Y, m3=Model 3, ms=Model S, mx=Model X
  condition: new
  market: PT
  zip: "3030-325"

filters:
  price_max: 45000
  trim_contains: ["Long Range"]
  exterior_contains: ["Pearl White", "Deep Blue Metallic"]
  interior_contains: ["All Black"]
  wheels_contains: []
  autopilot_contains: []
```

Cada lista funciona como "OU" (basta corresponder a um termo); deixa a lista
vazia (`[]`) para não filtrar por essa característica. As comparações são
por substring e não distinguem maiúsculas/minúsculas, usando os nomes reais
das opções devolvidos pela Tesla (ex.: "Pearl White Multi-Coat").

## Testar

```bash
# Testa se as notificações estão bem configuradas
python main.py --test-notify

# Corre uma verificação única
python main.py --once

# Corre uma verificação única e envia também uma mensagem "sem unidades
# disponíveis" se não houver nada a corresponder aos critérios (útil para
# confirmar que o agente está mesmo a correr, mesmo sem stock disponível)
python main.py --once --notify-empty

# Corre em loop contínuo (usa polling.interval_seconds do config.yaml)
python main.py

# Inspecionar a resposta bruta da API (debug)
python main.py --dump-raw dump.json
```

## Correr continuamente

Tens três opções principais:

### 1. GitHub Actions (recomendado — não precisas de deixar nada ligado)

Este repositório já inclui `.github/workflows/tesla-monitor.yml`, que corre
a cada 15 minutos.

1. Vai a **Settings → Secrets and variables → Actions** no GitHub e cria os
   secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (e, se usares WhatsApp,
   `WHATSAPP_PHONE` e `CALLMEBOT_APIKEY`).
2. Garante que o workflow tem permissão de escrita (**Settings → Actions →
   General → Workflow permissions → Read and write permissions**), porque ele
   faz commit do `state/seen_vehicles.json` a cada verificação para não
   repetir notificações.
3. Pronto — corre automaticamente. Podes também disparar manualmente em
   **Actions → Tesla Inventory Monitor → Run workflow**.

### 2. Cron local / servidor próprio (Raspberry Pi, NAS, VPS, etc.)

```cron
*/10 * * * * cd /caminho/para/Agente && /caminho/para/.venv/bin/python main.py --once >> monitor.log 2>&1
```

### 3. Loop contínuo (systemd, Docker, tmux, etc.)

```bash
python main.py   # fica a correr, verificando a cada polling.interval_seconds
```

## Limitações conhecidas

- A Tesla pode limitar (rate-limit) ou bloquear pedidos muito frequentes;
  não configures um intervalo muito baixo (recomendado ≥ 5 minutos).
- A estrutura da resposta da API pode variar ligeiramente por mercado; usa
  `--dump-raw` para confirmares os campos exatos disponíveis para o teu
  modelo/mercado antes de afinar os filtros.
- Isto não faz nenhuma reserva automática — apenas notifica; a reserva
  continua a ser feita manualmente por ti no site da Tesla.
