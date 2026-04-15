"""Compatibility wrapper for backend configuration imports."""

from .scanner_config import (  # noqa: F401
    DEFAULT_INTERVAL,
    DEFAULT_PERIOD,
    DEFAULT_UNIVERSE_SIZE,
    FALLBACK_UNIVERSE_SIZE,
    MAX_DEFAULT_UNIVERSE_SIZE,
    SUPPORTED_UNIVERSE_SIZES,
    normalize_universe_size,
)
from .universe_config import (  # noqa: F401
    FALLBACK_SYMBOLS,
    SYMBOL_GROUPS,
    US_RECOMMENDATION_UNIVERSE,
    get_default_symbols,
    get_symbols_for_group,
)
