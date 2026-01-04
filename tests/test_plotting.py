import json
import math
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("pandas")

from bondcalc.analytics import compute_periods
from bondcalc.plotting import (
    calculate_convexity_curve,
    calculate_modified_duration_curve,
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


def test_modified_duration_curve_tracks_curve_length():
    curve = generate_price_yield_curve(100, 5.5, 10, 2, 90, 110, 12)
    durations = calculate_modified_duration_curve(curve)

    assert not durations.empty
    assert set(durations.columns) == {"ytm", "modified_duration"}
    assert durations.shape[0] == curve.drop_duplicates(subset="ytm").shape[0]
    assert durations["modified_duration"].isna().sum() == 0


def test_convexity_curve_is_monotonic_with_ytm():
    curve = generate_price_yield_curve(100, 4.0, 8, 2, 95, 105, 10)
    convexity = calculate_convexity_curve(curve)

    assert not convexity.empty
    assert convexity["ytm"].is_monotonic_increasing
    assert convexity.shape[0] == curve.drop_duplicates(subset="ytm").shape[0]
