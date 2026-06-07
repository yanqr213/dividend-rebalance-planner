from __future__ import annotations

import csv
from pathlib import Path

from .models import DividendSchedule, Holding, TargetWeight


class InputValidationError(ValueError):
    """Raised when required CSV fields are missing or invalid."""


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise InputValidationError(f"CSV file is empty: {csv_path}")
        return list(reader)


def _normalize_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker:
        raise InputValidationError("Ticker cannot be blank.")
    return ticker


def _require_columns(rows: list[dict[str, str]], required: set[str], source_name: str) -> None:
    if not rows:
        raise InputValidationError(f"{source_name} does not contain any data rows.")
    missing = required.difference(rows[0].keys())
    if missing:
        columns = ", ".join(sorted(missing))
        raise InputValidationError(f"{source_name} is missing required columns: {columns}")


def load_holdings(path: str | Path) -> list[Holding]:
    rows = _read_rows(path)
    _require_columns(rows, {"ticker", "shares", "price"}, "holdings CSV")
    holdings: list[Holding] = []
    for row in rows:
        shares = float(row["shares"])
        price = float(row["price"])
        min_trade_unit = float(row.get("min_trade_unit", "1") or "1")
        if shares < 0:
            raise InputValidationError("Holding shares cannot be negative.")
        if price <= 0:
            raise InputValidationError("Holding price must be positive.")
        if min_trade_unit <= 0:
            raise InputValidationError("Minimum trade unit must be positive.")
        holdings.append(
            Holding(
                ticker=_normalize_ticker(row["ticker"]),
                shares=shares,
                price=price,
                min_trade_unit=min_trade_unit,
            )
        )
    return holdings


def load_targets(path: str | Path) -> list[TargetWeight]:
    rows = _read_rows(path)
    _require_columns(rows, {"ticker", "target_weight"}, "targets CSV")
    targets: list[TargetWeight] = []
    for row in rows:
        weight = float(row["target_weight"])
        if weight < 0:
            raise InputValidationError("Target weight cannot be negative.")
        targets.append(TargetWeight(ticker=_normalize_ticker(row["ticker"]), target_weight=weight))
    return targets


def parse_payout_months(raw_value: str) -> tuple[int, ...]:
    if not raw_value.strip():
        return tuple()
    separators = raw_value.replace(";", "|").replace(",", "|")
    months = []
    for token in separators.split("|"):
        token = token.strip()
        if not token:
            continue
        month = int(token)
        if month < 1 or month > 12:
            raise InputValidationError(f"Invalid payout month: {month}")
        months.append(month)
    return tuple(sorted(set(months)))


def load_dividends(path: str | Path) -> list[DividendSchedule]:
    rows = _read_rows(path)
    _require_columns(
        rows,
        {"ticker", "annual_dividend_per_share", "payout_months"},
        "dividends CSV",
    )
    schedules: list[DividendSchedule] = []
    for row in rows:
        annual_dividend = float(row["annual_dividend_per_share"])
        withholding_tax_rate = float(row.get("withholding_tax_rate", "0") or "0")
        if annual_dividend < 0:
            raise InputValidationError("Annual dividend per share cannot be negative.")
        if withholding_tax_rate < 0 or withholding_tax_rate >= 1:
            raise InputValidationError("Withholding tax rate must be between 0 and 1.")
        schedules.append(
            DividendSchedule(
                ticker=_normalize_ticker(row["ticker"]),
                annual_dividend_per_share=annual_dividend,
                payout_months=parse_payout_months(row["payout_months"]),
                withholding_tax_rate=withholding_tax_rate,
            )
        )
    return schedules

