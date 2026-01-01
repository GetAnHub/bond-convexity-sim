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


def calculate_price_yield_derivative(curve):
    pd = _ensure_pandas()
    if curve is None or getattr(curve, "empty", True):
        return pd.DataFrame(columns=["ytm", "price_derivative"])

    cleaned_curve = (
        curve[["ytm", "price"]]
        .replace([math.inf, -math.inf], math.nan)
        .dropna()
        .sort_values("ytm")
        .drop_duplicates(subset="ytm")
    )
    if cleaned_curve.empty or len(cleaned_curve.index) < 2:
        return pd.DataFrame(columns=["ytm", "price_derivative"])

    ytms = list(cleaned_curve["ytm"].tolist())
    prices = list(cleaned_curve["price"].tolist())
    derivatives = []
    for idx in range(len(ytms)):
        if idx == 0:
            delta_ytm = ytms[1] - ytms[0]
            delta_price = prices[1] - prices[0]
        elif idx == len(ytms) - 1:
            delta_ytm = ytms[-1] - ytms[-2]
            delta_price = prices[-1] - prices[-2]
        else:
            delta_ytm = ytms[idx + 1] - ytms[idx - 1]
            delta_price = prices[idx + 1] - prices[idx - 1]

        derivative = math.nan if delta_ytm == 0 else delta_price / delta_ytm
        derivatives.append(derivative)
    return pd.DataFrame({"ytm": ytms, "price_derivative": derivatives})


def generate_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    prices, ytms = calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)
    pd = _ensure_pandas()
    if prices is None or ytms is None:
        return pd.DataFrame(columns=["ytm", "price"])
    return pd.DataFrame({"ytm": ytms, "price": prices})


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
