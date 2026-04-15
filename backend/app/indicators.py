"""Technical indicator calculations for the stock scanner."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .cache import TTLCache
from .scanner_config import INDICATOR_CACHE_TTL_SECONDS


TRADING_DAYS_IN_YEAR = 252

_INDICATOR_CACHE: TTLCache[pd.DataFrame] = TTLCache()


def _frame_fingerprint(dataframe: pd.DataFrame) -> tuple[int, str, float | None, float | None]:
    """Create a lightweight cache fingerprint for an OHLCV dataframe."""
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


def calculate_rsi(close_series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI using rolling average gains and losses."""
    delta = close_series.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)

    average_gain = gains.rolling(window=period, min_periods=period).mean()
    average_loss = losses.rolling(window=period, min_periods=period).mean()

    relative_strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))

    rsi = rsi.where(~((average_loss == 0) & (average_gain > 0)), 100.0)
    rsi = rsi.where(~((average_loss == 0) & (average_gain == 0)), 50.0)
    return rsi


def calculate_atr(dataframe: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate average true range from OHLC data."""
    previous_close = dataframe["Close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["High"] - dataframe["Low"],
            (dataframe["High"] - previous_close).abs(),
            (dataframe["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean()


def add_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add trend, breakout, return, and volatility inputs for recommendation scoring."""
    if dataframe.empty:
        return dataframe.copy()

    cache_key = ("indicators", *_frame_fingerprint(dataframe))
    cached = _INDICATOR_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    frame = dataframe.copy()
    close = frame["Close"]
    high = frame["High"]
    volume = frame["Volume"]
    zero_safe_close = close.replace(0, np.nan)

    ma20 = close.rolling(window=20, min_periods=20).mean()
    ma60 = close.rolling(window=60, min_periods=60).mean()
    ma120 = close.rolling(window=120, min_periods=120).mean()
    atr14 = calculate_atr(frame, period=14)
    volume_average_20 = volume.rolling(window=20, min_periods=20).mean()
    daily_returns = close.pct_change()
    recent_high_20 = high.rolling(window=20, min_periods=20).max().shift(1)
    high_52_week = high.rolling(window=TRADING_DAYS_IN_YEAR, min_periods=TRADING_DAYS_IN_YEAR).max()

    frame["MA20"] = ma20
    frame["MA60"] = ma60
    frame["MA120"] = ma120
    frame["MA60Prior"] = ma60.shift(5)
    frame["RSI"] = calculate_rsi(close)
    frame["ATR14"] = atr14
    frame["ATRPercent"] = atr14 / zero_safe_close
    frame["VolumeAverage20"] = volume_average_20
    frame["VolumeRatio"] = volume / volume_average_20.replace(0, np.nan)

    frame["Return5D"] = close.pct_change(periods=5)
    frame["Return20D"] = close.pct_change(periods=20)
    frame["Volatility20"] = daily_returns.rolling(window=20, min_periods=20).std() * np.sqrt(TRADING_DAYS_IN_YEAR)

    frame["RecentHigh20"] = recent_high_20
    frame["DistanceFromRecentHigh20"] = (close / recent_high_20.replace(0, np.nan)) - 1.0
    frame["BreakoutAboveRecentHigh"] = (close > recent_high_20) & recent_high_20.notna()
    frame["BreakoutAttempt"] = (
        frame["DistanceFromRecentHigh20"].between(-0.02, 0.03, inclusive="both")
        & recent_high_20.notna()
    )

    frame["High52Week"] = high_52_week
    frame["PositionVs52WeekHigh"] = close / high_52_week.replace(0, np.nan)

    frame["MA60TrendUp"] = frame["MA60"] > frame["MA60Prior"]
    frame["MAAlignmentBullish"] = (
        frame["MA20"].notna()
        & frame["MA60"].notna()
        & frame["MA120"].notna()
        & (frame["MA20"] > frame["MA60"])
        & (frame["MA60"] > frame["MA120"])
    )
    frame["TrendStrength20"] = (frame["MA20"] / frame["MA20"].shift(20)) - 1.0
    frame["RecentSpike"] = frame["Return5D"] > 0.18

    _INDICATOR_CACHE.set(cache_key, frame.copy(), INDICATOR_CACHE_TTL_SECONDS)
    return frame
