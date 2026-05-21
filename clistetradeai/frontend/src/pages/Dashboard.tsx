import { useMemo, useState } from "react";
import { AgentOutputExplorer } from "../components/AgentOutputExplorer";
import { ConfigPanel } from "../components/ConfigPanel";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { MarketChart } from "../components/MarketChart";
import { SystemHeader } from "../components/SystemHeader";
import { WorkflowTimeline } from "../components/WorkflowTimeline";
import { useMarketAnalysis } from "../hooks/useMarketAnalysis";
import type { MarketRequest } from "../types/market";

const defaultRequest: MarketRequest = {
  assetType: "stock",
  ticker: "AAPL",
  tradingStyle: "swing",
  riskTolerance: "moderate"
};

export function Dashboard() {
  const [request, setRequest] = useState<MarketRequest>(defaultRequest);
  const { activeStage, error, isRunning, result, runAnalysis, workflow } = useMarketAnalysis();

  const chartData = useMemo(() => result?.chartData ?? [], [result]);

  return (
    <main className="app-shell">
      <ConfigPanel
        isRunning={isRunning}
        onAnalyze={() => runAnalysis(request)}
        onChange={setRequest}
        value={request}
      />

      <div className="workspace">
        <SystemHeader activeStage={activeStage} request={request} />

        <div className="top-grid">
          <ErrorBoundary><MarketChart data={chartData} ticker={request.ticker} tradingStyle={request.tradingStyle} /></ErrorBoundary>
          <section className="terminal-card recommendation-rail">
            <p className="eyebrow">Final Recommendation</p>
            <h2>{result?.recommendation.label ?? "Awaiting Execution"}</h2>
            <div className="large-score">{result?.recommendation.confidence ?? "--"}<span>%</span></div>
            <p>
              {result?.recommendation.explanation ??
                "Configure the market, risk tolerance, and trading horizon, then run the autonomous workflow."}
            </p>
            <div className="rail-metrics">
              <Metric label="Style" value={request.tradingStyle === "swing" ? "Swing" : "Last 3 Days"} />
              <Metric label="Asset" value={request.assetType} />
              <Metric label="Risk" value={request.riskTolerance} />
            </div>
          </section>
        </div>

        <ErrorBoundary><WorkflowTimeline stages={workflow} /></ErrorBoundary>
        {error && (
          <section className="terminal-card error-panel">
            <p className="eyebrow">Backend Workflow Error</p>
            <h2>Analysis could not complete</h2>
            <p>{error}</p>
          </section>
        )}
        <ErrorBoundary><AgentOutputExplorer result={result} /></ErrorBoundary>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
