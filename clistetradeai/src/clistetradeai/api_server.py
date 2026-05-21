import json
import os
import re
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from clistetradeai.config.trading_config import get_pipeline_config
from clistetradeai.crew import Clistetradeai
from clistetradeai.tools.IndicatorTool import IndicatorTool
from clistetradeai.tools.MarketDataTool import MarketDataTool
from clistetradeai.tools.MarketStateEngine import MarketStateEngine
from clistetradeai.tools.SentimentCompressorTool import SentimentCompressorTool
from clistetradeai.tools.SentimentDataFetcherTool import SentimentDataFetcherTool


RUN_STORE: dict[str, dict[str, Any]] = {}
RUN_LOCK = threading.Lock()


WORKFLOW_DEFINITION = [
    {"id": "market_data", "label": "Fetching Market Data", "description": "Yahoo Finance OHLCV ingestion"},
    {"id": "indicators", "label": "Computing Indicators", "description": "EMA, RSI, MACD enrichment"},
    {"id": "market_state", "label": "Generating Market Intelligence", "description": "Rule-based technical compression"},
    {"id": "news", "label": "Fetching Financial News", "description": "News and macro event collection"},
    {"id": "sentiment_compression", "label": "Compressing Sentiment Intelligence", "description": "Semantic news and macro compression"},
    {"id": "technical_agent", "label": "Running Technical Agent", "description": "Technical reasoning"},
    {"id": "sentiment_agent", "label": "Running Sentiment Agent", "description": "Sentiment reasoning"},
    {"id": "risk_agent", "label": "Running Risk Agent", "description": "Risk and uncertainty evaluation"},
    {"id": "decision_agent", "label": "Running Decision Agent", "description": "BUY, SELL, or HOLD synthesis"},
]


def make_workflow(status: str = "pending") -> list[dict[str, str]]:
    return [{**stage, "status": status} for stage in WORKFLOW_DEFINITION]


