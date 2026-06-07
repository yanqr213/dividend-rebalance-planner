from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dividend_rebalance_planner.io_utils import (
    InputValidationError,
    load_dividends,
    load_holdings,
    load_targets,
    parse_payout_months,
)


class IoUtilsTests(unittest.TestCase):
    def test_parse_payout_months_supports_multiple_separators(self) -> None:
        self.assertEqual(parse_payout_months("1, 3;6|12"), (1, 3, 6, 12))

    def test_parse_payout_months_rejects_invalid_month(self) -> None:
        with self.assertRaises(InputValidationError):
            parse_payout_months("0,13")

    def test_load_holdings_requires_positive_price(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "holdings.csv"
            path.write_text("ticker,shares,price\nABC,1,0\n", encoding="utf-8")
            with self.assertRaises(InputValidationError):
                load_holdings(path)

    def test_load_targets_requires_data_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "targets.csv"
            path.write_text("ticker,target_weight\n", encoding="utf-8")
            with self.assertRaises(InputValidationError):
                load_targets(path)

    def test_load_dividends_parses_tax_rate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dividends.csv"
            path.write_text(
                "ticker,annual_dividend_per_share,payout_months,withholding_tax_rate\nABC,1.2,\"3,6,9,12\",0.15\n",
                encoding="utf-8",
            )
            rows = load_dividends(path)
            self.assertEqual(rows[0].withholding_tax_rate, 0.15)


if __name__ == "__main__":
    unittest.main()

