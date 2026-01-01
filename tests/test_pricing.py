import math
from datetime import date

import bondcalc
from bondcalc.analytics import calculate_modified_duration


def test_bond_price_matches_expected():
    price = bondcalc.bond_price(100, 5.0, 4, 0.04, coupon_frequency=2)
    assert math.isclose(price, 101.903864, rel_tol=1e-6)


def test_calculate_ytm_solves_price():
    target_price = 101.90386434933714
    ytm = bondcalc.calculate_ytm(target_price, 100, 5.0, 4, coupon_frequency=2)
    assert math.isclose(ytm, 4.0, rel_tol=1e-4)


def test_modified_duration():
    duration = calculate_modified_duration(100, 5.0, 5, 0.04, coupon_frequency=1)
    assert math.isclose(duration, 4.381814, rel_tol=1e-6)
