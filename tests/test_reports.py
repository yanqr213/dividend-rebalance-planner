from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dividend_rebalance_planner.models import DividendSchedule, Holding, TargetWeight
from dividend_rebalance_planner.planner import create_plan
from dividend_rebalance_planner.reports import write_reports


class ReportTests(unittest.TestCase):
    def test_write_reports_creates_all_formats(self) -> None:
        plan = create_plan(
            holdings=[Holding("AAA", 10, 100, 1)],
            targets=[TargetWeight("AAA", 1.0)],
            dividends=[DividendSchedule("AAA", 4.0, (3, 6, 9, 12), 0.0)],
            cash=0,
            allow_sells=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_reports(plan, tmpdir, prefix="sample")
            for path in paths.values():
                self.assertTrue(Path(path).exists())
            data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
            self.assertIn("summary", data)

    def test_markdown_report_contains_sections(self) -> None:
        plan = create_plan(
            holdings=[Holding("AAA", 10, 100, 1)],
            targets=[TargetWeight("AAA", 1.0)],
            dividends=[DividendSchedule("AAA", 4.0, (3, 6, 9, 12), 0.0)],
            cash=0,
            allow_sells=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_reports(plan, tmpdir, prefix="sample")
            markdown = Path(paths["markdown"]).read_text(encoding="utf-8")
            self.assertIn("## Summary", markdown)
            self.assertIn("## Trades", markdown)


if __name__ == "__main__":
    unittest.main()

