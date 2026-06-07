from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Holding:
    ticker: str
    shares: float
    price: float
    min_trade_unit: float = 1.0

    @property
    def value(self) -> float:
        return self.shares * self.price


@dataclass(frozen=True)
class TargetWeight:
    ticker: str
    target_weight: float


@dataclass(frozen=True)
class DividendSchedule:
    ticker: str
    annual_dividend_per_share: float
    payout_months: tuple[int, ...]
    withholding_tax_rate: float = 0.0


@dataclass(frozen=True)
class TradeRecommendation:
    ticker: str
    action: str
    shares: float
    price: float
    notional: float
    fee: float
    reason: str

