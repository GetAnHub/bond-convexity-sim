from bondcalc import (
    AnalysisRequest,
    AnalysisResult,
    Bond,
    bond_price as _bond_price,
    calculate_accrued_interest as _calculate_accrued_interest,
    calculate_modified_duration as _calculate_modified_duration,
    calculate_ytm as _calculate_ytm,
    calculate_ytm_from_bond_data as _calculate_ytm_from_bond_data,
    calculate_ytm_range as _calculate_ytm_range,
    generate_price_yield_curve as _generate_price_yield_curve,
    plot_price_yield_curve as _plot_price_yield_curve,
)


# Existing functions (delegated)
def convert_date(date_str):
    if date_str is None or not isinstance(date_str, str):
        return date_str
    try:
        date_str = " ".join(date_str.split()).strip()
        month_map = {
            "Jan": "1",
            "Feb": "2",
            "Mar": "3",
            "Apr": "4",
            "May": "5",
            "Jun": "6",
            "Jul": "7",
            "Aug": "8",
            "Sep": "9",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        month = date_str[:3]
        month_num = month_map.get(month)
        if not month_num:
            return date_str
        date_clean = date_str.replace(month + " ", month_num + "/").replace(", ", "/"
        )
        from datetime import datetime

        date_obj = datetime.strptime(date_clean, "%m/%d/%Y")
        return date_obj.strftime("%d/%m/%Y")
    except Exception:
        return date_str


def bond_price(par_value, coupon_rate, periods, ytm, coupon_frequency=2):
    return _bond_price(par_value, coupon_rate, periods, ytm, coupon_frequency)


def calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency=2):
    return _calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency)


def calculate_accrued_interest(par_value, coupon_rate, issue_date, purchase_date, coupon_frequency=1):
    return _calculate_accrued_interest(par_value, coupon_rate, issue_date, purchase_date, coupon_frequency)


def calculate_modified_duration(par_value, coupon_rate, periods, ytm, coupon_frequency=1):
    return _calculate_modified_duration(par_value, coupon_rate, periods, ytm, coupon_frequency)


def calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    return _calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)


def plot_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    return _plot_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)


def calculate_ytm_from_bond_data(
    price,
    par_value,
    coupon_rate,
    maturity_date,
    purchase_date,
    coupon_frequency=1,
    issue_price=None,
    min_price=None,
    max_price=None,
):
    return _calculate_ytm_from_bond_data(
        price,
        par_value,
        coupon_rate,
        maturity_date,
        purchase_date,
        coupon_frequency,
        issue_price,
        min_price,
        max_price,
    )


if __name__ == "__main__":
    from bondcalc.cli import main

    raise SystemExit(main())
