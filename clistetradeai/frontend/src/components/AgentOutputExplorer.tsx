import { AlertTriangle, Brain, Gauge, Newspaper, TrendingUp } from "lucide-react";
import type React from "react";
import { useState } from "react";
import type { MarketAnalysisResult } from "../types/market";

interface AgentOutputExplorerProps {
  result: MarketAnalysisResult | null;
}

type TabKey = "final" | "technical" | "sentiment" | "risk";

export function AgentOutputExplorer({ result }: AgentOutputExplorerProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("final");

  if (!result) {
    return (
      <section className="terminal-card output-card empty-output">
        <p className="eyebrow">Agent Output Explorer</p>
        <h2>Awaiting market analysis</h2>
        <p>Run the workflow to inspect final recommendation, technical reasoning, sentiment intelligence, and risk evaluation.</p>
      </section>
    );
  }

  return (
    <section className="terminal-card output-card">
      <div className="tabs">
        <TabButton active={activeTab === "final"} icon={<Brain size={16} />} label="Final Recommendation" onClick={() => setActiveTab("final")} />
        <TabButton active={activeTab === "technical"} icon={<TrendingUp size={16} />} label="Technical Analysis" onClick={() => setActiveTab("technical")} />
        <TabButton active={activeTab === "sentiment"} icon={<Newspaper size={16} />} label="Sentiment Analysis" onClick={() => setActiveTab("sentiment")} />
        <TabButton active={activeTab === "risk"} icon={<Gauge size={16} />} label="Risk Analysis" onClick={() => setActiveTab("risk")} />
      </div>

      {activeTab === "final" && (
        <div className="analysis-grid final-grid">
          <div className="recommendation-panel">
            <p className="eyebrow">Final Market Intelligence</p>
            <h2>{result.decision?.final_recommendation ?? result.recommendation.label}</h2>
            <ConfidenceMeter value={result.decision?.final_confidence ?? result.recommendation.confidence} />
            <p>{result.decision?.reasoning_summary ?? result.recommendation.explanation}</p>
          </div>
          <InsightCard title="Signal Alignment" value={result.risk.signal_alignment} body={result.risk.risk_reasoning} />
          <InsightCard title="Exposure" value={result.risk.recommended_exposure_size} body={result.risk.risk_tolerance_context} />
          <ListCard title="Decision Supporting Factors" items={result.decision?.supporting_factors ?? []} />
          <ListCard title="Decision Warnings" items={result.decision?.warning_signals ?? []} warning />
        </div>
      )}

      {activeTab === "technical" && (
        <div className="analysis-grid">
          <InsightCard title="Outlook" value={result.technical.technical_outlook} body={result.technical.technical_reasoning} />
          <InsightCard title="Trend" value="Trend Explanation" body={result.technical.trend_explanation} />
          <InsightCard title="Momentum" value="Momentum Interpretation" body={result.technical.momentum_interpretation} />
          <InsightCard title="Volatility" value="Volatility Assessment" body={result.technical.volatility_assessment} />
          <ListCard title="Key Technical Signals" items={result.technical.key_technical_signals ?? []} />
          <ListCard title="Notable Risks" items={result.technical.notable_risks ?? []} warning />
        </div>
      )}

      {activeTab === "sentiment" && (
        <div className="analysis-grid">
          <InsightCard title="Outlook" value={result.sentiment.sentiment_outlook} body={result.sentiment.sentiment_reasoning} />
          <InsightCard title="Macro Interpretation" value="Macroeconomic Context" body={result.sentiment.macro_interpretation} />
          <ListCard title="Dominant Narratives" items={result.sentiment.dominant_narratives ?? []} />
          <ListCard title="Bullish Factors" items={result.sentiment.bullish_sentiment_factors ?? []} />
          <ListCard title="Bearish Factors" items={result.sentiment.bearish_sentiment_factors ?? []} warning />
          <ListCard title="Conflicting Narratives" items={result.sentiment.conflicting_narratives ?? []} warning />
        </div>
      )}

      {activeTab === "risk" && (
        <div className="analysis-grid">
          <InsightCard title="Overall Risk" value={result.risk.overall_risk_level} body={result.risk.risk_reasoning} />
          <InsightCard title="Trade Quality" value={result.risk.trade_quality} body={`Uncertainty: ${result.risk.uncertainty_level}`} />
          <InsightCard title="Exposure Size" value={result.risk.recommended_exposure_size} body={result.risk.risk_tolerance_context} />
          <ListCard title="Warnings" items={result.risk.warnings ?? []} warning />
        </div>
      )}
    </section>
  );
}

interface TabButtonProps {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}

function TabButton({ active, icon, label, onClick }: TabButtonProps) {
  return (
    <button className={active ? "tab-button active" : "tab-button"} onClick={onClick} type="button">
      {icon}
      <span>{label}</span>
    </button>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="confidence-meter">
      <div className="confidence-label">
        <span>Confidence</span>
        <strong>{value}%</strong>
      </div>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

interface InsightCardProps {
  title: string;
  value: string;
  body: string;
}

function InsightCard({ body, title, value }: InsightCardProps) {
  return (
    <article className="insight-card">
      <p className="mini-label">{title}</p>
      <h3>{value}</h3>
      <p>{body}</p>
    </article>
  );
}

interface ListCardProps {
  items: string[];
  title: string;
  warning?: boolean;
}

function renderItem(item: unknown): string {
  if (typeof item === "string") return item;
  if (item === null || item === undefined) return "";
  if (typeof item === "object") {
    try { return JSON.stringify(item); } catch { return String(item); }
  }
  return String(item);
}

function ListCard({ items, title, warning }: ListCardProps) {
  const safeItems: string[] = (Array.isArray(items) ? items : []).map(renderItem);
  return (
    <article className={warning ? "insight-card warning-card" : "insight-card"}>
      <p className="mini-label">{title}</p>
      <ul>
        {safeItems.length ? (
          safeItems.map((item) => <li key={item}>{item}</li>)
        ) : (
          <li>{warning ? "No warnings reported" : "No supporting items reported"}</li>
        )}
      </ul>
      {warning && <AlertTriangle className="card-watermark" size={44} />}
    </article>
  );
}
