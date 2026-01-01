import json
import math
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("pandas")

from bondcalc.analytics import compute_periods
from bondcalc.plotting import (
    calculate_price_yield_derivative,
    generate_price_yield_curve,
    plot_price_yield_derivative,
)


def test_calculate_price_yield_derivative():
    curve = generate_price_yield_curve(100, 5.0, 10, 1, 90, 110, 8)
    derivative = calculate_price_yield_derivative(curve)

    # derivatives should align with unique, finite ytm values
    expected_count = (
        curve[["ytm", "price"]]
        .replace([math.inf, -math.inf], math.nan)
        .dropna()
        .drop_duplicates(subset="ytm")
        .shape[0]
    )

    assert not derivative.empty
    assert derivative.shape[0] == expected_count
    assert derivative["price_derivative"].isna().sum() == 0
    assert derivative["ytm"].is_monotonic_increasing


def test_plot_price_yield_derivative_returns_data():
    derivative = plot_price_yield_derivative(100, 4.5, 12, 2, 95, 105, 6, show=False)

    assert not derivative.empty
    assert set(derivative.columns) == {"ytm", "price_derivative"}


def test_price_yield_curve_is_convex_for_long_maturity_bond():
    bonds = json.loads(Path("data/bonds.json").read_text(encoding="utf-8"))
    euro_bond = bonds["EuroBondExample"]

    purchase_date = datetime.strptime(euro_bond["purchase_date"], "%d/%m/%Y").date()
    maturity_date = datetime.strptime(euro_bond["maturity_date"], "%d/%m/%Y").date()
    periods = compute_periods(maturity_date, purchase_date, euro_bond["coupon_frequency"])

    curve = generate_price_yield_curve(
        euro_bond["par_value"],
        euro_bond["coupon_rate"],
        periods,
        euro_bond["coupon_frequency"],
        euro_bond["min_price"],
        euro_bond["max_price"],
        euro_bond["num_points"],
    )

    ytms = curve["ytm"].tolist()
    prices = curve["price"].tolist()

    assert curve.shape[0] == len(set(ytms))
    assert all(math.isfinite(value) for value in ytms + prices)
    assert all(next_ytm > prev_ytm for prev_ytm, next_ytm in zip(ytms, ytms[1:]))

    tolerance = 1e-4
    price_steps = [next_price - prev_price for prev_price, next_price in zip(prices, prices[1:])]
    assert all(step <= tolerance for step in price_steps)

    slopes = []
    for idx, delta_price in enumerate(price_steps, start=1):
        delta_yield = ytms[idx] - ytms[idx - 1]
        assert delta_yield > 0
        slopes.append(delta_price / delta_yield)

    assert slopes[0] < slopes[-1]
    slope_deltas = [next_slope - prev_slope for prev_slope, next_slope in zip(slopes, slopes[1:])]
    assert all(delta >= -tolerance for delta in slope_deltas)
