from __future__ import annotations

import csv
import json
from pathlib import Path


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_reports(plan: dict[str, object], output_dir: str | Path, prefix: str = "plan") -> dict[str, str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    json_path = destination / f"{prefix}.json"
    trades_csv_path = destination / f"{prefix}-trades.csv"
    dividends_csv_path = destination / f"{prefix}-monthly-dividends.csv"
    markdown_path = destination / f"{prefix}.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2)

    trades = plan["trades"]
    with trades_csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["ticker", "action", "shares", "price", "notional", "fee", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow({name: trade[name] for name in fieldnames})

    monthly_dividends = plan["monthly_dividends"]
    with dividends_csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["month", "month_name", "gross_dividend", "net_dividend"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in monthly_dividends:
            writer.writerow(item)

    summary = plan["summary"]
    positions = plan["positions"]
    summary_lines = [
        f"- Portfolio value before: {summary['portfolio_value_before']}",
        f"- Investable cash: {summary['investable_cash_total']}",
        f"- Fees total: {summary['fees_total']}",
        f"- Cash remaining: {summary['cash_remaining']}",
        f"- Cash shortfall: {summary['cash_shortfall']}",
        f"- Annual net dividend: {summary['annual_dividend_net']}",
        f"- Lot constraint value: {summary['lot_constraint_value']}",
    ]

    position_rows = [
        [
            str(item["ticker"]),
            f"{item['current_shares']}",
            f"{item['post_trade_shares']}",
            _format_pct(float(item["current_weight"])),
            _format_pct(float(item["target_weight"])),
            _format_pct(float(item["projected_weight"])),
            _format_pct(float(item["weight_deviation_after"])),
        ]
        for item in positions
    ]
    trade_rows = [
        [
            str(item["ticker"]),
            str(item["action"]),
            str(item["shares"]),
            str(item["notional"]),
            str(item["fee"]),
            str(item["reason"]),
        ]
        for item in trades
    ]
    dividend_rows = [
        [
            str(item["month_name"]),
            str(item["gross_dividend"]),
            str(item["net_dividend"]),
        ]
        for item in monthly_dividends
    ]

    markdown = "\n".join(
        [
            "# Dividend Rebalance Plan",
            "",
            "## Summary",
            *summary_lines,
            "",
            "## Positions",
            _markdown_table(
                ["Ticker", "Current Shares", "Post-trade Shares", "Current Weight", "Target Weight", "Projected Weight", "Deviation After"],
                position_rows,
            ),
            "",
            "## Trades",
            _markdown_table(["Ticker", "Action", "Shares", "Notional", "Fee", "Reason"], trade_rows or [["-", "-", "-", "-", "-", "No trades generated."]]),
            "",
            "## Monthly Dividend Forecast",
            _markdown_table(["Month", "Gross Dividend", "Net Dividend"], dividend_rows),
            "",
            "## Assumptions",
            f"- Price source: {plan['assumptions']['price_source']}",
            f"- Dividend model: {plan['assumptions']['dividend_model']}",
        ]
    )

    with markdown_path.open("w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")

    return {
        "json": str(json_path),
        "trades_csv": str(trades_csv_path),
        "monthly_dividends_csv": str(dividends_csv_path),
        "markdown": str(markdown_path),
    }

