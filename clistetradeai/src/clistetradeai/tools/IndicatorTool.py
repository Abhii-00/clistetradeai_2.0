# tools/indicator_tool.py

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any
import pandas as pd
import pandas_ta as ta

from clistetradeai.config.trading_config import get_trading_config


class IndicatorToolInput(BaseModel):

    market_data: List[Dict[str, Any]] | Dict[str, Any] = Field(..., description="Cleaned OHLCV records or MarketDataTool output")

    ema_fast: int | None = None
    ema_slow: int | None = None

    rsi_length: int | None = None
    trading_style: str | None = None


class IndicatorTool(BaseTool):

    name: str = "Technical Indicator Tool"

    description: str = (
        "Computes dynamic technical indicators."
    )

    args_schema: Type[BaseModel] = IndicatorToolInput

    def _run(
        self,
        market_data: List[Dict[str, Any]] | Dict[str, Any],
        ema_fast: int | None = None,
        ema_slow: int | None = None,
        rsi_length: int | None = None,
        trading_style: str | None = None,
    ) -> dict:

        try:
            config = get_trading_config(trading_style)
            resolved_ema_fast = ema_fast or config["ema_fast"]
            resolved_ema_slow = ema_slow or config["ema_slow"]
            resolved_rsi_length = rsi_length or config["rsi_length"]
            records = market_data.get("data", []) if isinstance(market_data, dict) else market_data

            df = pd.DataFrame(records)

            if df.empty:
                return {
                    "success": False,
                    "error": "Empty dataframe"
                }

            numeric_cols = ["open", "high", "low", "close", "volume"]
            missing_columns = [column for column in numeric_cols if column not in df.columns]

            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required OHLCV columns: {missing_columns}"
                }

            for col in numeric_cols:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

            df = df.dropna()

            if len(df) < max(resolved_ema_slow, resolved_rsi_length, 26):
                return {
                    "success": False,
                    "error": "Not enough rows to compute configured indicators",
                    "minimum_rows": max(resolved_ema_slow, resolved_rsi_length, 26),
                    "total_rows": len(df),
                }

            df[f"ema_{resolved_ema_fast}"] = ta.ema(
                df["close"],
                length=resolved_ema_fast
            )

            df[f"ema_{resolved_ema_slow}"] = ta.ema(
                df["close"],
                length=resolved_ema_slow
            )

            df["rsi"] = ta.rsi(
                df["close"],
                length=resolved_rsi_length
            )

            macd = ta.macd(df["close"])
            if macd is None or macd.empty:
                return {
                    "success": False,
                    "error": "Unable to compute MACD"
                }

            macd_cols = list(macd.columns)
            if len(macd_cols) < 3:
                return {
                    "success": False,
                    "error": f"MACD returned unexpected columns: {macd_cols}"
                }

            df["macd"] = macd[macd_cols[0]]
            df["macd_signal"] = macd[macd_cols[1]]
            df["macd_histogram"] = macd[macd_cols[2]]

            df = df.dropna()
            if "date" in df.columns:
                df["date"] = df["date"].astype(str)

            records = df.to_dict(orient="records")

            return {

                "success": True,

                "ema_fast": resolved_ema_fast,
                "ema_slow": resolved_ema_slow,
                "ema_fast_column": f"ema_{resolved_ema_fast}",
                "ema_slow_column": f"ema_{resolved_ema_slow}",

                "rsi_length": resolved_rsi_length,
                "trading_style": config["trading_style"],

                "total_rows": len(records),

                "data": records
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
