from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from .analytics import calculate_ytm_from_bond_data, compute_periods
from .models import AnalysisRequest, AnalysisResult, Bond
from .plotting import plot_price_yield_curve, plot_price_yield_derivative

DATE_FORMAT = "%d/%m/%Y"


def _parse_date(date_str: str):
    return datetime.strptime(date_str, DATE_FORMAT).date()


def load_bonds(path: Path) -> Dict[str, Bond]:
    if not path.exists():
        raise FileNotFoundError(f"Bond definition file not found: {path}")
    data = None
    with path.open() as fh:
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise RuntimeError("PyYAML is required to read YAML bond files") from exc
            data = yaml.safe_load(fh)
        else:
            data = json.load(fh)
    bonds = {}
    for name, cfg in (data or {}).items():
        bonds[name] = Bond(
            name=name,
            par_value=float(cfg["par_value"]),
            coupon_rate=float(cfg["coupon_rate"]),
            coupon_frequency=int(cfg.get("coupon_frequency", 1)),
            issue_date=_parse_date(cfg["issue_date"]),
            maturity_date=_parse_date(cfg["maturity_date"]),
        )
    return bonds


def analyze_bond(bond: Bond, request: AnalysisRequest) -> AnalysisResult | None:
    result = calculate_ytm_from_bond_data(
        request.price,
        bond.par_value,
        bond.coupon_rate,
        bond.maturity_date.strftime(DATE_FORMAT),
        request.purchase_date.strftime(DATE_FORMAT),
        bond.coupon_frequency,
    )
    if result is None:
        return None
    curve = None
    if request.min_price is not None and request.max_price is not None:
        from .plotting import generate_price_yield_curve

        periods = compute_periods(bond.maturity_date, request.purchase_date, bond.coupon_frequency)
        curve = generate_price_yield_curve(
            bond.par_value,
            bond.coupon_rate,
            periods,
            bond.coupon_frequency,
            request.min_price,
            request.max_price,
            request.num_points,
        )
    return AnalysisResult(
        ytm=result["ytm"],
        accrued_interest=result["accrued_interest"],
        modified_duration=result["modified_duration"],
        curve=curve,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bondcalc", description="Bond analytics CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a bond by name")
    analyze.add_argument("bond_name", help="Name of the bond to analyze")
    analyze.add_argument("--bonds", default="bonds.yaml", help="Path to YAML/JSON bond definitions")
    analyze.add_argument("--price", required=True, type=float, help="Clean price of the bond")
    analyze.add_argument("--purchase-date", required=True, help="Purchase date (DD/MM/YYYY)")
    analyze.add_argument("--min-price", type=float, help="Minimum price for price-yield curve")
    analyze.add_argument("--max-price", type=float, help="Maximum price for price-yield curve")
    analyze.add_argument("--num-points", type=int, default=100, help="Number of price points for plotting")
    analyze.add_argument("--plot", action="store_true", help="Display the price-yield curve")
    analyze.add_argument("--save-plot", type=Path, help="Save plot to file")
    analyze.add_argument("--plot-derivative", action="store_true", help="Display the first derivative of the price-yield curve")
    analyze.add_argument("--save-derivative", type=Path, help="Save derivative plot to file")
    return parser


def _print_result(bond: Bond, result: AnalysisResult):
    print(f"Bond: {bond.name}")
    print(f"YTM: {result.ytm:.4f}%")
    print(f"Accrued Interest: {result.accrued_interest:.4f}")
    print(f"Modified Duration: {result.modified_duration:.4f} years")


def main(argv: Tuple[str, ...] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        bonds = load_bonds(Path(args.bonds))
        if args.bond_name not in bonds:
            parser.error(f"Bond '{args.bond_name}' not found in {args.bonds}")
        bond = bonds[args.bond_name]
        request = AnalysisRequest(
            price=args.price,
            purchase_date=_parse_date(args.purchase_date),
            min_price=args.min_price,
            max_price=args.max_price,
            num_points=args.num_points,
        )
        result = analyze_bond(bond, request)
        if result is None:
            parser.error("Unable to compute analytics for the provided bond and inputs")
        _print_result(bond, result)

        if result.curve is not None and (args.plot or args.save_plot):
            periods = compute_periods(bond.maturity_date, request.purchase_date, bond.coupon_frequency)
            curve = plot_price_yield_curve(
                bond.par_value,
                bond.coupon_rate,
                periods,
                bond.coupon_frequency,
                request.min_price,
                request.max_price,
                request.num_points,
                show=args.plot,
            )
            if args.save_plot:
                curve_plot = curve.plot(x="ytm", y="price", title=f"Price-Yield Curve: {bond.name}")
                fig = curve_plot.get_figure()
                fig.savefig(args.save_plot)
        if result.curve is not None and (args.plot_derivative or args.save_derivative):
            periods = compute_periods(bond.maturity_date, request.purchase_date, bond.coupon_frequency)
            derivative = plot_price_yield_derivative(
                bond.par_value,
                bond.coupon_rate,
                periods,
                bond.coupon_frequency,
                request.min_price,
                request.max_price,
                request.num_points,
                show=args.plot_derivative,
            )
            if args.save_derivative:
                derivative_plot = derivative.plot(
                    x="ytm", y="price_derivative", title=f"Price-Yield Derivative: {bond.name}"
                )
                fig = derivative_plot.get_figure()
                fig.savefig(args.save_derivative)
    return 0


if __name__ == "__main__":
    sys.exit(main())
