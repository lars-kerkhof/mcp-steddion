# Steddion Energy MCP Server

MCP-server voor de Nederlandse energiemarkt: day-ahead prijzen, onbalansprijzen, weersvoorspellingen en BESS-businesscases.

## Tools

| Tool | Beschrijving |
|------|-------------|
| `get_day_ahead_prices` | Uurlijkse day-ahead prijzen (EUR/MWh) via ENTSO-E |
| `get_imbalance_prices` | Kwartierlijkse onbalansprijzen via TenneT |
| `get_weather_forecast` | Wind, zon (GHI) en temperatuur via Open-Meteo |
| `calculate_bess_business_case` | Day-ahead arbitrage-opbrengst voor een batterij |

## Installatie & draaien

### Vereisten

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Installeren

```bash
git clone https://github.com/lars-kerkhof/mcp-steddion.git
cd mcp-steddion
uv sync
```

### Environment variabelen

```bash
cp .env.example .env
# Bewerk .env en vul je ENTSO-E API token in (optioneel — zonder token draait de server op mock-data)
```

| Variabele | Vereist | Beschrijving |
|-----------|---------|-------------|
| `ENTSOE_API_TOKEN` | Nee | Token van [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/). Zonder token worden realistische mock-data gebruikt. |
| `HOST` | Nee | Server host (default: `0.0.0.0`) |
| `PORT` | Nee | Server port (default: `8000`) |

### Server starten

```bash
uv run python -m steddion_mcp
```

De server draait dan op `http://localhost:8000/mcp`.

### Tests draaien

```bash
uv run pytest
```

## Koppelen aan ChatGPT (Developer Mode)

ChatGPT ondersteunt geen lokale stdio-servers. Je moet de server via HTTPS bereikbaar maken.

### Stap 1: Server starten

```bash
uv run python -m steddion_mcp
```

### Stap 2: Tunnel opzetten

Kies een van:

**Cloudflared (aanbevolen):**
```bash
cloudflared tunnel --url http://localhost:8000
```

**ngrok:**
```bash
ngrok http 8000
```

Je krijgt een HTTPS-URL, bijvoorbeeld `https://abc123.trycloudflare.com`.

### Stap 3: Connector toevoegen in ChatGPT

1. Open ChatGPT → Settings → Apps/Connectors
2. Schakel **Developer Mode** in
3. Klik **Add Connector** → Custom
4. Vul de URL in: `https://<jouw-tunnel-url>/mcp`
5. Sla op — de tools verschijnen nu in ChatGPT

## Architectuur

```
steddion_mcp/
├── server.py      # FastMCP server, tool-registraties
├── entsoe.py      # ENTSO-E day-ahead prijzen
├── tennet.py      # TenneT onbalansprijzen
├── weather.py     # Open-Meteo weersdata
├── bess.py        # BESS businesscase calculator
├── models.py      # Pydantic response-modellen
├── mock_data.py   # Realistische mock-data generators
└── __main__.py    # Entry point
```

## Mock-data

Alle tools vallen automatisch terug op deterministische mock-data wanneer:
- De `ENTSOE_API_TOKEN` ontbreekt (day-ahead prijzen)
- De TenneT API niet bereikbaar is (onbalansprijzen)
- De Open-Meteo API niet bereikbaar is (weer)

Mock-data is herkenbaar aan het veld `source: "mock"` in de response.
