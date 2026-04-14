"""Scoring rules for swing and long-term stock setups."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


PATTERN_LOOKBACK_DAYS = 20
PATTERN_FORWARD_DAYS = 5
PATTERN_TOP_MATCHES = 10
PATTERN_MIN_MATCHES = 3

SWING_PATTERN_WEIGHT = 0.8
LONG_PATTERN_WEIGHT = 0.35


def _has_value(value: object) -> bool:
    """Return True when a scalar-like value is present."""
    return not pd.isna(value)


def _format_number(value: object) -> str:
    """Format numeric values consistently for explanations."""
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.2f}"


def _format_percent(value: object) -> str:
    """Format decimal values as percentages for explanations."""
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.1%}"


def _format_probability(value: float | None) -> str:
    """Format a probability for human-readable explanations."""
    if value is None:
        return "n/a"
    return f"{value:.0%}"


def _apply_score(score: int, reasons: list[str], condition: bool, points: int, message: str) -> int:
    """Apply a score delta and append the paired explanation when triggered."""
    if condition:
        score += points
        reasons.append(f"{message} ({points:+d})")
    return score


def _normalize_pattern(close_window: pd.Series) -> np.ndarray | None:
    """Normalize a price window into a comparable return pattern vector."""
    returns = close_window.pct_change().dropna().to_numpy(dtype=float)
    if returns.size == 0:
        return None

    volatility = np.linalg.norm(returns)
    if volatility == 0:
        return returns

    return returns / volatility


def calculate_pattern_signal(dataframe: pd.DataFrame) -> dict[str, float | int | None]:
    """Compare the last 20 trading days to historical windows and score the win rate."""
    close_series = dataframe.get("Close")
    if close_series is None:
        return {"score": 0, "probability": None, "matches": 0}

    minimum_length = PATTERN_LOOKBACK_DAYS + PATTERN_FORWARD_DAYS + PATTERN_MIN_MATCHES
    if len(close_series) < minimum_length:
        return {"score": 0, "probability": None, "matches": 0}

    current_window = close_series.iloc[-PATTERN_LOOKBACK_DAYS:]
    current_pattern = _normalize_pattern(current_window)
    if current_pattern is None:
        return {"score": 0, "probability": None, "matches": 0}

    candidates: list[tuple[float, float]] = []
    final_start = len(close_series) - PATTERN_LOOKBACK_DAYS - PATTERN_FORWARD_DAYS

    for start_index in range(final_start):
        historical_window = close_series.iloc[start_index : start_index + PATTERN_LOOKBACK_DAYS]
        forward_window = close_series.iloc[
            start_index + PATTERN_LOOKBACK_DAYS : start_index + PATTERN_LOOKBACK_DAYS + PATTERN_FORWARD_DAYS
        ]

        if len(historical_window) < PATTERN_LOOKBACK_DAYS or len(forward_window) < PATTERN_FORWARD_DAYS:
            continue

        historical_pattern = _normalize_pattern(historical_window)
        if historical_pattern is None or historical_pattern.shape != current_pattern.shape:
            continue

        similarity = float(np.dot(current_pattern, historical_pattern))
        if not np.isfinite(similarity):
            continue

        base_close = historical_window.iloc[-1]
        future_close = forward_window.iloc[-1]
        if pd.isna(base_close) or pd.isna(future_close) or base_close == 0:
            continue

        forward_return = float((future_close / base_close) - 1.0)
        candidates.append((similarity, forward_return))

    if len(candidates) < PATTERN_MIN_MATCHES:
        return {"score": 0, "probability": None, "matches": len(candidates)}

    top_matches = sorted(candidates, key=lambda item: item[0], reverse=True)[:PATTERN_TOP_MATCHES]
    forward_returns = [forward_return for _, forward_return in top_matches]
    probability = sum(return_value > 0 for return_value in forward_returns) / len(forward_returns)

    pattern_score = int(round((probability - 0.5) * 40))
    pattern_score = max(-20, min(20, pattern_score))

    return {
        "score": pattern_score,
        "probability": probability,
        "matches": len(top_matches),
    }


def _append_pattern_reason(
    score: int,
    reasons: list[str],
    pattern_signal: dict[str, float | int | None],
    *,
    context_label: str,
    weight: float,
) -> tuple[int, float | None]:
    """Apply weighted pattern evidence with consistent explanation text."""
    raw_pattern_score = int(pattern_signal["score"])
    pattern_probability = pattern_signal["probability"]
    pattern_matches = int(pattern_signal["matches"])
    weighted_pattern_score = int(round(raw_pattern_score * weight))

    if pattern_probability is not None and weighted_pattern_score != 0:
        score += weighted_pattern_score
        direction = "supports" if weighted_pattern_score > 0 else "tempers"
        reasons.append(
            f"Historical 20-day pattern {direction} the {context_label}: "
            f"{_format_probability(pattern_probability)} win rate over {pattern_matches} similar windows "
            f"for the next 5 trading days ({weighted_pattern_score:+d})"
        )
    elif pattern_probability is not None:
        reasons.append(
            f"Historical 20-day pattern is neutral: {_format_probability(pattern_probability)} "
            f"win rate over {pattern_matches} similar windows (0)"
        )
    else:
        reasons.append("Historical pattern score unavailable because there were not enough valid prior windows")

    return score, pattern_probability


def score_swing_setup(
    latest_row: pd.Series,
    pattern_signal: dict[str, float | int | None],
) -> tuple[int, float | None, list[str]]:
    """Score a stock for swing trading conditions."""
    score = 0
    reasons: list[str] = []

    close_price = latest_row.get("Close")
    ma20 = latest_row.get("MA20")
    ma60 = latest_row.get("MA60")
    ma120 = latest_row.get("MA120")
    rsi = latest_row.get("RSI")
    volume = latest_row.get("Volume")
    volume_average = latest_row.get("VolumeAverage20")
    volume_ratio = latest_row.get("VolumeRatio")
    return_5d = latest_row.get("Return5D")
    return_20d = latest_row.get("Return20D")
    atr_percent = latest_row.get("ATRPercent")
    volatility_20 = latest_row.get("Volatility20")
    recent_high_20 = latest_row.get("RecentHigh20")
    distance_recent_high = latest_row.get("DistanceFromRecentHigh20")
    breakout_above_recent_high = bool(latest_row.get("BreakoutAboveRecentHigh", False))
    breakout_attempt = bool(latest_row.get("BreakoutAttempt", False))
    recent_spike = bool(latest_row.get("RecentSpike", False))
    position_vs_52week_high = latest_row.get("PositionVs52WeekHigh")

    price_above_ma20 = _has_value(ma20) and _has_value(close_price) and close_price > ma20
    medium_term_support = _has_value(ma60) and _has_value(close_price) and close_price > ma60
    trend_stack = (
        _has_value(ma20)
        and _has_value(ma60)
        and _has_value(ma120)
        and close_price > ma20 > ma60 > ma120
    )
    breakout_clean = breakout_above_recent_high and _has_value(distance_recent_high) and distance_recent_high <= 0.02
    breakout_tight = (not breakout_above_recent_high) and breakout_attempt and _has_value(distance_recent_high)
    strong_volume = _has_value(volume_ratio) and volume_ratio >= 1.8
    weak_volume = _has_value(volume_ratio) and volume_ratio < 0.9
    healthy_short_return = _has_value(return_5d) and 0.02 <= return_5d <= 0.12
    healthy_month_return = _has_value(return_20d) and return_20d >= 0.07
    flat_month_return = _has_value(return_20d) and return_20d < 0.03
    near_52week_high = _has_value(position_vs_52week_high) and position_vs_52week_high >= 0.93
    far_from_52week_high = _has_value(position_vs_52week_high) and position_vs_52week_high < 0.78
    controlled_atr = _has_value(atr_percent) and atr_percent <= 0.05
    noisy_atr = _has_value(atr_percent) and atr_percent > 0.075
    rsi_constructive = _has_value(rsi) and 48 <= rsi <= 66
    overbought = _has_value(rsi) and rsi > 72
    elevated_volatility = _has_value(volatility_20) and volatility_20 > 0.45

    score = _apply_score(score, reasons, price_above_ma20, 8, f"Price closed at {_format_number(close_price)}, above MA20 {_format_number(ma20)}")
    score = _apply_score(score, reasons, medium_term_support, 8, f"Price is also holding above MA60 {_format_number(ma60)}, supporting the medium-term trend")
    score = _apply_score(score, reasons, trend_stack, 14, f"Moving averages are cleanly aligned with price > MA20 {_format_number(ma20)} > MA60 {_format_number(ma60)} > MA120 {_format_number(ma120)}")
    score = _apply_score(score, reasons, breakout_clean, 14, f"Price cleared the recent 20-day high of {_format_number(recent_high_20)} and remains {_format_percent(distance_recent_high)} above that level")
    score = _apply_score(score, reasons, breakout_tight, 8, f"Price is tightly coiled within {_format_percent(distance_recent_high)} of the recent 20-day high {_format_number(recent_high_20)}")
    score = _apply_score(score, reasons, strong_volume, 14, f"Volume expanded to {_format_number(volume)} versus the 20-day average {_format_number(volume_average)} ({_format_number(volume_ratio)}x), showing strong participation")
    score = _apply_score(score, reasons, healthy_short_return, 7, f"The stock is up {_format_percent(return_5d)} over 5 days, showing usable swing momentum")
    score = _apply_score(score, reasons, healthy_month_return, 9, f"The 20-day return is {_format_percent(return_20d)}, confirming upside trend follow-through")
    score = _apply_score(score, reasons, near_52week_high, 8, f"Price is holding at {_format_percent(position_vs_52week_high)} of its 52-week high, reflecting leadership")
    score = _apply_score(score, reasons, controlled_atr, 4, f"ATR is {_format_percent(atr_percent)} of price, keeping swing volatility controlled")
    score = _apply_score(score, reasons, rsi_constructive, 5, f"RSI is {_format_number(rsi)}, which supports upside momentum without looking overheated")

    score = _apply_score(score, reasons, weak_volume, -10, f"Volume is only {_format_number(volume_ratio)}x the 20-day average, which weakens conviction")
    score = _apply_score(score, reasons, overbought, -12, f"RSI reached {_format_number(rsi)}, which looks overextended for a fresh swing entry")
    score = _apply_score(score, reasons, recent_spike, -12, f"The 5-day return already reached {_format_percent(return_5d)}, increasing chase risk after a sharp run")
    score = _apply_score(score, reasons, flat_month_return, -8, f"The 20-day return is only {_format_percent(return_20d)}, leaving the setup too neutral to stand out")
    score = _apply_score(score, reasons, noisy_atr, -8, f"ATR is {_format_percent(atr_percent)} of price, making the setup noisier than preferred")
    score = _apply_score(score, reasons, elevated_volatility, -8, f"20-day realized volatility is {_format_percent(volatility_20)}, which reduces swing quality")
    score = _apply_score(score, reasons, far_from_52week_high, -8, f"Price is only at {_format_percent(position_vs_52week_high)} of its 52-week high, which weakens leadership quality")

    score, pattern_probability = _append_pattern_reason(score, reasons, pattern_signal, context_label="setup", weight=SWING_PATTERN_WEIGHT)

    if not reasons:
        reasons.append("The latest bar did not meet any configured swing evidence strongly enough to earn a score")

    return score, pattern_probability, reasons


def score_long_term_setup(
    latest_row: pd.Series,
    pattern_signal: dict[str, float | int | None],
) -> tuple[int, float | None, list[str]]:
    """Score a stock for longer-term trend conditions."""
    score = 0
    reasons: list[str] = []

    close_price = latest_row.get("Close")
    ma20 = latest_row.get("MA20")
    ma60 = latest_row.get("MA60")
    ma120 = latest_row.get("MA120")
    ma60_prior = latest_row.get("MA60Prior")
    rsi = latest_row.get("RSI")
    return_20d = latest_row.get("Return20D")
    volume_ratio = latest_row.get("VolumeRatio")
    atr_percent = latest_row.get("ATRPercent")
    position_vs_52week_high = latest_row.get("PositionVs52WeekHigh")
    trend_strength_20 = latest_row.get("TrendStrength20")
    ma60_trending_up = bool(latest_row.get("MA60TrendUp", False))

    price_above_ma60 = _has_value(ma60) and _has_value(close_price) and close_price > ma60
    price_above_ma120 = _has_value(ma120) and _has_value(close_price) and close_price > ma120
    clean_trend_stack = (
        _has_value(ma20)
        and _has_value(ma60)
        and _has_value(ma120)
        and close_price > ma20 > ma60 > ma120
    )
    strong_trend_slope = _has_value(trend_strength_20) and trend_strength_20 >= 0.03
    weak_trend_slope = _has_value(trend_strength_20) and trend_strength_20 < 0.015
    sustained_return = _has_value(return_20d) and return_20d >= 0.12
    weak_long_return = _has_value(return_20d) and return_20d < 0.04
    strong_volume = _has_value(volume_ratio) and volume_ratio >= 1.4
    weak_volume = _has_value(volume_ratio) and volume_ratio < 0.95
    near_52week_high = _has_value(position_vs_52week_high) and position_vs_52week_high >= 0.93
    far_from_52week_high = _has_value(position_vs_52week_high) and position_vs_52week_high < 0.8
    contained_volatility = _has_value(atr_percent) and atr_percent <= 0.06
    noisy_volatility = _has_value(atr_percent) and atr_percent > 0.08
    overextended_rsi = _has_value(rsi) and rsi > 70
    overextended_run = _has_value(return_20d) and return_20d > 0.13
    misaligned_mas = _has_value(ma20) and _has_value(ma60) and _has_value(ma120) and not (ma20 > ma60 > ma120)

    score = _apply_score(score, reasons, price_above_ma60, 6, f"Price closed at {_format_number(close_price)}, holding above MA60 {_format_number(ma60)}")
    score = _apply_score(score, reasons, price_above_ma120, 8, f"Price remains above MA120 {_format_number(ma120)}, preserving the primary uptrend")
    score = _apply_score(score, reasons, ma60_trending_up, 6, f"MA60 improved from {_format_number(ma60_prior)} to {_format_number(ma60)} over the last week")
    score = _apply_score(score, reasons, clean_trend_stack, 14, f"Moving averages are cleanly stacked with price > MA20 {_format_number(ma20)} > MA60 {_format_number(ma60)} > MA120 {_format_number(ma120)}")
    score = _apply_score(score, reasons, strong_trend_slope, 8, f"MA20 has improved by {_format_percent(trend_strength_20)} over the last month, indicating a durable trend slope")
    score = _apply_score(score, reasons, sustained_return, 8, f"The stock gained {_format_percent(return_20d)} over 20 days, confirming persistent demand")
    score = _apply_score(score, reasons, near_52week_high, 8, f"Price is at {_format_percent(position_vs_52week_high)} of its 52-week high, showing it remains near leadership levels")
    score = _apply_score(score, reasons, strong_volume, 5, f"Volume is running at {_format_number(volume_ratio)}x the 20-day average, supporting the longer-term move")
    score = _apply_score(score, reasons, contained_volatility, 4, f"ATR is {_format_percent(atr_percent)} of price, indicating the trend is relatively orderly")

    score = _apply_score(score, reasons, weak_volume, -12, f"Volume is only {_format_number(volume_ratio)}x the 20-day average, which is too weak for a higher-conviction trend setup")
    score = _apply_score(score, reasons, weak_long_return, -12, f"The 20-day return is only {_format_percent(return_20d)}, leaving the long-term trend case too neutral")
    score = _apply_score(score, reasons, weak_trend_slope, -10, f"MA20 has improved by just {_format_percent(trend_strength_20)}, which is too flat for a strong long-term trend")
    score = _apply_score(score, reasons, misaligned_mas, -12, f"Moving-average alignment is not clean enough because MA20 {_format_number(ma20)}, MA60 {_format_number(ma60)}, and MA120 {_format_number(ma120)} are not stacked cleanly")
    score = _apply_score(score, reasons, noisy_volatility, -10, f"ATR is {_format_percent(atr_percent)} of price, which makes the longer-term setup too noisy")
    score = _apply_score(score, reasons, far_from_52week_high, -10, f"Price is only at {_format_percent(position_vs_52week_high)} of its 52-week high, limiting leadership quality")
    score = _apply_score(score, reasons, overextended_rsi, -10, f"RSI reached {_format_number(rsi)}, which is too extended for a conservative long-term entry")
    score = _apply_score(score, reasons, overextended_run, -10, f"The 20-day return is already {_format_percent(return_20d)}, which raises mean-reversion risk for a conservative long-term setup")

    score, pattern_probability = _append_pattern_reason(score, reasons, pattern_signal, context_label="trend", weight=LONG_PATTERN_WEIGHT)

    if not reasons:
        reasons.append("The latest bar did not meet any configured long-term evidence strongly enough to earn a score")

    return score, pattern_probability, reasons


def build_recommendation(symbol: str, dataframe: pd.DataFrame, latest_row: pd.Series) -> dict[str, object]:
    """Create both recommendation payloads for a symbol."""
    pattern_signal = calculate_pattern_signal(dataframe)
    swing_score, swing_probability, swing_reasons = score_swing_setup(latest_row, pattern_signal)
    long_score, long_probability, long_reasons = score_long_term_setup(latest_row, pattern_signal)

    return {
        "symbol": symbol,
        "swing": {
            "symbol": symbol,
            "score": swing_score,
            "probability": swing_probability,
            "reason": swing_reasons,
        },
        "long": {
            "symbol": symbol,
            "score": long_score,
            "probability": long_probability,
            "reason": long_reasons,
        },
    }


def has_required_history(latest_row: pd.Series, required_fields: Iterable[str]) -> bool:
    """Check whether the enriched row has the required indicator values."""
    return all(_has_value(latest_row.get(field)) for field in required_fields)
