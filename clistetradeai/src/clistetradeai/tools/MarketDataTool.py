from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import yfinance as yf
import pandas as pd

from clistetradeai.config.trading_config import get_trading_config


class MarketDataInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker or forex pair")
    period: str | None = Field(default=None, description="Time period like 7d, 1mo, 6mo, 1y")
    interval: str | None = Field(default=None, description="Data interval like 1m, 15m, 1h, 1d")
    trading_style: str | None = Field(default=None, description="Frontend trading style")


class MarketDataTool(BaseTool):
    name: str = "Market Data Fetcher Tool"
    description: str = (
        "Fetches OHLCV market data for stocks or forex pairs "
        "using yfinance and returns cleaned JSON records."
    )

    args_schema: Type[BaseModel] = MarketDataInput

    def _run(self, ticker: str, period: str | None = None, interval: str | None = None, trading_style: str | None = None) -> dict:
        config = get_trading_config(trading_style)
        resolved_period = period or config["period"]
        resolved_interval = interval or config["interval"]

        try:
            data = yf.download(
                tickers=ticker,
                period=resolved_period,
                interval=resolved_interval,
                auto_adjust=False,
                progress=False
            )

            if data.empty:
                return {
                    "success": False,
                    "error": f"No data found for ticker: {ticker}",
                    "ticker": ticker,
                    "period": resolved_period,
                    "interval": resolved_interval,
                }

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [
                    next((str(part) for part in column if str(part).lower() in {"open", "high", "low", "close", "adj close", "volume"}), None)
                    for column in data.columns
                ]
                if any(col is None for col in data.columns):
                    return {
                        "success": False,
                        "error": f"Could not flatten MultiIndex columns: {list(data.columns)}",
                        "ticker": ticker,
                    }

            data = data.reset_index()
            data.columns = [str(col).strip().lower().replace(" ", "_") for col in data.columns]

            if "datetime" in data.columns and "date" not in data.columns:
                data = data.rename(columns={"datetime": "date"})

            required_columns = ["date", "open", "high", "low", "close", "volume"]
            missing_columns = [column for column in required_columns if column not in data.columns]

            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required OHLCV columns: {missing_columns}",
                    "ticker": ticker,
                    "period": resolved_period,
                    "interval": resolved_interval,
                }

            data = data[required_columns]

            for column in ["open", "high", "low", "close", "volume"]:
                data[column] = pd.to_numeric(data[column], errors="coerce")

            data = data.dropna(subset=required_columns)
            data = data[(data[["open", "high", "low", "close"]] > 0).all(axis=1)]
            data = data[data["volume"] >= 0]
            data["date"] = pd.to_datetime(data["date"], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
            data = data.dropna(subset=["date"])

            records = data.to_dict(orient="records")

            return {
                "success": True,
                "ticker": ticker,
                "period": resolved_period,
                "interval": resolved_interval,
                "trading_style": config["trading_style"],
                "total_rows": len(records),
                "data": records
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

