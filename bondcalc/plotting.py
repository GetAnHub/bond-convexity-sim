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
