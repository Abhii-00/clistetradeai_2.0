# tools/market_state_engine.py

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any
import pandas as pd

from clistetradeai.config.trading_config import (
    VOLATILITY_THRESHOLDS,
    get_risk_config,
    get_trading_config,
)


class MarketStateInput(BaseModel):

    indicator_data: List[Dict[str, Any]] | Dict[str, Any] = Field(..., description="Indicator records or IndicatorTool output")

    ema_fast: int | None = None
    ema_slow: int | None = None
    trading_style: str | None = None

    risk_tolerance: str = "moderate"


class MarketStateEngine(BaseTool):

    name: str = "Market State Engine"

    description: str = (
        "Analyzes indicators and generates "
        "market intelligence."
    )

    args_schema: Type[BaseModel] = MarketStateInput

    def _run(
        self,
        indicator_data: List[Dict[str, Any]] | Dict[str, Any],
        ema_fast: int | None = None,
        ema_slow: int | None = None,
        trading_style: str | None = None,
        risk_tolerance: str = "moderate"
    ) -> dict:

        try:
            trading_config = get_trading_config(trading_style)
            resolved_ema_fast = ema_fast or trading_config["ema_fast"]
            resolved_ema_slow = ema_slow or trading_config["ema_slow"]
            records = indicator_data.get("data", []) if isinstance(indicator_data, dict) else indicator_data

            df = pd.DataFrame(records)

            if df.empty:
                return {
                    "success": False,
                    "error": "Empty dataframe"
                }

            risk_config = get_risk_config(
                risk_tolerance
            )
            resolved_risk_tolerance = str(risk_config["risk_tolerance"])

            bullish_score = 0
            bearish_score = 0

            key_signals = []

            required_columns = ["close", "high", "low", "rsi", "macd", "macd_signal"]
            missing_columns = [column for column in required_columns if column not in df.columns]

            ema_fast_col = f"ema_{resolved_ema_fast}"
            ema_slow_col = f"ema_{resolved_ema_slow}"
            missing_columns.extend(
                column for column in [ema_fast_col, ema_slow_col] if column not in df.columns
            )

            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required indicator columns: {sorted(set(missing_columns))}",
                    "ema_fast_column": ema_fast_col,
                    "ema_slow_column": ema_slow_col,
                }

            for column in [*required_columns, ema_fast_col, ema_slow_col]:
                df[column] = pd.to_numeric(df[column], errors="coerce")

            df = df.dropna(subset=[*required_columns, ema_fast_col, ema_slow_col])
            if df.empty:
                return {
                    "success": False,
                    "error": "No valid numeric indicator rows"
                }

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest

            latest_ema_fast = latest[ema_fast_col]
            latest_ema_slow = latest[ema_slow_col]
            latest_rsi = latest["rsi"]
            latest_macd = latest["macd"]
            latest_macd_signal = latest["macd_signal"]

            trend_direction = "sideways"
            momentum_state = "neutral"

            if latest_ema_fast > latest_ema_slow:
                bullish_score += 3
                trend_direction = "bullish"
                key_signals.append("Bullish EMA alignment")
            elif latest_ema_fast < latest_ema_slow:
                bearish_score += 3
                trend_direction = "bearish"
                key_signals.append("Bearish EMA alignment")
            else:
                key_signals.append("Flat EMA alignment")

            if latest_rsi < 30:
                bullish_score += 2
                key_signals.append("RSI oversold condition")
            elif latest_rsi > 70:
                bearish_score += 2
                key_signals.append("RSI overbought condition")
            elif 45 <= latest_rsi <= 55:
                key_signals.append("RSI neutral momentum")

            if latest_macd > latest_macd_signal:
                bullish_score += 3
                momentum_state = "increasing"
                key_signals.append("Bullish MACD alignment")
            elif latest_macd < latest_macd_signal:
                bearish_score += 3
                momentum_state = "weakening"
                key_signals.append("Bearish MACD alignment")

            if previous["macd"] <= previous["macd_signal"] and latest_macd > latest_macd_signal:
                key_signals.append("Bullish MACD crossover")
            elif previous["macd"] >= previous["macd_signal"] and latest_macd < latest_macd_signal:
                key_signals.append("Bearish MACD crossover")

            recent = df.tail(min(20, len(df)))
            higher_high = latest["high"] >= recent["high"].max()
            lower_low = latest["low"] <= recent["low"].min()

            if higher_high and trend_direction == "bullish":
                bullish_score += 1
                market_structure = "higher-high breakout"
                key_signals.append("Bullish market structure")
            elif lower_low and trend_direction == "bearish":
                bearish_score += 1
                market_structure = "lower-low breakdown"
                key_signals.append("Bearish market structure")
            else:
                market_structure = "range-bound"

            returns = df["close"].pct_change().dropna()
            volatility = float(returns.std()) if not returns.empty else 0.0

            if volatility < VOLATILITY_THRESHOLDS["low"]:
                volatility_state = "low"
            elif volatility < VOLATILITY_THRESHOLDS["moderate"]:
                volatility_state = "moderate"
            else:
                volatility_state = "high"

            total_score = bullish_score + bearish_score
            dominant_score = max(bullish_score, bearish_score)
            confidence = int((dominant_score / total_score) * 100) if total_score else 0

            if volatility > risk_config["max_volatility"]:
                confidence -= int(risk_config["confidence_penalty"])
                key_signals.append(
                    f"Volatility exceeds {resolved_risk_tolerance} risk threshold"
                )

            confidence = min(max(confidence, 0), 100)

            if bullish_score > bearish_score:
                market_regime = "bullish trending"
            elif bearish_score > bullish_score:
                market_regime = "bearish trending"
            else:
                market_regime = "sideways/ranging"

            return {

                "success": True,

                "market_regime": market_regime,

                "trend_direction": trend_direction,

                "momentum_state": momentum_state,

                "volatility": volatility_state,
                "volatility_value": volatility,
                "market_structure": market_structure,

                "bullish_score": bullish_score,

                "bearish_score": bearish_score,

                "confidence": confidence,

                "risk_tolerance": resolved_risk_tolerance,
                "risk_context": {
                    "max_volatility": risk_config["max_volatility"],
                    "confidence_penalty": risk_config["confidence_penalty"],
                },
                "configuration": {
                    "trading_style": trading_config["trading_style"],
                    "ema_fast": resolved_ema_fast,
                    "ema_slow": resolved_ema_slow,
                    "ema_fast_column": ema_fast_col,
                    "ema_slow_column": ema_slow_col,
                },

                "key_signals": key_signals
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
