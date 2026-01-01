from pathlib import Path
import json

from bondcalc.cli import analyze_bond, build_parser, load_bonds, _parse_date
from bondcalc.models import AnalysisRequest


def test_argument_parsing():
    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "test-bond",
            "--price",
            "99",
            "--purchase-date",
            "01/01/2030",
        ]
    )
    assert args.command == "analyze"
    assert args.bond_name == "test-bond"
    assert args.price == 99
    assert args.plot is False
    assert args.plot_derivative is False
    assert args.save_derivative is None


def test_analyze_bond_flow(tmp_path):
    bond_file = tmp_path / "bonds.json"
    bond_data = {
        "TestBond": {
            "par_value": 100,
            "coupon_rate": 5.0,
            "coupon_frequency": 1,
            "issue_date": "01/01/2020",
            "maturity_date": "01/01/2031",
        }
    }
    bond_file.write_text(json.dumps(bond_data))

    bonds = load_bonds(bond_file)
    bond = bonds["TestBond"]
    request = AnalysisRequest(price=95.0, purchase_date=_parse_date("01/01/2025"))
    result = analyze_bond(bond, request)
    assert result is not None
    assert result.ytm > 0
    assert result.modified_duration > 0