def set_stage(request_id: str, stage_id: str, status: str) -> None:
    with RUN_LOCK:
        entry = RUN_STORE.get(request_id)
        if entry:
            for stage in entry.get("workflow", []):
                if stage["id"] == stage_id:
                    stage["status"] = status
                    break


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "ClisteTradeAI/0.1"

    def do_OPTIONS(self) -> None:
        self._send_json({}, HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:
        if self.path.startswith("/workflow-status/"):
            return self._get_workflow_status()
        if self.path.startswith("/analysis-result/"):
            return self._get_analysis_result()
        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/analyze-market":
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        try:
            payload = self._read_json()
            request_id = str(uuid.uuid4())
            with RUN_LOCK:
                RUN_STORE[request_id] = {
                    "workflow": make_workflow("pending"),
                    "result": None,
                    "error": None,
                }
            thread = threading.Thread(target=_run_pipeline, args=(request_id, payload), daemon=True)
            thread.start()
            with RUN_LOCK:
                workflow = list(RUN_STORE[request_id]["workflow"])
            self._send_json({"requestId": request_id, "workflow": workflow})
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _get_workflow_status(self) -> None:
        request_id = self.path.rstrip("/").split("/")[-1]
        with RUN_LOCK:
            entry = RUN_STORE.get(request_id)
        if not entry:
            return self._send_json({"error": "Unknown request id"}, HTTPStatus.NOT_FOUND)
        self._send_json({
            "workflow": entry.get("workflow", []),
            "complete": entry.get("result") is not None,
            "error": entry.get("error"),
        })

    def _get_analysis_result(self) -> None:
        request_id = self.path.rstrip("/").split("/")[-1]
        with RUN_LOCK:
            result = RUN_STORE.get(request_id, {}).get("result")
        if not result:
            return self._send_json({"error": "Result not ready"}, HTTPStatus.NOT_FOUND)
        self._send_json(result)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body or "{}")

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if status != HTTPStatus.NO_CONTENT:
            self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _run_pipeline(request_id: str, payload: dict[str, Any]) -> None:
    try:
        asset_type = payload.get("asset_type") or payload.get("assetType") or "stock"
        ticker = payload.get("ticker") or "AAPL"
        trading_style = payload.get("trading_style") or payload.get("tradingStyle") or "swing"
        risk_tolerance = payload.get("risk_tolerance") or payload.get("riskTolerance") or "moderate"
        config = get_pipeline_config(asset_type, ticker, trading_style, risk_tolerance)
        market_symbol = to_yfinance_symbol(config["asset_type"], config["ticker"])

        set_stage(request_id, "market_data", "running")
        market_data = MarketDataTool()._run(
            ticker=market_symbol,
            period=config["period"],
            interval=config["interval"],
            trading_style=config["trading_style"],
        )
        require_success(market_data, "MarketDataTool")
        set_stage(request_id, "market_data", "complete")

        set_stage(request_id, "indicators", "running")
        indicators = IndicatorTool()._run(
            market_data=market_data,
            ema_fast=config["ema_fast"],
            ema_slow=config["ema_slow"],
            rsi_length=config["rsi_length"],
            trading_style=config["trading_style"],
        )
        require_success(indicators, "IndicatorTool")
        set_stage(request_id, "indicators", "complete")

        set_stage(request_id, "market_state", "running")
        market_state = MarketStateEngine()._run(
            indicator_data=indicators,
            ema_fast=config["ema_fast"],
            ema_slow=config["ema_slow"],
            trading_style=config["trading_style"],
            risk_tolerance=config["risk_tolerance"],
        )
        require_success(market_state, "MarketStateEngine")
        set_stage(request_id, "market_state", "complete")

        set_stage(request_id, "news", "running")
        sentiment_raw = SentimentDataFetcherTool()._run(
            asset_type=config["asset_type"],
            ticker=config["ticker"],
            trading_style=config["trading_style"],
        )
        set_stage(request_id, "news", "complete")

        set_stage(request_id, "sentiment_compression", "running")
        sentiment_compressed = SentimentCompressorTool()._run(
            sentiment_data=sentiment_raw,
            asset_type=config["asset_type"],
            ticker=config["ticker"],
            trading_style=config["trading_style"],
            risk_tolerance=config["risk_tolerance"],
            use_llm=bool(os.getenv("OPENAI_API_KEY")),
        )
        if not sentiment_compressed.get("success"):
            sentiment_compressed = empty_sentiment(config["ticker"], config["trading_style"])
        set_stage(request_id, "sentiment_compression", "complete")

        set_stage(request_id, "technical_agent", "running")
        set_stage(request_id, "sentiment_agent", "running")
        agent_outputs = run_agents(
            ticker=config["ticker"],
            trading_style=config["trading_style"],
            risk_tolerance=config["risk_tolerance"],
            market_state=market_state,
            sentiment_compressed=sentiment_compressed,
        )
        set_stage(request_id, "technical_agent", "complete")
        set_stage(request_id, "sentiment_agent", "complete")

        set_stage(request_id, "risk_agent", "running")
        set_stage(request_id, "risk_agent", "complete")

        set_stage(request_id, "decision_agent", "running")
        decision = agent_outputs["decision"]
        set_stage(request_id, "decision_agent", "complete")

        result = {
            "requestId": request_id,
            "assetType": config["asset_type"],
            "ticker": config["ticker"],
            "tradingStyle": config["trading_style"],
            "riskTolerance": config["risk_tolerance"],
            "recommendation": {
                "label": decision.get("final_recommendation", "HOLD"),
                "confidence": int(decision.get("final_confidence", 50)),
                "explanation": decision.get("reasoning_summary", "Decision Agent completed final synthesis."),
            },
            "chartData": indicators["data"],
            "workflow": make_workflow("complete"),
            "technical": agent_outputs["technical"],
            "sentiment": agent_outputs["sentiment"],
            "risk": agent_outputs["risk"],
            "decision": decision,
            "toolOutputs": {
                "marketData": without_heavy_data(market_data),
                "indicators": without_heavy_data(indicators),
                "marketState": market_state,
                "sentimentRaw": sentiment_raw,
                "sentimentCompressed": sentiment_compressed,
            },
        }
        with RUN_LOCK:
            if request_id in RUN_STORE:
                RUN_STORE[request_id]["result"] = result
                RUN_STORE[request_id]["workflow"] = make_workflow("complete")

    except Exception as exc:
        with RUN_LOCK:
            if request_id in RUN_STORE:
                RUN_STORE[request_id]["error"] = str(exc)


