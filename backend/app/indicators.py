"""Technical indicator calculations for the stock scanner."""

from __future__ import annotations

import numpy as np
import pandas as pd


TRADING_DAYS_IN_YEAR = 252


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

    frame = dataframe.copy()

    frame["MA20"] = frame["Close"].rolling(window=20, min_periods=20).mean()
    frame["MA60"] = frame["Close"].rolling(window=60, min_periods=60).mean()
    frame["MA120"] = frame["Close"].rolling(window=120, min_periods=120).mean()
    frame["MA60Prior"] = frame["MA60"].shift(5)
    frame["RSI"] = calculate_rsi(frame["Close"])
    frame["ATR14"] = calculate_atr(frame, period=14)
    frame["ATRPercent"] = frame["ATR14"] / frame["Close"].replace(0, np.nan)
    frame["VolumeAverage20"] = frame["Volume"].rolling(window=20, min_periods=20).mean()
    frame["VolumeRatio"] = frame["Volume"] / frame["VolumeAverage20"].replace(0, np.nan)

    frame["Return5D"] = frame["Close"].pct_change(periods=5)
    frame["Return20D"] = frame["Close"].pct_change(periods=20)
    daily_returns = frame["Close"].pct_change()
    frame["Volatility20"] = daily_returns.rolling(window=20, min_periods=20).std() * np.sqrt(TRADING_DAYS_IN_YEAR)

    frame["RecentHigh20"] = frame["High"].rolling(window=20, min_periods=20).max().shift(1)
    frame["DistanceFromRecentHigh20"] = (
        frame["Close"] / frame["RecentHigh20"].replace(0, np.nan)
    ) - 1.0
    frame["BreakoutAboveRecentHigh"] = (
        frame["Close"] > frame["RecentHigh20"]
    ) & frame["RecentHigh20"].notna()
    frame["BreakoutAttempt"] = (
        frame["DistanceFromRecentHigh20"] >= -0.02
    ) & (
        frame["DistanceFromRecentHigh20"] <= 0.03
    ) & frame["RecentHigh20"].notna()

    frame["High52Week"] = frame["High"].rolling(window=TRADING_DAYS_IN_YEAR, min_periods=TRADING_DAYS_IN_YEAR).max()
    frame["PositionVs52WeekHigh"] = frame["Close"] / frame["High52Week"].replace(0, np.nan)

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

    return frame
