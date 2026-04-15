import unittest

from app.universe_config import (
    FALLBACK_SYMBOLS,
    US_RECOMMENDATION_UNIVERSE,
    SUPPORTED_UNIVERSE_SIZES,
    get_default_symbols,
    get_symbols_for_group,
)


class UniverseConfigTests(unittest.TestCase):
    def test_supported_universe_sizes_include_stage_three_large(self) -> None:
        self.assertEqual(SUPPORTED_UNIVERSE_SIZES, (100, 300, 1000))

    def test_default_universe_respects_requested_size(self) -> None:
        self.assertEqual(len(get_default_symbols(100)), 100)
        self.assertEqual(len(get_default_symbols(300)), 300)
        self.assertEqual(len(get_default_symbols(1000)), 1000)

    def test_group_universe_is_capped_by_requested_size(self) -> None:
        symbols = get_symbols_for_group("big-tech", 100)
        self.assertLessEqual(len(symbols), 100)
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)

    def test_unknown_group_falls_back_to_default_universe(self) -> None:
        self.assertEqual(get_symbols_for_group("unknown-group", 100), get_default_symbols(100))

    def test_large_universe_contains_at_least_one_thousand_symbols(self) -> None:
        self.assertGreaterEqual(len(US_RECOMMENDATION_UNIVERSE), 1000)

    def test_fallback_symbols_preserve_small_universe_size(self) -> None:
        self.assertEqual(len(FALLBACK_SYMBOLS), 100)


if __name__ == "__main__":
    unittest.main()