def normalize_agent_output(output: dict[str, Any], schema: dict[str, type]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, expected_type in schema.items():
        value = output.get(key)
        if expected_type is str:
            if isinstance(value, dict | list):
                result[key] = json.dumps(value, default=str)
            elif value is None:
                result[key] = ""
            else:
                result[key] = str(value)
        elif expected_type is int:
            try:
                result[key] = int(float(str(value))) if value is not None else 0
            except (ValueError, TypeError):
                result[key] = 0
        elif expected_type == "list[str]":
            if isinstance(value, list):
                result[key] = [
                    json.dumps(item, default=str) if isinstance(item, dict | list) else str(item) if item is not None else ""
                    for item in value
                ]
            else:
                result[key] = []
        else:
            result[key] = value
    return result


TECHNICAL_SCHEMA: dict[str, type] = {
    "technical_outlook": str,
    "confidence_level": int,
    "trend_explanation": str,
    "momentum_interpretation": str,
    "volatility_assessment": str,
    "technical_reasoning": str,
    "notable_risks": "list[str]",
    "key_technical_signals": "list[str]",
}

SENTIMENT_SCHEMA: dict[str, type] = {
    "sentiment_outlook": str,
    "confidence_level": int,
    "macro_interpretation": str,
    "dominant_narratives": "list[str]",
    "bullish_sentiment_factors": "list[str]",
    "bearish_sentiment_factors": "list[str]",
    "conflicting_narratives": "list[str]",
    "sentiment_reasoning": str,
}

RISK_SCHEMA: dict[str, type] = {
    "overall_risk_level": str,
    "trade_quality": str,
    "uncertainty_level": str,
    "signal_alignment": str,
    "recommended_exposure_size": str,
    "risk_tolerance_context": str,
    "warnings": "list[str]",
    "risk_reasoning": str,
}

DECISION_SCHEMA: dict[str, type] = {
    "final_recommendation": str,
    "final_confidence": int,
    "reasoning_summary": str,
    "supporting_factors": "list[str]",
    "warning_signals": "list[str]",
    "technical_weight": int,
    "sentiment_weight": int,
    "risk_weight": int,
    "execution_notes": str,
}


def run_agents(
    ticker: str,
    trading_style: str,
    risk_tolerance: str,
    market_state: dict[str, Any],
    sentiment_compressed: dict[str, Any],
) -> dict[str, Any]:
    fallback = deterministic_agent_outputs(market_state, sentiment_compressed, risk_tolerance)
    if not os.getenv("OPENAI_API_KEY"):
        return fallback

    try:
        crew_result = Clistetradeai().crew().kickoff(
            inputs={
                "ticker": ticker,
                "trading_style": trading_style,
                "risk_tolerance": risk_tolerance,
                "technical_market_state": json.dumps(market_state, default=str),
                "compressed_sentiment": json.dumps(sentiment_compressed, default=str),
            }
        )
        task_outputs = getattr(crew_result, "tasks_output", []) or []
        return {
            "technical": normalize_agent_output(parse_task_json(task_outputs, 0, fallback["technical"]), TECHNICAL_SCHEMA),
            "sentiment": normalize_agent_output(parse_task_json(task_outputs, 1, fallback["sentiment"]), SENTIMENT_SCHEMA),
            "risk": normalize_agent_output(parse_task_json(task_outputs, 2, fallback["risk"]), RISK_SCHEMA),
            "decision": normalize_agent_output(parse_task_json(task_outputs, 3, fallback["decision"]), DECISION_SCHEMA),
        }
    except Exception as exc:
        fallback["decision"]["warning_signals"].append(f"CrewAI agent execution fallback used: {exc}")
        return fallback


def deterministic_agent_outputs(
    market_state: dict[str, Any],
    sentiment: dict[str, Any],
    risk_tolerance: str,
) -> dict[str, Any]:
    technical_outlook = normalize_direction(market_state.get("trend_direction", "neutral"))
    sentiment_outlook = sentiment.get("overall_sentiment", "neutral")
    technical_confidence = int(market_state.get("confidence", 50))
    sentiment_confidence = int(sentiment.get("confidence_score", 45))
    aligned = directions_align(technical_outlook, sentiment_outlook)
    volatility = market_state.get("volatility", "moderate")
    risk_level = "high" if volatility == "high" or not aligned else "moderate"
    exposure = "small" if risk_tolerance == "low" or risk_level == "high" else "moderate"

    recommendation = "HOLD"
    if aligned and technical_confidence >= 60:
        recommendation = "BUY" if technical_outlook == "bullish" else "SELL" if technical_outlook == "bearish" else "HOLD"

    final_confidence = int((technical_confidence + sentiment_confidence) / 2)
    if not aligned:
        final_confidence = max(35, final_confidence - 18)
    if risk_tolerance == "low" and volatility != "low":
        final_confidence = max(30, final_confidence - 10)

    technical = {
        "technical_outlook": technical_outlook,
        "confidence_level": technical_confidence,
        "trend_explanation": f"Trend direction is {market_state.get('trend_direction')} with regime {market_state.get('market_regime')}.",
        "momentum_interpretation": f"Momentum state is {market_state.get('momentum_state')}.",
        "volatility_assessment": f"Volatility is classified as {volatility}.",
        "technical_reasoning": "MarketStateEngine converted backend indicators into scored technical intelligence.",
        "notable_risks": [f"Volatility regime: {volatility}"],
        "key_technical_signals": market_state.get("key_signals", []),
    }
    sent = {
        "sentiment_outlook": sentiment_outlook,
        "confidence_level": sentiment_confidence,
        "macro_interpretation": "; ".join(sentiment.get("macroeconomic_implications", [])) or "No major macro event pressure retrieved.",
        "dominant_narratives": sentiment.get("major_themes", []),
        "bullish_sentiment_factors": sentiment.get("bullish_pressure_indicators", []),
        "bearish_sentiment_factors": sentiment.get("bearish_pressure_indicators", []),
        "conflicting_narratives": sentiment.get("conflicting_narratives", []),
        "sentiment_reasoning": sentiment.get("market_narrative", "Sentiment compression completed."),
    }
    risk = {
        "overall_risk_level": risk_level,
        "trade_quality": "acceptable" if aligned else "uncertain",
        "uncertainty_level": "moderate" if aligned else "high",
        "signal_alignment": "aligned" if aligned else "conflicting",
        "recommended_exposure_size": exposure,
        "risk_tolerance_context": f"{risk_tolerance} risk tolerance applied to volatility and confidence.",
        "warnings": [] if aligned else ["Technical and sentiment directions conflict."],
        "risk_reasoning": "Risk assessment compares technical direction, sentiment direction, confidence, and volatility.",
    }
    decision = {
        "final_recommendation": recommendation,
        "final_confidence": final_confidence,
        "reasoning_summary": f"{recommendation} generated from technical {technical_outlook}, sentiment {sentiment_outlook}, and {risk_level} risk.",
        "supporting_factors": [*technical["key_technical_signals"][:4], *sent["dominant_narratives"][:3]],
        "warning_signals": risk["warnings"],
        "technical_weight": 0.4,
        "sentiment_weight": 0.3,
        "risk_weight": 0.3,
        "execution_notes": "Final recommendation produced by backend orchestration fallback because no agent LLM key was available.",
    }
    return {"technical": technical, "sentiment": sent, "risk": risk, "decision": decision}


def parse_task_json(task_outputs: list[Any], index: int, fallback: dict[str, Any]) -> dict[str, Any]:
    if index >= len(task_outputs):
        return fallback
    raw = getattr(task_outputs[index], "raw", str(task_outputs[index]))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return fallback
    return fallback


def require_success(result: dict[str, Any], tool_name: str) -> None:
    if not result.get("success"):
        raise RuntimeError(f"{tool_name} failed: {result.get('error', 'Unknown error')}")


def without_heavy_data(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "data"}


def empty_sentiment(ticker: str, trading_style: str) -> dict[str, Any]:
    return {
        "success": True,
        "overall_sentiment": "neutral",
        "confidence_score": 35,
        "major_themes": ["No external sentiment data available"],
        "macroeconomic_implications": [],
        "market_narrative": f"No usable sentiment data was retrieved for {ticker} in {trading_style} mode.",
        "bullish_pressure_indicators": [],
        "bearish_pressure_indicators": [],
        "conflicting_narratives": [],
        "key_supporting_headlines": [],
        "key_supporting_events": [],
    }


def normalize_direction(value: str) -> str:
    lowered = str(value).lower()
    if "bull" in lowered:
        return "bullish"
    if "bear" in lowered:
        return "bearish"
    return "neutral"


def directions_align(technical: str, sentiment: str) -> bool:
    if sentiment in {"mixed", "neutral"} or technical == "neutral":
        return False
    return technical == sentiment


def to_yfinance_symbol(asset_type: str, ticker: str) -> str:
    if asset_type.lower() == "forex" and not ticker.endswith("=X"):
        return f"{ticker}=X"
    return ticker


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"ClisteTrade AI API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
