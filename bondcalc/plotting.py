from __future__ import annotations

import math
from typing import Tuple

from .pricing import calculate_ytm


def calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100) -> Tuple[list, list]:
    try:
        step = (max_price - min_price) / (num_points - 1)
        prices = [min_price + i * step for i in range(num_points)]
        ytms = []
        for price in prices:
            ytm = calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency)
            ytms.append(ytm if not math.isnan(ytm) else math.nan)
        return prices, ytms
    except Exception:
        return None, None


def _ensure_pandas():
    try:
        import pandas as pd

        return pd
    except ImportError as exc:
        raise RuntimeError("pandas is required for curve generation") from exc


def _compute_first_derivative(xs, ys):
    derivatives = []
    for idx in range(len(xs)):
        if idx == 0:
            delta_x = xs[1] - xs[0]
            delta_y = ys[1] - ys[0]
        elif idx == len(xs) - 1:
            delta_x = xs[-1] - xs[-2]
            delta_y = ys[-1] - ys[-2]
        else:
            delta_x = xs[idx + 1] - xs[idx - 1]
            delta_y = ys[idx + 1] - ys[idx - 1]

        if delta_x == 0 or any(math.isnan(val) for val in (delta_x, delta_y)):
            derivatives.append(math.nan)
        else:
            derivatives.append(delta_y / delta_x)
    return derivatives


def _prepare_clean_curve(curve, columns):
    pd = _ensure_pandas()
    if curve is None or getattr(curve, "empty", True):
        return pd.DataFrame(columns=columns)

    cleaned_curve = (
        curve[["ytm", "price"]]
        .replace([math.inf, -math.inf], math.nan)
        .dropna()
        .sort_values("ytm")
        .drop_duplicates(subset="ytm")
    )
    if cleaned_curve.empty or len(cleaned_curve.index) < 2:
        return pd.DataFrame(columns=columns)
    return cleaned_curve.reset_index(drop=True)


def calculate_price_yield_derivative(curve):
    pd = _ensure_pandas()
    cleaned_curve = _prepare_clean_curve(curve, ["ytm", "price_derivative"])
    if cleaned_curve.empty:
        return cleaned_curve

    ytms = list(cleaned_curve["ytm"].tolist())
    prices = list(cleaned_curve["price"].tolist())
    ytms_decimal = [ytm / 100 for ytm in ytms]
    derivatives_decimal = _compute_first_derivative(ytms_decimal, prices)
    derivatives_percent = [
        math.nan if math.isnan(val) else val / 100 for val in derivatives_decimal
    ]
    cleaned_curve["price_derivative"] = derivatives_percent
    return cleaned_curve[["ytm", "price_derivative"]]


def calculate_modified_duration_curve(curve):
    pd = _ensure_pandas()
    cleaned_curve = _prepare_clean_curve(curve, ["ytm", "modified_duration"])
    if cleaned_curve.empty:
        return cleaned_curve

    ytms_decimal = [ytm / 100 for ytm in cleaned_curve["ytm"].tolist()]
    prices = cleaned_curve["price"].tolist()
    first_derivative = _compute_first_derivative(ytms_decimal, prices)

    durations = []
    for price, d_price in zip(prices, first_derivative):
        if price in (0, math.inf, -math.inf) or math.isnan(price) or math.isnan(d_price):
            durations.append(math.nan)
            continue
        durations.append(-(d_price / price))

    cleaned_curve["modified_duration"] = durations
    return cleaned_curve[["ytm", "modified_duration"]]


def calculate_convexity_curve(curve):
    pd = _ensure_pandas()
    cleaned_curve = _prepare_clean_curve(curve, ["ytm", "convexity"])
    if cleaned_curve.empty:
        return cleaned_curve

    ytms_decimal = [ytm / 100 for ytm in cleaned_curve["ytm"].tolist()]
    prices = cleaned_curve["price"].tolist()

    first_derivative = _compute_first_derivative(ytms_decimal, prices)
    second_derivative = _compute_first_derivative(ytms_decimal, first_derivative)

    cleaned_curve["convexity"] = [
        math.nan if math.isnan(val) else val for val in second_derivative
    ]
    return cleaned_curve[["ytm", "convexity"]]


def generate_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    prices, ytms = calculate_ytm_range(
        par_value,
        coupon_rate,
        periods,
        coupon_frequency,
        min_price,
        max_price,
        num_points,
    )
    pd = _ensure_pandas()
    if prices is None or ytms is None:
        return pd.DataFrame(columns=["ytm", "price"])
    return (
        pd.DataFrame({"ytm": ytms, "price": prices})
        .replace([math.inf, -math.inf], math.nan)
        .dropna()
        .sort_values("ytm")
        .drop_duplicates(subset="ytm")
        .reset_index(drop=True)
    )


def plot_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100, show=True, ax=None):
    curve = generate_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)
    if curve.empty:
        return curve

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for plotting") from exc

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    ax.plot(curve["ytm"], curve["price"], label="Price-Yield Curve", color="blue")
    ax.set_xlabel("Yield to Maturity (%)")
    ax.set_ylabel("Bond Price")
    ax.set_title("Price-Yield Curve for Bond")
    ax.grid(True)
    ax.legend()
    if show:
        plt.show()
    return curve


def plot_price_yield_derivative(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100, show=True, ax=None):
    curve = generate_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)
    derivative = calculate_price_yield_derivative(curve)
    if derivative.empty:
        return derivative

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for plotting") from exc

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    ax.plot(derivative["ytm"], derivative["price_derivative"], label="dPrice/dYTM", color="orange")
    ax.set_xlabel("Yield to Maturity (%)")
    ax.set_ylabel("Price Sensitivity")
    ax.set_title("First Derivative of Price-Yield Curve")
    ax.grid(True)
    ax.legend()
    if show:
        plt.show()
    return derivative
