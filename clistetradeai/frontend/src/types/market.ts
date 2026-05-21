export type AssetType = "stock" | "forex";
export type TradingStyle = "swing" | "last_3_days";
export type RiskTolerance = "low" | "moderate" | "high";
export type WorkflowStatus = "pending" | "running" | "complete" | "error";

export interface MarketRequest {
  assetType: AssetType;
  ticker: string;
  tradingStyle: TradingStyle;
  riskTolerance: RiskTolerance;
}

export interface CandleRecord {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema_9?: number;
  ema_20?: number;
  ema_50?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
}

export interface WorkflowStage {
  id: string;
  label: string;
  description: string;
  status: WorkflowStatus;
}

export interface TechnicalOutput {
  technical_outlook: string;
  confidence_level: number;
  trend_explanation: string;
  momentum_interpretation: string;
  volatility_assessment: string;
  technical_reasoning: string;
  notable_risks: string[];
  key_technical_signals: string[];
}

export interface SentimentOutput {
  sentiment_outlook: string;
  confidence_level: number;
  macro_interpretation: string;
  dominant_narratives: string[];
  bullish_sentiment_factors: string[];
  bearish_sentiment_factors: string[];
  conflicting_narratives: string[];
  sentiment_reasoning: string;
}

export interface RiskOutput {
  overall_risk_level: string;
  trade_quality: string;
  uncertainty_level: string;
  signal_alignment: string;
  recommended_exposure_size: string;
  risk_tolerance_context: string;
  warnings: string[];
  risk_reasoning: string;
}

export interface DecisionOutput {
  final_recommendation: "BUY" | "SELL" | "HOLD";
  final_confidence: number;
  reasoning_summary: string;
  supporting_factors: string[];
  warning_signals: string[];
  technical_weight: number;
  sentiment_weight: number;
  risk_weight: number;
  execution_notes: string;
}

export interface MarketAnalysisResult {
  requestId: string;
  assetType?: AssetType;
  ticker?: string;
  tradingStyle?: TradingStyle;
  riskTolerance?: RiskTolerance;
  recommendation: {
    label: string;
    confidence: number;
    explanation: string;
  };
  chartData: CandleRecord[];
  workflow: WorkflowStage[];
  technical: TechnicalOutput;
  sentiment: SentimentOutput;
  risk: RiskOutput;
  decision: DecisionOutput;
}
