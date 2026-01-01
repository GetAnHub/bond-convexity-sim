from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Bond:
    name: str
    par_value: float
    coupon_rate: float
    coupon_frequency: int
    issue_date: date
    maturity_date: date


@dataclass
class AnalysisRequest:
    price: float
    purchase_date: date
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    num_points: int = 100


@dataclass
class AnalysisResult:
    ytm: float
    accrued_interest: float
    modified_duration: float
    curve: Optional[object] = None
