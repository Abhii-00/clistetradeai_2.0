import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Type
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import yfinance as yf

from clistetradeai.config.trading_config import get_sentiment_config


class SentimentDataFetcherInput(BaseModel):
    asset_type: str = Field(..., description="Asset class, such as stock or forex")
    ticker: str = Field(..., description="Stock ticker or forex pair")
    trading_style: str | None = Field(default=None, description="Frontend trading style")
    company_name: str | None = Field(default=None, description="Optional company name for better news matching")
    max_articles: int | None = Field(default=None, description="Optional article fetch limit override")
    max_events: int | None = Field(default=None, description="Optional economic event limit override")


class SentimentDataFetcherTool(BaseTool):
    name: str = "Sentiment Data Fetcher Tool"
    description: str = (
        "Fetches raw financial news and macroeconomic events for a selected "
        "asset and timeframe. It does not summarize or interpret sentiment."
    )
    args_schema: Type[BaseModel] = SentimentDataFetcherInput

    def _run(
        self,
        asset_type: str,
        ticker: str,
        trading_style: str | None = None,
        company_name: str | None = None,
        max_articles: int | None = None,
        max_events: int | None = None,
    ) -> dict:
        config = get_sentiment_config(trading_style)
        resolved_max_articles = max_articles or int(config["sentiment_max_articles"])
        resolved_max_events = max_events or int(config["sentiment_max_events"])
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=int(config["sentiment_lookback_hours"]))

        query = self._build_query(asset_type=asset_type, ticker=ticker, company_name=company_name)
        errors: list[str] = []
        articles = self._fetch_newsapi_articles(
            query=query,
            start_time=start_time,
            end_time=end_time,
            max_articles=resolved_max_articles,
            errors=errors,
        )
        if not articles:
            articles = self._fetch_yfinance_news(
                ticker=ticker,
                start_time=start_time,
                max_articles=resolved_max_articles,
                errors=errors,
            )
        events = self._fetch_finnhub_events(
            start_time=start_time,
            end_time=end_time,
            max_events=resolved_max_events,
            errors=errors,
        )

        return {
            "success": bool(articles or events),
            "asset_type": asset_type.lower(),
            "ticker": ticker.upper(),
            "trading_style": config["trading_style"],
            "timeframe": {
                "lookback_hours": config["sentiment_lookback_hours"],
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "query": query,
            "total_articles": len(articles),
            "total_events": len(events),
            "articles": articles,
            "economic_events": events,
            "errors": errors,
        }

    def _build_query(self, asset_type: str, ticker: str, company_name: str | None) -> str:
        normalized_asset = asset_type.lower()
        normalized_ticker = ticker.upper().replace("/", "")

        if normalized_asset == "forex":
            pair_terms = [
                ticker.upper(),
                normalized_ticker,
                *self._forex_terms(normalized_ticker),
                "central bank",
                "interest rates",
                "inflation",
            ]
            return " OR ".join(dict.fromkeys(term for term in pair_terms if term))

        stock_terms = [ticker.upper(), company_name or "", "earnings", "analyst", "guidance"]
        return " OR ".join(dict.fromkeys(term for term in stock_terms if term))

    def _fetch_newsapi_articles(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        max_articles: int,
        errors: list[str],
    ) -> list[dict[str, Any]]:
        api_key = os.getenv("NEWSAPI_API_KEY")
        if not api_key:
            errors.append("NEWSAPI_API_KEY is not configured")
            return []

        params = urlencode(
            {
                "q": query,
                "from": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(max_articles, 100),
                "apiKey": api_key,
            }
        )
        url = f"https://newsapi.org/v2/everything?{params}"
        payload = self._get_json(url, errors)
        raw_articles = payload.get("articles", []) if payload else []

        return [
            {
                "type": "news_article",
                "title": article.get("title") or "",
                "description": article.get("description") or "",
                "published_at": article.get("publishedAt") or "",
                "source": (article.get("source") or {}).get("name") or "",
                "url": article.get("url") or "",
            }
            for article in raw_articles[:max_articles]
            if article.get("title") or article.get("description")
        ]

    def _fetch_yfinance_news(
        self,
        ticker: str,
        start_time: datetime,
        max_articles: int,
        errors: list[str],
    ) -> list[dict[str, Any]]:
        try:
            news_symbol = f"{ticker}=X" if len(ticker) == 6 and not ticker.endswith("=X") else ticker
            news_items = yf.Ticker(news_symbol).news or []
        except Exception as exc:
            errors.append(f"yfinance news fallback failed: {exc}")
            return []

        articles: list[dict[str, Any]] = []
        for item in news_items:
            content = item.get("content", item)
            publish_time = content.get("pubDate") or content.get("displayTime") or item.get("providerPublishTime")
            published_at = self._normalize_publish_time(publish_time)

            if published_at and published_at < start_time:
                continue

            click_through = content.get("clickThroughUrl") or content.get("canonicalUrl") or {}
            source = content.get("provider") or content.get("publisher") or item.get("publisher") or ""
            articles.append(
                {
                    "type": "news_article",
                    "title": content.get("title") or item.get("title") or "",
                    "description": content.get("summary") or item.get("summary") or "",
                    "published_at": published_at.isoformat() if published_at else "",
                    "source": source.get("displayName", source) if isinstance(source, dict) else source,
                    "url": click_through.get("url", "") if isinstance(click_through, dict) else str(click_through),
                }
            )

        return [
            article
            for article in articles[:max_articles]
            if article["title"] or article["description"]
        ]

    def _normalize_publish_time(self, value: Any) -> datetime | None:
        if isinstance(value, int | float):
            return datetime.fromtimestamp(value, UTC)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _fetch_finnhub_events(
        self,
        start_time: datetime,
        end_time: datetime,
        max_events: int,
        errors: list[str],
    ) -> list[dict[str, Any]]:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            errors.append("FINNHUB_API_KEY is not configured")
            return []

        params = urlencode(
            {
                "from": start_time.strftime("%Y-%m-%d"),
                "to": end_time.strftime("%Y-%m-%d"),
                "token": api_key,
            }
        )
        url = f"https://finnhub.io/api/v1/calendar/economic?{params}"
        payload = self._get_json(url, errors)
        raw_events = payload.get("economicCalendar", []) if payload else []
        relevant_events = [
            event
            for event in raw_events
            if self._is_relevant_macro_event(event)
        ]

        return [
            {
                "type": "economic_event",
                "event": event.get("event") or "",
                "country": event.get("country") or "",
                "date": event.get("date") or "",
                "period": event.get("period") or "",
                "actual": event.get("actual"),
                "estimate": event.get("estimate"),
                "previous": event.get("prev"),
                "impact": event.get("impact") or "",
            }
            for event in relevant_events[:max_events]
        ]

    def _get_json(self, url: str, errors: list[str]) -> dict[str, Any]:
        try:
            request = Request(url, headers={"User-Agent": "clistetradeai/0.1"})
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            errors.append(f"HTTP {exc.code} from {quote(url.split('?')[0], safe=':/')}")
        except (TimeoutError, URLError, json.JSONDecodeError) as exc:
            errors.append(f"API request failed: {exc}")
        return {}

    def _is_relevant_macro_event(self, event: dict[str, Any]) -> bool:
        event_text = f"{event.get('event', '')} {event.get('country', '')}".lower()
        keywords = [
            "cpi",
            "inflation",
            "fomc",
            "interest rate",
            "rate decision",
            "nonfarm",
            "nfp",
            "gdp",
            "pmi",
            "unemployment",
            "retail sales",
            "central bank",
        ]
        return any(keyword in event_text for keyword in keywords)

    def _forex_terms(self, ticker: str) -> list[str]:
        currencies = {
            "USD": "US dollar Federal Reserve",
            "EUR": "euro ECB",
            "GBP": "British pound Bank of England",
            "JPY": "Japanese yen Bank of Japan",
            "CAD": "Canadian dollar Bank of Canada",
            "AUD": "Australian dollar RBA",
            "NZD": "New Zealand dollar RBNZ",
            "CHF": "Swiss franc SNB",
        }
        return [term for code, term in currencies.items() if code in ticker]
