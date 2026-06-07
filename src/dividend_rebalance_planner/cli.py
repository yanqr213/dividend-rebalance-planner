from __future__ import annotations

import argparse
from pathlib import Path

from .io_utils import load_dividends, load_holdings, load_targets
from .planner import create_plan
from .reports import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dividend-rebalance-planner",
        description="Create an offline dividend and rebalance plan from local CSV files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Build a rebalance plan.")
    plan_parser.add_argument("--holdings", required=True, help="Path to holdings CSV.")
    plan_parser.add_argument("--targets", required=True, help="Path to target weights CSV.")
    plan_parser.add_argument("--dividends", required=True, help="Path to dividend schedule CSV.")
    plan_parser.add_argument("--cash", type=float, default=0.0, help="Available cash to invest now.")
    plan_parser.add_argument(
        "--monthly-contribution",
        type=float,
        default=0.0,
        help="Recurring monthly contribution to include in this plan.",
    )
    plan_parser.add_argument("--fee-rate", type=float, default=0.0, help="Variable fee rate per trade, e.g. 0.001.")
    plan_parser.add_argument("--fee-fixed", type=float, default=0.0, help="Fixed fee charged per trade.")
    plan_parser.add_argument(
        "--no-sells",
        action="store_true",
        help="Disable sell recommendations and only allocate available cash.",
    )
    plan_parser.add_argument("--output-dir", default="outputs", help="Directory for generated reports.")
    plan_parser.add_argument("--prefix", default="plan", help="Filename prefix for generated reports.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "plan":
        parser.error("Unsupported command.")

    holdings = load_holdings(args.holdings)
    targets = load_targets(args.targets)
    dividends = load_dividends(args.dividends)

    plan = create_plan(
        holdings=holdings,
        targets=targets,
        dividends=dividends,
        cash=args.cash,
        monthly_contribution=args.monthly_contribution,
        fee_rate=args.fee_rate,
        fee_fixed=args.fee_fixed,
        allow_sells=not args.no_sells,
    )
    report_paths = write_reports(plan, Path(args.output_dir), prefix=args.prefix)

    print("Generated reports:")
    for label, path in report_paths.items():
        print(f"- {label}: {path}")
    print(
        "Summary: "
        f"trades={plan['summary']['trade_count']}, "
        f"cash_remaining={plan['summary']['cash_remaining']}, "
        f"net_dividend={plan['summary']['annual_dividend_net']}"
    )
    return 0
