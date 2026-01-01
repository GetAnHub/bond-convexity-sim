from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import math

from .models import AnalysisRequest, AnalysisResult, Bond
from .pricing import bond_price, calculate_ytm


def compute_periods(maturity_date: datetime.date, purchase_date: datetime.date, coupon_frequency: int) -> int:
    delta = maturity_date - purchase_date
    return round(delta.days / 365.25 * coupon_frequency)


def calculate_accrued_interest(par_value: float, coupon_rate: float, issue_date: str, purchase_date: str, coupon_frequency: int = 1):
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        issue = datetime.strptime(issue_date, "%d/%m/%Y")
        purchase = datetime.strptime(purchase_date, "%d/%m/%Y")
        coupon_interval = 365.25 / coupon_frequency
        years_since_issue = (purchase - issue).days / 365.25
        coupons_paid = int(years_since_issue * coupon_frequency)
        last_coupon_date = issue
        for _ in range(coupons_paid):
            increment = timedelta(days=coupon_interval)
            last_coupon_date += increment

        days_since_last_coupon = (purchase - last_coupon_date).days
        if days_since_last_coupon < 0:
            days_since_last_coupon += coupon_interval

        annual_coupon = (coupon_rate / 100) * par_value
        accrued_interest = annual_coupon * (days_since_last_coupon / coupon_interval)
        return accrued_interest
    except Exception:
        return math.nan


def calculate_modified_duration(par_value: float, coupon_rate: float, periods: int, ytm: float, coupon_frequency: int = 1):
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        ytm = float(ytm)
        coupon = (coupon_rate / 100) * par_value / coupon_frequency
        discount_rate = ytm / coupon_frequency
        macaulay_duration = 0
        present_value_total = 0

        for t in range(1, int(periods) + 1):
            cash_flow = coupon if t < periods else coupon + par_value
            pv_cash_flow = cash_flow / (1 + discount_rate) ** t
            macaulay_duration += t * pv_cash_flow
            present_value_total += pv_cash_flow

        if present_value_total == 0:
            return math.nan

        macaulay_duration /= present_value_total
        modified_duration = macaulay_duration / (1 + discount_rate)
        return modified_duration
    except (ValueError, TypeError):
        return math.nan


def generate_cash_flows(par_value: float, coupon_rate: float, periods: int, coupon_frequency: int) -> List[float]:
    coupon = (coupon_rate / 100) * par_value / coupon_frequency
    flows = [coupon] * max(periods - 1, 0)
    flows.append(coupon + par_value)
    return flows


def calculate_ytm_from_bond_data(
    price: float,
    par_value: float,
    coupon_rate: float,
    maturity_date: str,
    purchase_date: str,
    coupon_frequency: int = 1,
    issue_price: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
):
    try:
        purchase = datetime.strptime(purchase_date, "%d/%m/%Y")
        maturity = datetime.strptime(maturity_date, "%d/%m/%Y")
        if maturity <= purchase:
            return None
        periods = compute_periods(maturity, purchase, coupon_frequency)
        if periods <= 0:
            return None

        accrued_interest = calculate_accrued_interest(par_value, coupon_rate, "20/09/2017", purchase_date, coupon_frequency)
        if math.isnan(accrued_interest):
            return None

        dirty_price = price + accrued_interest
        ytm = calculate_ytm(dirty_price, par_value, coupon_rate, periods, coupon_frequency)
        if math.isnan(ytm):
            return None

        modified_duration = calculate_modified_duration(par_value, coupon_rate, periods, ytm / 100, coupon_frequency)
        if math.isnan(modified_duration):
            return None

        result = AnalysisResult(ytm=ytm, accrued_interest=accrued_interest, modified_duration=modified_duration)
        return result.__dict__
    except Exception:
        return None
