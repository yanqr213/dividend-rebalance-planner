from __future__ import annotations

import math
from dataclasses import asdict

from .models import DividendSchedule, Holding, TargetWeight, TradeRecommendation


def _round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def _round_units(value: float) -> float:
    return round(value + 1e-9, 6)


def normalize_targets(targets: list[TargetWeight]) -> dict[str, float]:
    if not targets:
        raise ValueError("At least one target weight is required.")
    total = sum(item.target_weight for item in targets)
    if total <= 0:
        raise ValueError("Target weights must sum to a positive number.")
    normalized: dict[str, float] = {}
    for item in targets:
        normalized[item.ticker] = normalized.get(item.ticker, 0.0) + (item.target_weight / total)
    return normalized


def _estimate_trade_fee(notional: float, fee_rate: float, fee_fixed: float) -> float:
    if notional <= 0:
        return 0.0
    return fee_fixed + (notional * fee_rate)


def _affordable_lots(cash_available: float, price: float, lot_size: float, fee_rate: float, fee_fixed: float) -> int:
    if cash_available <= fee_fixed:
        return 0
    full_lot_cost = (lot_size * price * (1 + fee_rate))
    if full_lot_cost <= 0:
        return 0
    return max(0, int((cash_available - fee_fixed) // full_lot_cost))


def _build_monthly_dividend_forecast(
    final_shares: dict[str, float],
    dividends: dict[str, DividendSchedule],
) -> list[dict[str, float | int | str]]:
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result: list[dict[str, float | int | str]] = []
    for month_index, month_name in enumerate(month_names, start=1):
        gross = 0.0
        net = 0.0
        for ticker, shares in final_shares.items():
            schedule = dividends.get(ticker)
            if schedule is None or month_index not in schedule.payout_months or not schedule.payout_months:
                continue
            per_payment = schedule.annual_dividend_per_share / len(schedule.payout_months)
            gross_amount = shares * per_payment
            gross += gross_amount
            net += gross_amount * (1 - schedule.withholding_tax_rate)
        result.append(
            {
                "month": month_index,
                "month_name": month_name,
                "gross_dividend": _round_money(gross),
                "net_dividend": _round_money(net),
            }
        )
    return result


def create_plan(
    holdings: list[Holding],
    targets: list[TargetWeight],
    dividends: list[DividendSchedule],
    cash: float,
    monthly_contribution: float = 0.0,
    fee_rate: float = 0.0,
    fee_fixed: float = 0.0,
    allow_sells: bool = True,
) -> dict[str, object]:
    if cash < 0:
        raise ValueError("Cash cannot be negative.")
    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative.")
    if fee_rate < 0 or fee_fixed < 0:
        raise ValueError("Fees cannot be negative.")

    target_weights = normalize_targets(targets)
    holdings_map = {item.ticker: item for item in holdings}
    tradable_tickers = set(holdings_map)
    missing_prices = [ticker for ticker in target_weights if ticker not in tradable_tickers]
    if missing_prices:
        missing_joined = ", ".join(sorted(missing_prices))
        raise ValueError(
            "All target tickers must exist in holdings CSV with a local price. Missing: "
            f"{missing_joined}"
        )

    dividend_map = {item.ticker: item for item in dividends}
    current_shares = {ticker: holding.shares for ticker, holding in holdings_map.items()}
    prices = {ticker: holding.price for ticker, holding in holdings_map.items()}
    lot_sizes = {ticker: holding.min_trade_unit for ticker, holding in holdings_map.items()}

    total_current_value = sum(holding.value for holding in holdings)
    investable_cash = cash + monthly_contribution
    desired_total_value = total_current_value + investable_cash
    desired_values = {ticker: desired_total_value * target_weights.get(ticker, 0.0) for ticker in holdings_map}

    trades: list[TradeRecommendation] = []
    sell_proceeds = 0.0
    buy_cost = 0.0
    fee_total = 0.0

    if allow_sells:
        sell_candidates: list[tuple[str, float]] = []
        for ticker, holding in holdings_map.items():
            target_value = desired_values.get(ticker, 0.0)
            gap_value = holding.value - target_value
            if gap_value <= 0:
                continue
            sell_candidates.append((ticker, gap_value / max(target_value, 1.0)))
        for ticker, _score in sorted(sell_candidates, key=lambda item: item[1], reverse=True):
            price = prices[ticker]
            lot_size = lot_sizes[ticker]
            target_value = desired_values.get(ticker, 0.0)
            current_value = current_shares[ticker] * price
            excess_value = current_value - target_value
            shares_to_sell = math.floor((excess_value / price) / lot_size) * lot_size
            shares_to_sell = min(shares_to_sell, current_shares[ticker])
            shares_to_sell = _round_units(max(0.0, shares_to_sell))
            if shares_to_sell <= 0:
                continue
            notional = shares_to_sell * price
            fee = _estimate_trade_fee(notional, fee_rate, fee_fixed)
            current_shares[ticker] = _round_units(current_shares[ticker] - shares_to_sell)
            sell_proceeds += notional
            fee_total += fee
            trades.append(
                TradeRecommendation(
                    ticker=ticker,
                    action="SELL",
                    shares=shares_to_sell,
                    price=price,
                    notional=_round_money(notional),
                    fee=_round_money(fee),
                    reason="Reduce overweight position toward target allocation.",
                )
            )

    cash_available = investable_cash + sell_proceeds - fee_total

    buy_candidates: list[tuple[str, float]] = []
    for ticker, price in prices.items():
        target_value = desired_values.get(ticker, 0.0)
        current_value = current_shares[ticker] * price
        gap_value = target_value - current_value
        if gap_value <= 0:
            continue
        gap_ratio = gap_value / max(target_value, 1.0)
        buy_candidates.append((ticker, gap_ratio))

    for ticker, _score in sorted(buy_candidates, key=lambda item: item[1], reverse=True):
        price = prices[ticker]
        lot_size = lot_sizes[ticker]
        target_value = desired_values.get(ticker, 0.0)
        current_value = current_shares[ticker] * price
        gap_value = target_value - current_value
        needed_lots = int((gap_value // (price * lot_size)))
        affordable_lots = _affordable_lots(cash_available, price, lot_size, fee_rate, fee_fixed)
        lots_to_buy = min(needed_lots, affordable_lots)
        if lots_to_buy <= 0:
            continue
        shares_to_buy = _round_units(lots_to_buy * lot_size)
        notional = shares_to_buy * price
        fee = _estimate_trade_fee(notional, fee_rate, fee_fixed)
        current_shares[ticker] = _round_units(current_shares[ticker] + shares_to_buy)
        cash_available -= notional + fee
        buy_cost += notional
        fee_total += fee
        trades.append(
            TradeRecommendation(
                ticker=ticker,
                action="BUY",
                shares=shares_to_buy,
                price=price,
                notional=_round_money(notional),
                fee=_round_money(fee),
                reason="Add to underweight position within cash and lot constraints.",
            )
        )

    final_values = {ticker: current_shares[ticker] * price for ticker, price in prices.items()}
    remaining_positive_deficits = {}
    lot_constraint_value = 0.0
    cash_needed_to_finish = 0.0
    for ticker, final_value in final_values.items():
        target_value = desired_values.get(ticker, 0.0)
        deficit = max(0.0, target_value - final_value)
        if deficit <= 0:
            continue
        remaining_positive_deficits[ticker] = deficit
        lot_value = prices[ticker] * lot_sizes[ticker]
        if deficit < lot_value:
            lot_constraint_value += deficit
            continue
        lots_needed = math.ceil(deficit / lot_value)
        notional_needed = lots_needed * lot_value
        cash_needed_to_finish += notional_needed + _estimate_trade_fee(notional_needed, fee_rate, fee_fixed)

    cash_shortfall = max(0.0, cash_needed_to_finish - max(0.0, cash_available))
    monthly_dividends = _build_monthly_dividend_forecast(current_shares, dividend_map)
    annual_gross_dividend = _round_money(sum(item["gross_dividend"] for item in monthly_dividends))
    annual_net_dividend = _round_money(sum(item["net_dividend"] for item in monthly_dividends))

    current_weight_denominator = total_current_value or 1.0
    projected_total_value = sum(final_values.values())
    projected_weight_denominator = projected_total_value or 1.0
    positions: list[dict[str, object]] = []
    for ticker in sorted(holdings_map):
        holding = holdings_map[ticker]
        current_value = holding.value
        final_value = final_values[ticker]
        current_weight = current_value / current_weight_denominator if total_current_value else 0.0
        projected_weight = final_value / projected_weight_denominator if desired_total_value else 0.0
        target_weight = target_weights.get(ticker, 0.0)
        positions.append(
            {
                "ticker": ticker,
                "current_shares": _round_units(holding.shares),
                "post_trade_shares": _round_units(current_shares[ticker]),
                "price": _round_money(holding.price),
                "current_value": _round_money(current_value),
                "post_trade_value": _round_money(final_value),
                "current_weight": round(current_weight, 6),
                "target_weight": round(target_weight, 6),
                "projected_weight": round(projected_weight, 6),
                "weight_deviation_before": round(current_weight - target_weight, 6),
                "weight_deviation_after": round(projected_weight - target_weight, 6),
                "estimated_annual_dividend_gross": _round_money(
                    current_shares[ticker] * dividend_map.get(ticker, DividendSchedule(ticker, 0.0, tuple(), 0.0)).annual_dividend_per_share
                ),
                "estimated_annual_dividend_net": _round_money(
                    current_shares[ticker]
                    * dividend_map.get(ticker, DividendSchedule(ticker, 0.0, tuple(), 0.0)).annual_dividend_per_share
                    * (1 - dividend_map.get(ticker, DividendSchedule(ticker, 0.0, tuple(), 0.0)).withholding_tax_rate)
                ),
            }
        )

    summary = {
        "portfolio_value_before": _round_money(total_current_value),
        "cash_input": _round_money(cash),
        "monthly_contribution_input": _round_money(monthly_contribution),
        "investable_cash_total": _round_money(investable_cash),
        "sell_proceeds": _round_money(sell_proceeds),
        "buy_cost": _round_money(buy_cost),
        "fees_total": _round_money(fee_total),
        "cash_remaining": _round_money(max(0.0, cash_available)),
        "cash_shortfall": _round_money(cash_shortfall),
        "lot_constraint_value": _round_money(lot_constraint_value),
        "desired_total_value": _round_money(desired_total_value),
        "projected_total_value": _round_money(projected_total_value),
        "annual_dividend_gross": annual_gross_dividend,
        "annual_dividend_net": annual_net_dividend,
        "trade_count": len(trades),
        "allow_sells": allow_sells,
    }

    return {
        "summary": summary,
        "positions": positions,
        "trades": [asdict(trade) for trade in trades],
        "monthly_dividends": monthly_dividends,
        "assumptions": {
            "price_source": "Local holdings CSV prices supplied by user.",
            "target_weights_normalized": True,
            "dividend_model": "Annual dividend per share spread equally across listed payout months.",
            "fees_model": {
                "fee_rate": fee_rate,
                "fee_fixed": fee_fixed,
            },
        },
    }
