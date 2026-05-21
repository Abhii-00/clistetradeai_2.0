import type { MarketAnalysisResult, MarketRequest, WorkflowStage } from "../types/market";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const workflowLabels: Omit<WorkflowStage, "status">[] = [
  { id: "market_data", label: "Fetching Market Data", description: "Yahoo Finance OHLCV ingestion" },
  { id: "indicators", label: "Computing Indicators", description: "EMA, RSI, MACD enrichment" },
  { id: "market_state", label: "Generating Market State Intelligence", description: "Rule-based technical compression" },
  { id: "news", label: "Fetching Financial News", description: "News and macro event collection" },
  { id: "sentiment_compression", label: "Compressing Sentiment Intelligence", description: "Semantic news and macro compression" },
  { id: "technical_agent", label: "Running Technical Agent", description: "LLM technical interpretation" },
  { id: "sentiment_agent", label: "Running Sentiment Agent", description: "LLM sentiment interpretation" },
  { id: "risk_agent", label: "Running Risk Agent", description: "Signal alignment and uncertainty analysis" },
  { id: "decision_agent", label: "Running Decision Agent", description: "BUY, SELL, or HOLD synthesis" }
];

export const initialWorkflow = (): WorkflowStage[] =>
  workflowLabels.map((stage) => ({ ...stage, status: "pending" }));

export async function startAnalysis(request: MarketRequest): Promise<{ requestId: string; workflow: WorkflowStage[] }> {
  const response = await fetch(`${API_BASE}/analyze-market`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_type: request.assetType,
      ticker: request.ticker,
      trading_style: request.tradingStyle,
      risk_tolerance: request.riskTolerance
    })
  });

  if (!response.ok) {
    let message = `Backend returned ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.error ?? message;
    } catch {
      // Keep the HTTP status message if the backend did not return JSON.
    }
    throw new Error(message);
  }

  return response.json();
}

export async function pollWorkflow(requestId: string): Promise<{ workflow: WorkflowStage[]; complete: boolean; error?: string }> {
  const response = await fetch(`${API_BASE}/workflow-status/${requestId}`);

  if (!response.ok) {
    throw new Error(`Failed to poll workflow: ${response.status}`);
  }

  return response.json();
}

export async function fetchResult(requestId: string): Promise<MarketAnalysisResult> {
  const response = await fetch(`${API_BASE}/analysis-result/${requestId}`);

  if (!response.ok) {
    let message = `Failed to fetch result: ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.error ?? message;
    } catch {
      // Keep the HTTP status message if the backend did not return JSON.
    }
    throw new Error(message);
  }

  return response.json();
}
