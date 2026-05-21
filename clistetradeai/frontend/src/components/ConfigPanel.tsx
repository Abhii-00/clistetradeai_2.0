import { Activity, BarChart3, BrainCircuit, Gauge, Search } from "lucide-react";
import type { AssetType, MarketRequest, RiskTolerance, TradingStyle } from "../types/market";

const stocks = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"];
const forexPairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"];

interface ConfigPanelProps {
  value: MarketRequest;
  isRunning: boolean;
  onChange: (value: MarketRequest) => void;
  onAnalyze: () => void;
}

export function ConfigPanel({ value, isRunning, onAnalyze, onChange }: ConfigPanelProps) {
  const tickers = value.assetType === "stock" ? stocks : forexPairs;

  function update(patch: Partial<MarketRequest>) {
    onChange({ ...value, ...patch });
  }

  function setAssetType(assetType: AssetType) {
    onChange({
      ...value,
      assetType,
      ticker: assetType === "stock" ? stocks[0] : forexPairs[0]
    });
  }

  return (
    <aside className="config-panel">
      <div className="brand-lockup">
        <div className="brand-mark">
          <BrainCircuit size={26} />
        </div>
        <div>
          <p className="eyebrow">Autonomous Intelligence</p>
          <h1>ClisteTrade AI</h1>
        </div>
      </div>

      <section className="panel-section">
        <div className="section-title">
          <BarChart3 size={16} />
          <span>Market Universe</span>
        </div>
        <label className="field-label">Asset Type</label>
        <div className="segmented-control">
          {(["stock", "forex"] as AssetType[]).map((assetType) => (
            <button
              className={value.assetType === assetType ? "selected" : ""}
              key={assetType}
              onClick={() => setAssetType(assetType)}
              type="button"
            >
              {assetType === "stock" ? "Stock" : "Forex"}
            </button>
          ))}
        </div>

        <label className="field-label" htmlFor="ticker-select">
          {value.assetType === "stock" ? "Ticker" : "Forex Pair"}
        </label>
        <div className="select-shell">
          <Search size={16} />
          <select
            id="ticker-select"
            value={value.ticker}
            onChange={(event) => update({ ticker: event.target.value })}
          >
            {tickers.map((ticker) => (
              <option key={ticker} value={ticker}>
                {ticker}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="panel-section">
        <div className="section-title">
          <Activity size={16} />
          <span>Execution Horizon</span>
        </div>
        <label className="field-label">Trading Style</label>
        <div className="stacked-options">
          <OptionButton
            active={value.tradingStyle === "swing"}
            label="Swing Trading"
            meta="6mo candles, EMA20/50, 30d sentiment"
            onClick={() => update({ tradingStyle: "swing" })}
          />
          <OptionButton
            active={value.tradingStyle === "last_3_days"}
            label="Last 3 Days"
            meta="7d intraday, EMA9/20, 72h catalysts"
            onClick={() => update({ tradingStyle: "last_3_days" })}
          />
        </div>
      </section>

      <section className="panel-section">
        <div className="section-title">
          <Gauge size={16} />
          <span>Risk Profile</span>
        </div>
        <div className="risk-grid">
          {(["low", "moderate", "high"] as RiskTolerance[]).map((risk) => (
            <button
              className={value.riskTolerance === risk ? "risk-chip selected" : "risk-chip"}
              key={risk}
              onClick={() => update({ riskTolerance: risk })}
              type="button"
            >
              {risk}
            </button>
          ))}
        </div>
      </section>

      <button className="analyze-button" disabled={isRunning} onClick={onAnalyze} type="button">
        {isRunning ? "Running Workflow" : "Analyze Market"}
      </button>
    </aside>
  );
}

interface OptionButtonProps {
  active: boolean;
  label: string;
  meta: string;
  onClick: () => void;
}

function OptionButton({ active, label, meta, onClick }: OptionButtonProps) {
  return (
    <button className={active ? "option-card active" : "option-card"} onClick={onClick} type="button">
      <span>{label}</span>
      <small>{meta}</small>
    </button>
  );
}
