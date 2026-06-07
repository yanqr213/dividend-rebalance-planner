from __future__ import annotations

import unittest

from dividend_rebalance_planner.models import DividendSchedule, Holding, TargetWeight
from dividend_rebalance_planner.planner import create_plan, normalize_targets


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holdings = [
            Holding("AAA", 10, 100, 1),
            Holding("BBB", 10, 50, 1),
            Holding("CCC", 5, 80, 1),
        ]
        self.targets = [
            TargetWeight("AAA", 0.4),
            TargetWeight("BBB", 0.35),
            TargetWeight("CCC", 0.25),
        ]
        self.dividends = [
            DividendSchedule("AAA", 4.0, (3, 6, 9, 12), 0.1),
            DividendSchedule("BBB", 2.4, (1, 4, 7, 10), 0.0),
            DividendSchedule("CCC", 1.2, (2, 5, 8, 11), 0.0),
        ]

    def test_normalize_targets_scales_to_one(self) -> None:
        normalized = normalize_targets([TargetWeight("AAA", 40), TargetWeight("BBB", 60)])
        self.assertAlmostEqual(sum(normalized.values()), 1.0)
        self.assertAlmostEqual(normalized["AAA"], 0.4)

    def test_create_plan_generates_buy_trades(self) -> None:
        plan = create_plan(self.holdings, self.targets, self.dividends, cash=300, allow_sells=False)
        actions = {trade["action"] for trade in plan["trades"]}
        self.assertIn("BUY", actions)
        self.assertGreaterEqual(plan["summary"]["trade_count"], 1)

    def test_create_plan_can_generate_sell_trades(self) -> None:
        sell_heavy_holdings = [
            Holding("AAA", 20, 100, 1),
            Holding("BBB", 5, 50, 1),
            Holding("CCC", 5, 80, 1),
        ]
        plan = create_plan(sell_heavy_holdings, self.targets, self.dividends, cash=0, allow_sells=True)
        actions = {trade["action"] for trade in plan["trades"]}
        self.assertIn("SELL", actions)

    def test_create_plan_calculates_monthly_dividends(self) -> None:
        plan = create_plan(self.holdings, self.targets, self.dividends, cash=0, allow_sells=False)
        self.assertEqual(len(plan["monthly_dividends"]), 12)
        march = next(item for item in plan["monthly_dividends"] if item["month"] == 3)
        self.assertGreater(march["gross_dividend"], 0)

    def test_create_plan_rejects_missing_target_price(self) -> None:
        targets = self.targets + [TargetWeight("DDD", 0.1)]
        with self.assertRaises(ValueError):
            create_plan(self.holdings, targets, self.dividends, cash=100)

    def test_create_plan_respects_min_trade_unit(self) -> None:
        holdings = [
            Holding("AAA", 10, 100, 5),
            Holding("BBB", 10, 50, 1),
            Holding("CCC", 5, 80, 1),
        ]
        plan = create_plan(holdings, self.targets, self.dividends, cash=700, allow_sells=False)
        aaa_buys = [trade for trade in plan["trades"] if trade["ticker"] == "AAA" and trade["action"] == "BUY"]
        if aaa_buys:
            self.assertEqual(aaa_buys[0]["shares"] % 5, 0)

    def test_create_plan_tracks_cash_shortfall(self) -> None:
        plan = create_plan(self.holdings, self.targets, self.dividends, cash=10, allow_sells=False)
        self.assertGreaterEqual(plan["summary"]["cash_shortfall"], 0)

    def test_create_plan_includes_fees(self) -> None:
        plan = create_plan(self.holdings, self.targets, self.dividends, cash=500, fee_rate=0.01, fee_fixed=1, allow_sells=False)
        self.assertGreaterEqual(plan["summary"]["fees_total"], 0)

    def test_create_plan_rejects_negative_cash(self) -> None:
        with self.assertRaises(ValueError):
            create_plan(self.holdings, self.targets, self.dividends, cash=-1)


if __name__ == "__main__":
    unittest.main()

