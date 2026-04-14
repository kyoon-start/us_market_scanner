"""Ranking pipeline for stock recommendations."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from .data_loader import load_daily_stock_data, load_daily_stock_data_bulk, sanitize_symbols
from .indicators import add_indicators
from .scorer import build_recommendation, has_required_history
from .universe_config import get_default_symbols


logger = logging.getLogger(__name__)


def analyze_symbol(symbol: str, historical_data: pd.DataFrame | None = None) -> dict[str, Any] | None:
    """Load, enrich, and score one symbol."""
    logger.debug("Processing symbol %s", symbol)

    try:
        symbol_data = historical_data if historical_data is not None else load_daily_stock_data(symbol=symbol)
        if symbol_data.empty:
            logger.warning("Skipping %s because no historical data was returned", symbol)
            return None

        enriched_data = add_indicators(symbol_data)
        if enriched_data.empty:
            logger.warning("Skipping %s because indicator enrichment returned no rows", symbol)
            return None

        latest_row = enriched_data.iloc[-1]

        if not has_required_history(latest_row, ("MA20", "MA60", "MA120", "VolumeAverage20", "RSI")):
            logger.warning("Skipping %s because it lacks enough lookback history", symbol)
            return None

        recommendation = build_recommendation(symbol=symbol, dataframe=enriched_data, latest_row=latest_row)
        logger.debug(
            "Finished %s with swing score %s and long score %s (probabilities: %s, %s)",
            symbol,
            recommendation["swing"]["score"],
            recommendation["long"]["score"],
            recommendation["swing"]["probability"],
            recommendation["long"]["probability"],
        )
        return recommendation
    except Exception:
        logger.exception("Skipping %s due to processing failure", symbol)
        return None


def _analyze_preloaded_symbol(
    historical_data_map: dict[str, pd.DataFrame],
    symbol: str,
) -> dict[str, Any] | None:
    """Adapter for concurrent symbol processing with preloaded data."""
    return analyze_symbol(symbol, historical_data_map.get(symbol))


def _analyze_symbols_parallel(
    symbols: list[str],
    historical_data_map: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Run per-symbol indicator and scoring work concurrently."""
    if len(symbols) <= 1:
        recommendation = analyze_symbol(symbols[0], historical_data_map.get(symbols[0])) if symbols else None
        return [recommendation] if recommendation is not None else []

    max_workers = min(8, len(symbols))
    analysis_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        recommendations = list(
            executor.map(lambda symbol: _analyze_preloaded_symbol(historical_data_map, symbol), symbols)
        )

    filtered_recommendations = [recommendation for recommendation in recommendations if recommendation is not None]
    logger.info(
        "Symbol analysis completed in %.2f seconds (symbols=%d, workers=%d, successful=%d)",
        time.perf_counter() - analysis_start,
        len(symbols),
        max_workers,
        len(filtered_recommendations),
    )
    return filtered_recommendations


def rank_recommendations(symbols: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Return top recommendations for swing and long-term setups."""
    ranking_start = time.perf_counter()
    sanitized_symbols = sanitize_symbols(symbols)
    if not sanitized_symbols:
        sanitized_symbols = get_default_symbols()

    logger.info("Ranking recommendations for %d symbols", len(sanitized_symbols))
    historical_data_map = load_daily_stock_data_bulk(sanitized_symbols)
    analyzed_symbols = _analyze_symbols_parallel(sanitized_symbols, historical_data_map)

    swing_ranked = sorted(
        (item["swing"] for item in analyzed_symbols),
        key=lambda item: item["score"],
        reverse=True,
    )[:3]
    long_ranked = sorted(
        (item["long"] for item in analyzed_symbols),
        key=lambda item: item["score"],
        reverse=True,
    )[:3]

    logger.info(
        "Recommendation ranking completed in %.2f seconds (symbols=%d, analyzed=%d)",
        time.perf_counter() - ranking_start,
        len(sanitized_symbols),
        len(analyzed_symbols),
    )
    return {"swing": swing_ranked, "long": long_ranked}
