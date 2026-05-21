"""Centralized deterministic trading configuration.

Frontend selections should be normalized here before they reach backend tools.
The tools stay generic: this module decides periods, intervals, indicator
lengths, volatility thresholds, and risk penalties.
"""

from typing import Any


DEFAULT_TRADING_STYLE = "swing"
DEFAULT_RISK_TOLERANCE = "moderate"


TRADING_CONFIGS: dict[str, dict[str, Any]] = {
    "swing": {
        "period": "6mo",
        "interval": "1d",
        "ema_fast": 20,
        "ema_slow": 50,
        "rsi_length": 14,
        "news_days": 30,
        "sentiment_lookback_hours": 24 * 30,
        "sentiment_max_articles": 50,
        "sentiment_max_events": 25,
        "sentiment_focus": "earnings, macroeconomic shifts, rate outlook, institutional sentiment, and broader market narratives",
        "sentiment_compression": "broad",
    },
    "last_3_days": {
        "period": "7d",
        "interval": "15m",
        "ema_fast": 9,
        "ema_slow": 20,
        "rsi_length": 7,
        "news_days": 3,
        "sentiment_lookback_hours": 72,
        "sentiment_max_articles": 25,
        "sentiment_max_events": 12,
        "sentiment_focus": "breaking news, analyst actions, sudden macro reactions, and short-term catalysts",
        "sentiment_compression": "aggressive",
    },
}


RISK_CONFIGS: dict[str, dict[str, float | int]] = {
    "low": {
        "max_volatility": 0.02,
        "confidence_penalty": 20,
    },
    "moderate": {
        "max_volatility": 0.03,
        "confidence_penalty": 10,
    },
    "high": {
        "max_volatility": 0.05,
        "confidence_penalty": 5,
    },
}


VOLATILITY_THRESHOLDS: dict[str, float] = {
    "low": 0.01,
    "moderate": 0.03,
}


def get_trading_config(trading_style: str | None) -> dict[str, Any]:
    normalized_style = (trading_style or DEFAULT_TRADING_STYLE).lower()
    return {
        "trading_style": normalized_style
        if normalized_style in TRADING_CONFIGS
        else DEFAULT_TRADING_STYLE,
        **TRADING_CONFIGS.get(normalized_style, TRADING_CONFIGS[DEFAULT_TRADING_STYLE]),
    }


def get_risk_config(risk_tolerance: str | None) -> dict[str, float | int | str]:
    normalized_risk = (risk_tolerance or DEFAULT_RISK_TOLERANCE).lower()
    return {
        "risk_tolerance": normalized_risk
        if normalized_risk in RISK_CONFIGS
        else DEFAULT_RISK_TOLERANCE,
        **RISK_CONFIGS.get(normalized_risk, RISK_CONFIGS[DEFAULT_RISK_TOLERANCE]),
    }


def get_pipeline_config(
    asset_type: str,
    ticker: str,
    trading_style: str | None = DEFAULT_TRADING_STYLE,
    risk_tolerance: str | None = DEFAULT_RISK_TOLERANCE,
) -> dict[str, Any]:
    """Convert frontend inputs into deterministic backend execution params."""

    trading_config = get_trading_config(trading_style)
    risk_config = get_risk_config(risk_tolerance)

    return {
        "asset_type": asset_type,
        "ticker": ticker.upper(),
        **trading_config,
        **risk_config,
        "volatility_thresholds": VOLATILITY_THRESHOLDS.copy(),
    }


def get_sentiment_config(trading_style: str | None) -> dict[str, Any]:
    """Return the sentiment-specific execution parameters for a trading style."""

    config = get_trading_config(trading_style)
    return {
        "trading_style": config["trading_style"],
        "news_days": config["news_days"],
        "sentiment_lookback_hours": config["sentiment_lookback_hours"],
        "sentiment_max_articles": config["sentiment_max_articles"],
        "sentiment_max_events": config["sentiment_max_events"],
        "sentiment_focus": config["sentiment_focus"],
        "sentiment_compression": config["sentiment_compression"],
    }
