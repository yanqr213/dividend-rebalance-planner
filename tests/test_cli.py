from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_cli_plan_command_generates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "reports"
            command = [
                sys.executable,
                "-m",
                "dividend_rebalance_planner",
                "plan",
                "--holdings",
                str(PROJECT_DIR / "examples" / "holdings.csv"),
                "--targets",
                str(PROJECT_DIR / "examples" / "targets.csv"),
                "--dividends",
                str(PROJECT_DIR / "examples" / "dividends.csv"),
                "--cash",
                "1500",
                "--monthly-contribution",
                "500",
                "--fee-rate",
                "0.001",
                "--fee-fixed",
                "1",
                "--output-dir",
                str(output_dir),
                "--prefix",
                "cli-run",
            ]
            completed = subprocess.run(command, cwd=PROJECT_DIR, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("Generated reports:", completed.stdout)
            self.assertTrue((output_dir / "cli-run.json").exists())
            payload = json.loads((output_dir / "cli-run.json").read_text(encoding="utf-8"))
            self.assertIn("positions", payload)

    def test_cli_help(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "dividend_rebalance_planner", "--help"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("plan", completed.stdout)


if __name__ == "__main__":
    unittest.main()
