# ClisteTrade AI — Autonomous Multi-Agent Financial Intelligence Terminal

An end-to-end system that transforms user market selections into explainable technical, sentiment, and risk-aware trade recommendations using CrewAI agents, deterministic analysis engines, and an interactive React dashboard.

## Architecture

```
Frontend (React + Vite)                    Backend (Python + CrewAI)
─────────────────────────                  ──────────────────────────
ConfigPanel                                 trading_config.py (dynamic params)
  │ POST /analyze-market                     ├── MarketDataTool (yfinance)
  ▼                                         ├── IndicatorTool (pandas_ta)
API server (background thread)              ├── MarketStateEngine (rule-based)
  │                                         ├── SentimentDataFetcherTool
  ├── GET /workflow-status/:id  ◄── polls  │   (NewsAPI / Finnhub)
  │   (every 400ms)                         ├── SentimentCompressorTool (OpenAI)
  ├── GET /analysis-result/:id  ◄── fetch  └── CrewAI Agents (4 sequential)
  │                                             Technical → Sentiment → Risk → Decision
WorkflowTimeline  ◄── stage transitions
AgentOutputExplorer ◄── structured output
MarketChart       ◄── OHLCV + indicator data
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, CrewAI 1.14.4, yfinance, pandas_ta, OpenAI Responses API |
| Frontend | React 18, TypeScript, Vite, ECharts 5, Framer Motion, Lucide Icons |
| APIs | Yahoo Finance, NewsAPI, Finnhub, OpenAI |
| Infra | ThreadingHTTPServer, uv package manager |

## Project Structure

```
clistetradeai/
├── src/clistetradeai/
│   ├── config/
│   │   ├── agents.yaml              # CrewAI agent definitions
│   │   ├── tasks.yaml               # CrewAI task definitions
│   │   └── trading_config.py        # Dynamic trading style → parameter mapping
│   ├── tools/
│   │   ├── MarketDataTool.py        # yfinance OHLCV fetcher
│   │   ├── IndicatorTool.py         # EMA, RSI, MACD computation
│   │   ├── MarketStateEngine.py     # Rule-based market intelligence
│   │   ├── SentimentDataFetcherTool.py  # News + macro event collection
│   │   └── SentimentCompressorTool.py   # LLM-based sentiment compression
│   ├── crew.py                      # CrewAI crew orchestration (4 agents)
│   ├── api_server.py                # HTTP server with background thread pipeline
│   └── main.py                      # CLI entry points
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfigPanel.tsx      # Ticker/style/risk tolerance selection
│   │   │   ├── MarketChart.tsx      # ECharts candlestick chart with indicators
│   │   │   ├── WorkflowTimeline.tsx # Real-time pipeline progress
│   │   │   ├── AgentOutputExplorer.tsx  # Tabbed structured results view
│   │   │   ├── SystemHeader.tsx     # Status bar
│   │   │   └── ErrorBoundary.tsx    # Crash containment wrapper
│   │   ├── hooks/useMarketAnalysis.ts  # Poll-based workflow orchestration
│   │   ├── services/marketApi.ts    # API client (start, poll, fetch)
│   │   ├── types/market.ts          # TypeScript interfaces
│   │   └── styles/global.css        # Dark theme terminal UI
│   └── vite.config.ts               # Dev proxy for 3 backend endpoints
├── .env                             # API keys (OPENAI_API_KEY, NEWSAPI_API_KEY, FINNHUB_API_KEY)
└── pyproject.toml
```

## Setup

### Prerequisites
- Python >=3.12, <3.14
- Node.js 18+
- uv package manager (`pip install uv`)

### Backend

```bash
# Install dependencies
uv sync

# Configure API keys in .env (OPENAI_API_KEY is required; NEWSAPI_API_KEY and FINNHUB_API_KEY are optional)
# OPENAI_API_KEY=sk-...
# NEWSAPI_API_KEY=...
# FINNHUB_API_KEY=...

# Start the API server
uv run api_server
# → http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npx vite --host 127.0.0.1 --port 5173
# → http://127.0.0.1:5173
```

## Pipeline Flow

| Stage | Frontend Label | Tool/Agent | Description |
|-------|---------------|-----------|-------------|
| 1 | Fetching Market Data | MarketDataTool | yfinance OHLCV fetch (period/interval from trading style) |
| 2 | Computing Indicators | IndicatorTool | EMA Fast/Slow, RSI, MACD via pandas_ta |
| 3 | Generating Market State Intelligence | MarketStateEngine | Rule-based trend, momentum, volatility, confidence scoring |
| 4 | Fetching Financial News | SentimentDataFetcherTool | News + macro events from NewsAPI / Finnhub |
| 5 | Compressing Sentiment Intelligence | SentimentCompressorTool | LLM compresses raw news into structured sentiment |
| 6 | Running Technical Agent | Technical Agent (CrewAI) | LLM interprets technical intelligence |
| 7 | Running Sentiment Agent | Sentiment Agent (CrewAI) | LLM interprets sentiment intelligence |
| 8 | Running Risk Agent | Risk Agent (CrewAI) | LLM evaluates signal alignment + uncertainty |
| 9 | Running Decision Agent | Decision Agent (CrewAI) | LLM synthesizes final BUY/SELL/HOLD |

All stages run in a background thread (`_run_pipeline`). The frontend polls `GET /workflow-status/:id` every 400ms and renders stage transitions in real time. When the `complete` flag is set, it fetches the full result via `GET /analysis-result/:id`.

## Key Design Decisions

- **No mock data**: Every number comes from live APIs — yfinance for prices, NewsAPI/Finnhub for news, OpenAI for sentiment compression
- **Deterministic fallback**: When no `OPENAI_API_KEY` is set, `deterministic_agent_outputs()` produces rule-based BUY/SELL/HOLD output with no LLM calls
- **Type-safe agent outputs**: `normalize_agent_output()` with per-field schemas (`TECHNICAL_SCHEMA`, `SENTIMENT_SCHEMA`, `RISK_SCHEMA`, `DECISION_SCHEMA`) coerces any LLM output to `str`, `int`, or `list[str]`
- **Error resilience**: All tool calls fail with clear errors; CrewAI exceptions fall back to deterministic output; `ErrorBoundary` prevents blank-screen crashes
- **Stable chart rendering**: ECharts instance is reused via `echarts.getInstanceByDom()` to avoid DOM race conditions on re-render
- **Adaptive configuration**: `trading_config.py` dynamically sets periods, intervals, indicator lengths, and sentiment windows from frontend trading style + risk tolerance

## Configuration

### Trading Styles (`trading_config.py`)

| Style | Period | Interval | EMA Fast | EMA Slow | RSI | Sentiment Window | Max Articles | Max Events |
|-------|--------|----------|----------|----------|-----|-----------------|-------------|------------|
| Swing Trading | 6mo | 1d | 20 | 50 | 14 | 30 days / 720h | 50 | 25 |
| Last 3 Days | 7d | 15m | 9 | 20 | 7 | 3 days / 72h | 25 | 12 |

### Risk Profiles

| Tolerance | Max Volatility | Fallback Confidence Effect |
|-----------|---------------|---------------------------|
| Low | 2% | If volatility != low: subtract 10, cap at 30 |
| Moderate | 3% | No additional penalty |
| High | 5% | No additional penalty |

The confidence penalty in the deterministic fallback reduces the final confidence when low-risk tolerance combines with non-low volatility. The CrewAI risk agent handles it via LLM reasoning when available.
