"""Utilities for fetching and normalizing market data."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf

from .cache import TTLCache
from .scanner_config import (
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_MAX_WORKERS,
    DOWNLOAD_RETRY_SYMBOL_LIMIT,
    FAILED_DATA_CACHE_TTL_SECONDS,
    RAW_DATA_CACHE_TTL_SECONDS,
)


logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
_DATA_CACHE: TTLCache[pd.DataFrame] = TTLCache()


@dataclass(slots=True)
class DownloadStats:
    """Operational stats for one bulk market-data request."""

    requested: int
    cache_hits: int
    cache_misses: int
    downloaded_successfully: int
    skipped: int


@dataclass(slots=True)
class BulkDownloadResult:
    """Bulk market-data payload plus stats and timing info."""

    data: dict[str, pd.DataFrame]
    stats: DownloadStats
    download_seconds: float
    total_seconds: float


def _cache_key(symbol: str, period: str, interval: str) -> tuple[str, str, str]:
    """Build a stable cache key for a market data request."""
    return symbol.upper(), period, interval


def _get_cached_data(symbol: str, period: str, interval: str) -> pd.DataFrame | None:
    """Return cached data when it is still fresh."""
    cached = _DATA_CACHE.get(_cache_key(symbol, period, interval))
    if cached is None:
        return None
    return cached.copy()


def _set_cached_data(
    symbol: str,
    period: str,
    interval: str,
    dataframe: pd.DataFrame,
    ttl_seconds: int,
) -> None:
    """Store normalized data in the in-memory cache."""
    _DATA_CACHE.set(
        _cache_key(symbol, period, interval),
        dataframe.copy(),
        ttl_seconds,
    )


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
        tickers=" ".join(symbols),
        period=period,
        interval=interval,
        auto_adjust=True,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def _chunk_symbols(symbols: list[str], chunk_size: int) -> list[list[str]]:
    """Split a symbol list into stable chunk sizes for bulk downloads."""
    return [symbols[index : index + chunk_size] for index in range(0, len(symbols), chunk_size)]


def _download_chunk(symbols: list[str], period: str, interval: str) -> dict[str, pd.DataFrame]:
    """Download and normalize one chunk of symbols."""
    downloaded_data = _download_batch(symbols, period, interval)
    multiple_symbols = len(symbols) > 1
    return {
        symbol: _extract_symbol_frame(downloaded_data, symbol, multiple_symbols)
        for symbol in symbols
    }


def _download_missing_symbols(
    missing_symbols: list[str],
    period: str,
    interval: str,
) -> tuple[dict[str, pd.DataFrame], float]:
    """Download uncached symbols with chunking and limited individual retries."""
    if not missing_symbols:
        return {}, 0.0

    download_start = time.perf_counter()
    downloaded_results: dict[str, pd.DataFrame] = {}
    retry_symbols: list[str] = []
    chunks = _chunk_symbols(missing_symbols, DOWNLOAD_CHUNK_SIZE)

    logger.info(
        "Market data cache miss for %d symbols; downloading in %d chunk(s)",
        len(missing_symbols),
        len(chunks),
    )

    max_workers = min(DOWNLOAD_MAX_WORKERS, len(chunks))
    if max_workers <= 1:
        for chunk in chunks:
            try:
                downloaded_results.update(_download_chunk(chunk, period, interval))
            except Exception:
                logger.exception("Bulk download failed for chunk of %d symbols", len(chunk))
                retry_symbols.extend(chunk)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_download_chunk, chunk, period, interval): chunk
                for chunk in chunks
            }
            for future in as_completed(future_map):
                chunk = future_map[future]
                try:
                    downloaded_results.update(future.result())
                except Exception:
                    logger.exception("Bulk download failed for chunk of %d symbols", len(chunk))
                    retry_symbols.extend(chunk)

    missing_after_bulk = [
        symbol for symbol in missing_symbols
        if downloaded_results.get(symbol, pd.DataFrame(columns=REQUIRED_COLUMNS)).empty
    ]
    for symbol in missing_after_bulk:
        if symbol not in retry_symbols:
            retry_symbols.append(symbol)

    retry_candidates = retry_symbols[:DOWNLOAD_RETRY_SYMBOL_LIMIT]
    if retry_candidates:
        logger.info("Retrying %d symbol(s) individually after bulk download gaps", len(retry_candidates))

    for symbol in retry_candidates:
        symbol_start = time.perf_counter()
        try:
            single_symbol_data = _download_batch([symbol], period, interval)
            downloaded_results[symbol] = _extract_symbol_frame(single_symbol_data, symbol, multiple_symbols=False)
            logger.debug(
                "Downloaded symbol %s individually in %.2f seconds",
                symbol,
                time.perf_counter() - symbol_start,
            )
        except Exception:
            logger.exception("Failed downloading symbol %s", symbol)
            downloaded_results[symbol] = pd.DataFrame(columns=REQUIRED_COLUMNS)

    return downloaded_results, time.perf_counter() - download_start


def load_daily_stock_data_bulk_with_stats(
    symbols: Iterable[str],
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> BulkDownloadResult:
    """Fetch daily stock data for many symbols with caching and batch download."""
    request_start = time.perf_counter()
    sanitized_symbols = sanitize_symbols(symbols)
    if not sanitized_symbols:
        return BulkDownloadResult(
            data={},
            stats=DownloadStats(0, 0, 0, 0, 0),
            download_seconds=0.0,
            total_seconds=0.0,
        )

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

    logger.info(
        "Market data cache %s (requested=%d, hits=%d, misses=%d, period=%s, interval=%s)",
        "hit" if not missing_symbols else "partial-miss",
        len(sanitized_symbols),
        cache_hits,
        len(missing_symbols),
        period,
        interval,
    )

    downloaded_results, download_seconds = _download_missing_symbols(missing_symbols, period, interval)
    for symbol in missing_symbols:
        symbol_frame = downloaded_results.get(symbol, pd.DataFrame(columns=REQUIRED_COLUMNS))
        ttl_seconds = RAW_DATA_CACHE_TTL_SECONDS if not symbol_frame.empty else FAILED_DATA_CACHE_TTL_SECONDS
        _set_cached_data(symbol, period, interval, symbol_frame, ttl_seconds=ttl_seconds)
        results[symbol] = symbol_frame

    final_results = {
        symbol: results.get(symbol, pd.DataFrame(columns=REQUIRED_COLUMNS))
        for symbol in sanitized_symbols
    }
    downloaded_successfully = sum(1 for symbol in missing_symbols if not final_results[symbol].empty)
    skipped = sum(1 for symbol in sanitized_symbols if final_results[symbol].empty)
    total_seconds = time.perf_counter() - request_start

    logger.info(
        "Market data prepared in %.2f seconds (requested=%d, cache_hits=%d, downloaded_successfully=%d, skipped=%d)",
        total_seconds,
        len(sanitized_symbols),
        cache_hits,
        downloaded_successfully,
        skipped,
    )

    return BulkDownloadResult(
        data=final_results,
        stats=DownloadStats(
            requested=len(sanitized_symbols),
            cache_hits=cache_hits,
            cache_misses=len(missing_symbols),
            downloaded_successfully=downloaded_successfully,
            skipped=skipped,
        ),
        download_seconds=download_seconds,
        total_seconds=total_seconds,
    )


def load_daily_stock_data_bulk(
    symbols: Iterable[str],
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> dict[str, pd.DataFrame]:
    """Fetch daily stock data for many symbols with caching and batch download."""
    return load_daily_stock_data_bulk_with_stats(symbols, period=period, interval=interval).data


def load_daily_stock_data(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
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
