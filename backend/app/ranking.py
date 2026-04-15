"""Ranking pipeline for stock recommendations."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from heapq import nlargest
from typing import Any

import pandas as pd

from .cache import TTLCache
from .data_loader import (
    BulkDownloadResult,
    load_daily_stock_data,
    load_daily_stock_data_bulk_with_stats,
    sanitize_symbols,
)
from .indicators import add_indicators
from .scanner_config import (
    ANALYSIS_MAX_WORKERS,
    ANALYSIS_PARALLEL_THRESHOLD,
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    RECOMMENDATION_CACHE_TTL_SECONDS,
    RECOMMENDATION_TOP_N,
    SYMBOL_ANALYSIS_CACHE_TTL_SECONDS,
)
from .scorer import build_recommendation, has_required_history
from .universe_config import get_default_symbols


logger = logging.getLogger(__name__)

_SYMBOL_ANALYSIS_CACHE: TTLCache[dict[str, Any] | None] = TTLCache()
_RECOMMENDATION_CACHE: TTLCache[dict[str, list[dict[str, Any]]]] = TTLCache()


def _frame_fingerprint(dataframe: pd.DataFrame) -> tuple[int, str, float | None, float | None]:
    """Create a lightweight fingerprint for unchanged historical data."""
    if dataframe.empty:
        return (0, "", None, None)

    last_index = dataframe.index[-1]
    last_close = dataframe["Close"].iloc[-1] if "Close" in dataframe.columns else None
    last_volume = dataframe["Volume"].iloc[-1] if "Volume" in dataframe.columns else None

    return (
        len(dataframe),
        str(last_index),
        None if pd.isna(last_close) else round(float(last_close), 6),
        None if pd.isna(last_volume) else round(float(last_volume), 2),
    )


def _symbol_analysis_cache_key(symbol: str, historical_data: pd.DataFrame) -> tuple[object, ...]:
    """Build a stable cache key for one symbol's computed recommendation."""
    return ("symbol-analysis", symbol.upper(), *_frame_fingerprint(historical_data))


def analyze_symbol(symbol: str, historical_data: pd.DataFrame | None = None) -> dict[str, Any] | None:
    """Load, enrich, and score one symbol."""
    logger.debug("Processing symbol %s", symbol)

    try:
        symbol_data = historical_data if historical_data is not None else load_daily_stock_data(symbol=symbol)
        if symbol_data.empty:
            logger.warning("Skipping %s because no historical data was returned", symbol)
            return None

        cache_key = _symbol_analysis_cache_key(symbol, symbol_data)
        cached_recommendation = _SYMBOL_ANALYSIS_CACHE.get(cache_key)
        if cached_recommendation is not None:
            logger.debug("Symbol analysis cache hit for %s", symbol)
            return cached_recommendation

        enriched_data = add_indicators(symbol_data)
        if enriched_data.empty:
            logger.warning("Skipping %s because indicator enrichment returned no rows", symbol)
            _SYMBOL_ANALYSIS_CACHE.set(cache_key, None, SYMBOL_ANALYSIS_CACHE_TTL_SECONDS)
            return None

        latest_row = enriched_data.iloc[-1]

        if not has_required_history(latest_row, ("MA20", "MA60", "MA120", "VolumeAverage20", "RSI")):
            logger.warning("Skipping %s because it lacks enough lookback history", symbol)
            _SYMBOL_ANALYSIS_CACHE.set(cache_key, None, SYMBOL_ANALYSIS_CACHE_TTL_SECONDS)
            return None

        recommendation = build_recommendation(symbol=symbol, dataframe=enriched_data, latest_row=latest_row)
        _SYMBOL_ANALYSIS_CACHE.set(cache_key, recommendation, SYMBOL_ANALYSIS_CACHE_TTL_SECONDS)
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

    if len(symbols) >= ANALYSIS_PARALLEL_THRESHOLD:
        analysis_start = time.perf_counter()
        recommendations = [
            _analyze_preloaded_symbol(historical_data_map, symbol)
            for symbol in symbols
        ]
        filtered_recommendations = [recommendation for recommendation in recommendations if recommendation is not None]
        logger.info(
            "Symbol analysis completed in %.2f seconds (symbols=%d, workers=%d, successful=%d)",
            time.perf_counter() - analysis_start,
            len(symbols),
            1,
            len(filtered_recommendations),
        )
        return filtered_recommendations

    max_workers = min(ANALYSIS_MAX_WORKERS, len(symbols))
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


def _recommendation_cache_key(
    symbols: list[str],
    universe_size: int | None,
    period: str,
    interval: str,
) -> tuple[object, ...]:
    """Build a stable cache key for a recommendations request."""
    return (
        "recommendations",
        universe_size,
        period,
        interval,
        tuple(symbols),
    )


def _rank_items(analyzed_symbols: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build the final top-N swing and long recommendation payload."""
    swing_ranked = nlargest(
        RECOMMENDATION_TOP_N,
        (item["swing"] for item in analyzed_symbols),
        key=lambda item: item["score"],
    )
    long_ranked = nlargest(
        RECOMMENDATION_TOP_N,
        (item["long"] for item in analyzed_symbols),
        key=lambda item: item["score"],
    )
    return {"swing": swing_ranked, "long": long_ranked}


def rank_recommendations(
    symbols: list[str] | None = None,
    *,
    universe_size: int | None = None,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> dict[str, list[dict[str, Any]]]:
    """Return top recommendations for swing and long-term setups."""
    ranking_start = time.perf_counter()
    sanitized_symbols = sanitize_symbols(symbols or [])
    if not sanitized_symbols:
        sanitized_symbols = get_default_symbols(universe_size)

    cache_key = _recommendation_cache_key(sanitized_symbols, universe_size, period, interval)
    cached_recommendations = _RECOMMENDATION_CACHE.get(cache_key)
    if cached_recommendations is not None:
        logger.info(
            "Recommendation cache hit (symbols=%d, universe_size=%s, period=%s, interval=%s)",
            len(sanitized_symbols),
            universe_size,
            period,
            interval,
        )
        return cached_recommendations

    logger.info(
        "Recommendation cache miss (symbols=%d, universe_size=%s, period=%s, interval=%s)",
        len(sanitized_symbols),
        universe_size,
        period,
        interval,
    )
    logger.info("Ranking recommendations for %d symbols", len(sanitized_symbols))

    scoring_start = time.perf_counter()
    download_result: BulkDownloadResult = load_daily_stock_data_bulk_with_stats(
        sanitized_symbols,
        period=period,
        interval=interval,
    )
    analyzed_symbols = _analyze_symbols_parallel(sanitized_symbols, download_result.data)
    scored_payload = _rank_items(analyzed_symbols)
    scoring_seconds = time.perf_counter() - scoring_start

    requested = download_result.stats.requested
    ranked = len(analyzed_symbols)
    skipped = max(download_result.stats.skipped, requested - ranked)
    logger.info(
        "Recommendation ranking completed in %.2f seconds (requested=%d, downloaded_successfully=%d, skipped=%d, ranked=%d, download_time=%.2f, scoring_time=%.2f)",
        time.perf_counter() - ranking_start,
        requested,
        download_result.stats.downloaded_successfully + download_result.stats.cache_hits,
        skipped,
        ranked,
        download_result.download_seconds,
        max(0.0, scoring_seconds - download_result.download_seconds),
    )

    _RECOMMENDATION_CACHE.set(cache_key, scored_payload, RECOMMENDATION_CACHE_TTL_SECONDS)
    return scored_payload
