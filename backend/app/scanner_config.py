"""Central scanner configuration for universe sizing, caching, and batching."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

SUPPORTED_UNIVERSE_SIZES = (100, 300, 1000)
FALLBACK_UNIVERSE_SIZE = 100
DEFAULT_UNIVERSE_SIZE = 300
MAX_DEFAULT_UNIVERSE_SIZE = max(SUPPORTED_UNIVERSE_SIZES)

DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"
RECOMMENDATION_TOP_N = 3

RAW_DATA_CACHE_TTL_SECONDS = 300
FAILED_DATA_CACHE_TTL_SECONDS = 90
SYMBOL_ANALYSIS_CACHE_TTL_SECONDS = 300
RECOMMENDATION_CACHE_TTL_SECONDS = 120

DOWNLOAD_CHUNK_SIZE = 150
DOWNLOAD_MAX_WORKERS = 4
DOWNLOAD_RETRY_SYMBOL_LIMIT = 25
ANALYSIS_MAX_WORKERS = 8
ANALYSIS_PARALLEL_THRESHOLD = 128
INDICATOR_CACHE_TTL_SECONDS = 300


def normalize_universe_size(universe_size: int | None) -> int:
    """Return a supported universe size with a stable default fallback."""
    if universe_size in SUPPORTED_UNIVERSE_SIZES:
        return universe_size

    if universe_size is not None:
        logger.warning(
            "Unsupported universe size '%s', using default size %d instead",
            universe_size,
            DEFAULT_UNIVERSE_SIZE,
        )
    return DEFAULT_UNIVERSE_SIZE
