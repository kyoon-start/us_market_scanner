"""Utilities for fetching and normalizing market data."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf


logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
CACHE_TTL_SECONDS = 900
FAILED_DOWNLOAD_CACHE_TTL_SECONDS = 120


@dataclass(slots=True)
class CacheEntry:
    """In-memory cached market data entry."""

    dataframe: pd.DataFrame
    expires_at: float


_CACHE_LOCK = threading.Lock()
_DATA_CACHE: dict[tuple[str, str, str], CacheEntry] = {}


def _cache_key(symbol: str, period: str, interval: str) -> tuple[str, str, str]:
    """Build a stable cache key for a market data request."""
    return symbol.upper(), period, interval


def _get_cached_data(symbol: str, period: str, interval: str) -> pd.DataFrame | None:
    """Return cached data when it is still fresh."""
    key = _cache_key(symbol, period, interval)

    with _CACHE_LOCK:
        entry = _DATA_CACHE.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            _DATA_CACHE.pop(key, None)
            return None
        return entry.dataframe.copy()


def _set_cached_data(
    symbol: str,
    period: str,
    interval: str,
    dataframe: pd.DataFrame,
    ttl_seconds: int = CACHE_TTL_SECONDS,
) -> None:
    """Store normalized data in the in-memory cache."""
    key = _cache_key(symbol, period, interval)
    expires_at = time.time() + ttl_seconds

    with _CACHE_LOCK:
        _DATA_CACHE[key] = CacheEntry(dataframe=dataframe.copy(), expires_at=expires_at)


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance columns and keep only the standard OHLCV fields."""
    frame = dataframe.copy()

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [
            " ".join(str(part) for part in column if part).strip()
            for column in frame.columns.to_flat_index()
        ]

    renamed_columns: dict[str, str] = {}
    for column in frame.columns:
        for required in REQUIRED_COLUMNS:
            if column == required or column.startswith(f"{required} "):
                renamed_columns[column] = required
                break

    frame = frame.rename(columns=renamed_columns)
    available_columns = [column for column in REQUIRED_COLUMNS if column in frame.columns]
    frame = frame.loc[:, available_columns]

    for column in available_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "Close" not in frame.columns:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    return frame.dropna(subset=["Close"]).sort_index()


def _extract_symbol_frame(
    downloaded_data: pd.DataFrame,
    symbol: str,
    multiple_symbols: bool,
) -> pd.DataFrame:
    """Extract one symbol's dataframe from yfinance download output."""
    if downloaded_data.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    if not isinstance(downloaded_data.columns, pd.MultiIndex):
        return _normalize_columns(downloaded_data) if not multiple_symbols else pd.DataFrame(columns=REQUIRED_COLUMNS)

    level_zero = downloaded_data.columns.get_level_values(0)
    level_one = downloaded_data.columns.get_level_values(1)

    if symbol in level_zero:
        symbol_frame = downloaded_data.xs(symbol, axis=1, level=0, drop_level=True)
        return _normalize_columns(symbol_frame)

    if symbol in level_one:
        symbol_frame = downloaded_data.xs(symbol, axis=1, level=1, drop_level=True)
        return _normalize_columns(symbol_frame)

    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _download_batch(symbols: list[str], period: str, interval: str) -> pd.DataFrame:
    """Download one batch of symbols from yfinance."""
    return yf.download(
        tickers=symbols,
        period=period,
        interval=interval,
        auto_adjust=True,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def _download_missing_symbols(
    missing_symbols: list[str],
    period: str,
    interval: str,
) -> dict[str, pd.DataFrame]:
    """Download uncached symbols, falling back to per-symbol requests on failure."""
    downloaded_results: dict[str, pd.DataFrame] = {}
    batch_start = time.perf_counter()

    try:
        logger.info("Downloading market data for %d uncached symbols", len(missing_symbols))
        downloaded_data = _download_batch(missing_symbols, period, interval)
        multiple_symbols = len(missing_symbols) > 1

        for symbol in missing_symbols:
            downloaded_results[symbol] = _extract_symbol_frame(downloaded_data, symbol, multiple_symbols)

        logger.info(
            "Bulk market download completed in %.2f seconds for %d symbols",
            time.perf_counter() - batch_start,
            len(missing_symbols),
        )
        return downloaded_results
    except Exception:
        logger.exception("Bulk download failed after %.2f seconds, retrying symbols individually", time.perf_counter() - batch_start)

    for symbol in missing_symbols:
        symbol_start = time.perf_counter()
        try:
            single_symbol_data = _download_batch([symbol], period, interval)
            downloaded_results[symbol] = _extract_symbol_frame(single_symbol_data, symbol, multiple_symbols=False)
            logger.info(
                "Downloaded symbol %s individually in %.2f seconds",
                symbol,
                time.perf_counter() - symbol_start,
            )
        except Exception:
            logger.exception("Failed downloading symbol %s", symbol)
            downloaded_results[symbol] = pd.DataFrame(columns=REQUIRED_COLUMNS)

    return downloaded_results


def load_daily_stock_data_bulk(
    symbols: Iterable[str],
    period: str = "1y",
    interval: str = "1d",
) -> dict[str, pd.DataFrame]:
    """Fetch daily stock data for many symbols with caching and batch download."""
    request_start = time.perf_counter()
    sanitized_symbols = sanitize_symbols(symbols)
    if not sanitized_symbols:
        return {}

    results: dict[str, pd.DataFrame] = {}
    missing_symbols: list[str] = []
    cache_hits = 0

    for symbol in sanitized_symbols:
        cached_data = _get_cached_data(symbol, period, interval)
        if cached_data is not None:
            cache_hits += 1
            results[symbol] = cached_data
        else:
            missing_symbols.append(symbol)

    if missing_symbols:
        downloaded_results = _download_missing_symbols(missing_symbols, period, interval)
        for symbol, symbol_frame in downloaded_results.items():
            ttl_seconds = CACHE_TTL_SECONDS if not symbol_frame.empty else FAILED_DOWNLOAD_CACHE_TTL_SECONDS
            _set_cached_data(symbol, period, interval, symbol_frame, ttl_seconds=ttl_seconds)
            results[symbol] = symbol_frame

    logger.info(
        "Market data prepared in %.2f seconds (symbols=%d, cache_hits=%d, downloaded=%d)",
        time.perf_counter() - request_start,
        len(sanitized_symbols),
        cache_hits,
        len(missing_symbols),
    )
    return {symbol: results.get(symbol, pd.DataFrame(columns=REQUIRED_COLUMNS)) for symbol in sanitized_symbols}


def load_daily_stock_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch daily stock data for a single symbol."""
    return load_daily_stock_data_bulk([symbol], period=period, interval=interval).get(
        symbol.upper(),
        pd.DataFrame(columns=REQUIRED_COLUMNS),
    )


def sanitize_symbols(symbols: Iterable[str]) -> list[str]:
    """Normalize a symbol list while preserving order and uniqueness."""
    seen: set[str] = set()
    cleaned_symbols: list[str] = []

    for symbol in symbols:
        normalized = symbol.strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned_symbols.append(normalized)

    return cleaned_symbols
