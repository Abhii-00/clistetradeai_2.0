# ClisteTrade AI Frontend

Professional React TypeScript dashboard for the autonomous multi-agent financial intelligence workflow.

## Stack

- React 18 with TypeScript
- Vite
- Apache ECharts for candlestick, EMA, RSI, MACD, volume, zoom, pan, and tooltips
- Framer Motion for workflow-stage transitions
- Lucide React for terminal-style interface icons
- CSS modules through `src/styles/global.css`

## Run

```bash
cd frontend
npm install
npm run dev
```

The app expects backend APIs at `http://127.0.0.1:8000` through the Vite proxy.

Start the backend from the project root:

```bash
uv run python -m clistetradeai.api_server
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

## Backend Endpoint Contract

The frontend posts user selections to:

```http
POST /analyze-market
```

Request body:

```json
{
  "asset_type": "stock",
  "ticker": "AAPL",
  "trading_style": "swing",
  "risk_tolerance": "moderate"
}
```

Expected response:

```json
{
  "requestId": "run-id",
  "recommendation": {
    "label": "Constructive Setup",
    "confidence": 72,
    "explanation": "Final market recommendation narrative"
  },
  "chartData": [],
  "workflow": [],
  "technical": {},
  "sentiment": {},
  "risk": {}
}
```

Additional planned endpoints consumed by the service layer:

- `GET /workflow-status/{requestId}`
- `GET /chart-data/{requestId}`
- `GET /technical-output/{requestId}`
- `GET /sentiment-output/{requestId}`
- `GET /risk-output/{requestId}`

If `/analyze-market` is unavailable, the frontend now shows a visible backend workflow error instead of mock market data.
