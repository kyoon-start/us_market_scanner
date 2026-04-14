import unittest

import numpy as np
import pandas as pd

from app.indicators import add_indicators
from app.scorer import build_recommendation, has_required_history


class ScoringEvidenceTests(unittest.TestCase):
    def _build_strong_frame(self) -> pd.DataFrame:
        index = pd.date_range("2024-01-01", periods=280, freq="B")
        base = np.linspace(100.0, 165.0, len(index))
        close = base.copy()
        close[-20:] = np.linspace(close[-21] * 1.01, 182.0, 20)
        high = close * 1.01
        low = close * 0.99
        open_price = close * 0.995
        volume = np.full(len(index), 1_000_000.0)
        volume[-1] = 2_200_000.0
        return pd.DataFrame(
            {
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": volume,
            },
            index=index,
        )

    def _build_neutral_frame(self) -> pd.DataFrame:
        index = pd.date_range("2024-01-01", periods=280, freq="B")
        base = np.linspace(100.0, 112.0, len(index))
        noise = np.sin(np.linspace(0, 18, len(index))) * 1.8
        close = base + noise
        close[-20:] = np.linspace(108.5, 110.5, 20)
        high = close * 1.01
        low = close * 0.985
        open_price = close * 0.997
        volume = np.full(len(index), 1_000_000.0)
        volume[-1] = 780_000.0
        return pd.DataFrame(
            {
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": volume,
            },
            index=index,
        )

    def test_indicators_include_stronger_evidence_fields(self) -> None:
        enriched = add_indicators(self._build_strong_frame())
        latest = enriched.iloc[-1]

        self.assertTrue(
            has_required_history(
                latest,
                (
                    "MA20",
                    "MA60",
                    "MA120",
                    "VolumeAverage20",
                    "RSI",
                    "ATR14",
                    "RecentHigh20",
                    "PositionVs52WeekHigh",
                ),
            )
        )
        self.assertIn("Return5D", enriched.columns)
        self.assertIn("Return20D", enriched.columns)
        self.assertIn("Volatility20", enriched.columns)
        self.assertIn("BreakoutAboveRecentHigh", enriched.columns)

    def test_recommendation_reasons_reflect_refined_logic(self) -> None:
        enriched = add_indicators(self._build_strong_frame())
        recommendation = build_recommendation("TEST", enriched, enriched.iloc[-1])

        swing_reasons = " ".join(recommendation["swing"]["reason"])
        long_reasons = " ".join(recommendation["long"]["reason"])

        self.assertIn("20-day high", swing_reasons)
        self.assertIn("5 days", swing_reasons)
        self.assertIn("52-week high", swing_reasons)
        self.assertIn("ATR", swing_reasons)
        self.assertIn("20-day", long_reasons)
        self.assertIn("52-week high", long_reasons)
        self.assertIn("Moving averages", long_reasons)

    def test_neutral_setup_scores_lower_than_strong_setup(self) -> None:
        strong = add_indicators(self._build_strong_frame())
        neutral = add_indicators(self._build_neutral_frame())

        strong_recommendation = build_recommendation("STRONG", strong, strong.iloc[-1])
        neutral_recommendation = build_recommendation("NEUTRAL", neutral, neutral.iloc[-1])

        self.assertGreater(strong_recommendation["swing"]["score"], neutral_recommendation["swing"]["score"])
        self.assertGreater(strong_recommendation["long"]["score"], neutral_recommendation["long"]["score"])

    def test_long_term_scoring_is_more_conservative(self) -> None:
        enriched = add_indicators(self._build_strong_frame())
        recommendation = build_recommendation("TEST", enriched, enriched.iloc[-1])

        self.assertLessEqual(recommendation["long"]["score"], recommendation["swing"]["score"])


if __name__ == "__main__":
    unittest.main()
