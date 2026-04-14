"""Stock detail service helpers."""

from __future__ import annotations

from typing import Any

from .data_loader import load_daily_stock_data, sanitize_symbols
from .indicators import add_indicators
from .scorer import build_recommendation, has_required_history


class StockDetailError(Exception):
    """Base error for stock detail lookups."""


class InvalidSymbolError(StockDetailError):
    """Raised when a symbol is missing or malformed."""


class StockNotFoundError(StockDetailError):
    """Raised when a symbol cannot be analyzed safely."""


def _build_price_history(symbol_data) -> list[dict[str, float | str]]:
    """Return the last 30 trading-day closes for charting."""
    recent_history = symbol_data.tail(30)
    return [
        {
            "date": index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index),
            "close": float(close_value),
        }
        for index, close_value in zip(recent_history.index, recent_history["Close"], strict=False)
    ]


def get_stock_detail(symbol: str) -> dict[str, Any]:
    """Return latest price and both recommendation views for one symbol."""
    sanitized_symbols = sanitize_symbols([symbol])
    if not sanitized_symbols:
        raise InvalidSymbolError("A valid stock symbol is required.")

    normalized_symbol = sanitized_symbols[0]
    symbol_data = load_daily_stock_data(normalized_symbol)
    if symbol_data.empty:
        raise StockNotFoundError(f"No historical data was found for symbol '{normalized_symbol}'.")

    enriched_data = add_indicators(symbol_data)
    if enriched_data.empty:
        raise StockNotFoundError(f"Not enough market data is available for symbol '{normalized_symbol}'.")

    latest_row = enriched_data.iloc[-1]
    if not has_required_history(latest_row, ("MA20", "MA60", "MA120", "VolumeAverage20", "RSI")):
        raise StockNotFoundError(
            f"Symbol '{normalized_symbol}' does not have enough lookback history for scoring."
        )

    recommendation = build_recommendation(
        symbol=normalized_symbol,
        dataframe=enriched_data,
        latest_row=latest_row,
    )

    latest_close = latest_row.get("Close")
    if latest_close is None:
        raise StockNotFoundError(f"Latest close price is unavailable for symbol '{normalized_symbol}'.")

    return {
        "symbol": normalized_symbol,
        "latest_close_price": float(latest_close),
        "swing_score": recommendation["swing"]["score"],
        "long_term_score": recommendation["long"]["score"],
        "swing_probability": recommendation["swing"]["probability"],
        "long_term_probability": recommendation["long"]["probability"],
        "swing_reasons": recommendation["swing"]["reason"],
        "long_term_reasons": recommendation["long"]["reason"],
        "price_history": _build_price_history(symbol_data),
    }