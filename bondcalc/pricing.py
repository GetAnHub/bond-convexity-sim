from __future__ import annotations

import math


def _is_invalid(*values):
    for value in values:
        if value is None:
            return True
        try:
            if math.isnan(float(value)):
                return True
        except (TypeError, ValueError):
            continue
    return False


def bond_price(par_value: float, coupon_rate: float, periods: int, ytm: float, coupon_frequency: int = 2):
    if _is_invalid(par_value, coupon_rate, periods, ytm) or periods <= 0:
        return math.nan
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        ytm = float(ytm)
        coupon = (coupon_rate / 100) * par_value / coupon_frequency
        discount_factor = 1 / (1 + ytm / coupon_frequency)
        coupon_pv = coupon * (1 - discount_factor ** periods) / (ytm / coupon_frequency)
        par_pv = par_value * discount_factor ** periods
        return coupon_pv + par_pv
    except (ValueError, TypeError):
        return math.nan


def _newton(func, guess: float, maxiter: int = 150, tol: float = 1e-8):
    x = guess
    for _ in range(maxiter):
        fx = func(x)
        h = 1e-5
        derivative = (func(x + h) - fx) / h
        if derivative == 0:
            break
        step = fx / derivative
        x -= step
        if abs(step) < tol:
            return x
    raise RuntimeError("Newton method did not converge")


def calculate_ytm(price: float, par_value: float, coupon_rate: float, periods: int, coupon_frequency: int = 2):
    if _is_invalid(price, par_value, coupon_rate, periods) or periods <= 0:
        return math.nan

    price = float(price)
    par_value = float(par_value)
    coupon_rate = float(coupon_rate)

    def bond_price_error(ytm_guess: float):
        return bond_price(par_value, coupon_rate, periods, ytm_guess, coupon_frequency) - price

    try:
        ytm = _newton(bond_price_error, 0.05, maxiter=150)
        return ytm * 100
    except (ValueError, TypeError, RuntimeError):
        return math.nan
