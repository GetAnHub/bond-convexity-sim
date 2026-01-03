from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, render_template, request

from bondcalc.analytics import calculate_accrued_interest, compute_periods
from bondcalc.plotting import calculate_price_yield_derivative, generate_price_yield_curve
from bondcalc.pricing import bond_price, calculate_ytm

app = Flask(__name__)


DATA_PATH = Path(__file__).resolve().parent / "data" / "bonds.json"


def load_bonds() -> Dict[str, Dict[str, Any]]:
    if not DATA_PATH.exists():
        return {}
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_date(value: str) -> Optional[datetime.date]:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def _coerce_number(value: Any, cast=float) -> Optional[Any]:
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def _generate_yield_targets(ytm: float, max_points: int = 8) -> list[int]:
    if ytm is None or not math.isfinite(ytm):
        return []

    targets = {0}
    rounded_ytm = int(round(ytm))
    is_integer_ytm = float(ytm).is_integer()
    lower = math.floor(ytm)
    upper = math.ceil(ytm)

    while len(targets) < max_points:
        if lower >= 0 and not (is_integer_ytm and lower == rounded_ytm):
            targets.add(lower)
        if len(targets) >= max_points:
            break
        if upper >= 0 and not (is_integer_ytm and upper == rounded_ytm):
            targets.add(upper)
        lower -= 1
        upper += 1

    return sorted(targets)[:max_points]


def _build_price_change_profile(
    par_value: float,
    coupon_rate: float,
    periods: int,
    coupon_frequency: int,
    current_price: float,
    ytm: float,
) -> Dict[str, list]:
    if any(
        [
            par_value is None,
            coupon_rate is None,
            periods is None,
            coupon_frequency is None,
            current_price in (None, 0),
            ytm is None,
        ]
    ):
        return {"ytm": [], "price_change_pct": []}

    yield_targets = _generate_yield_targets(ytm)
    if not yield_targets:
        return {"ytm": [], "price_change_pct": []}

    deltas = []
    for target in yield_targets:
        price_at_yield = bond_price(
            par_value,
            coupon_rate,
            periods,
            target / 100,
            coupon_frequency,
        )
        if not math.isfinite(price_at_yield) or not math.isfinite(current_price):
            deltas.append(math.nan)
            continue
        deltas.append(((price_at_yield - current_price) / current_price) * 100)

    return {"ytm": yield_targets, "price_change_pct": deltas}


def _build_analysis(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    par_value = _coerce_number(payload.get("par_value"))
    coupon_rate = _coerce_number(payload.get("coupon_rate"))
    coupon_frequency = _coerce_number(payload.get("coupon_frequency"), int)
    price = _coerce_number(payload.get("price"))
    min_price = _coerce_number(payload.get("min_price"))
    max_price = _coerce_number(payload.get("max_price"))
    num_points = _coerce_number(payload.get("num_points"), int) or 50

    issue_date = _parse_date(payload.get("issue_date"))
    maturity_date = _parse_date(payload.get("maturity_date"))
    purchase_date = _parse_date(payload.get("purchase_date"))

    if not all([
        par_value is not None,
        coupon_rate is not None,
        coupon_frequency is not None,
        issue_date,
        maturity_date,
        purchase_date,
        price is not None,
        min_price is not None,
        max_price is not None,
    ]):
        return None, "Please provide valid numeric values and dates in DD/MM/YYYY format."

    periods = compute_periods(maturity_date, purchase_date, coupon_frequency)
    if periods <= 0:
        return None, "The purchase date must be before the maturity date."

    curve = generate_price_yield_curve(
        par_value,
        coupon_rate,
        periods,
        coupon_frequency,
        min_price,
        max_price,
        num_points=num_points,
    )
    derivative = calculate_price_yield_derivative(curve)

    accrued_interest = calculate_accrued_interest(
        par_value,
        coupon_rate,
        payload.get("issue_date"),
        payload.get("purchase_date"),
        coupon_frequency,
    )
    ytm = calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency)
    price_change = _build_price_change_profile(
        par_value,
        coupon_rate,
        periods,
        coupon_frequency,
        price,
        ytm,
    )

    summary = {
        "par_value": par_value,
        "coupon_rate": coupon_rate,
        "coupon_frequency": coupon_frequency,
        "issue_date": issue_date.strftime("%d/%m/%Y"),
        "maturity_date": maturity_date.strftime("%d/%m/%Y"),
        "purchase_date": purchase_date.strftime("%d/%m/%Y"),
        "price": price,
        "min_price": min_price,
        "max_price": max_price,
        "num_points": num_points,
        "periods": periods,
        "accrued_interest": accrued_interest,
        "ytm": ytm,
    }

    response = {
        "summary": summary,
        "curve": curve.to_dict(orient="list"),
        "derivative": derivative.to_dict(orient="list"),
        "price_change": price_change,
    }
    return response, None


@app.route("/")
def index():
    bonds = load_bonds()
    return render_template("index.html", bonds=bonds)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    data, error = _build_analysis(payload)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
