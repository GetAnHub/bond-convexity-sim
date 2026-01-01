# bond-convexity-sim
A tool to view and analyze the convexity of a bond.

## Quick start
1. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install the runtime dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   * `pandas` for generating price–yield curve dataframes
   * `matplotlib` for optional plotting
   * `PyYAML` for loading YAML bond definitions (JSON works out-of-the-box)
3. Run analytics through the CLI (see example below). Use `pip install pytest` if you want to execute the test suite.

## Contributing notes
The project avoids committing binary artifacts (images, spreadsheets, notebooks) so the
GitHub-style PR flow in this environment remains compatible. If you need to surface
plot outputs or other visuals, prefer text-based formats (CSV/JSON for data, Markdown
for screenshots with links to generated artifacts) or regenerate the assets locally
instead of checking them into git.

## Sample bond definition
The CLI loads bonds from a YAML or JSON mapping of bond names to attributes. A minimal
YAML example lives at `tests/data/sample_bond.yaml`:

```yaml
EuroBondExample:
  par_value: 1000            # Face value of the bond
  coupon_rate: 4.5           # Annual coupon rate expressed in percent
  coupon_frequency: 2        # Number of coupon payments per year
  issue_date: "15/03/2020"   # DD/MM/YYYY
  maturity_date: "15/03/2030"
```

You can point the CLI at this file and request analytics, a price–yield curve, and its first derivative:

```bash
python -m bondcalc analyze EuroBondExample \
  --bonds tests/data/sample_bond.yaml \
  --price 980 \
  --purchase-date 15/03/2025 \
  --min-price 950 --max-price 1050 --num-points 50 --plot --plot-derivative
```

The derivative plot is computed from the simulated curve points using finite differences,
so you can visualize how sensitive price is to small changes in yield even without a
closed-form expression.

If you prefer JSON inputs, supply a `bonds.json` file with the same structure and omit
the YAML-specific dependency. For a quick sanity check of the codebase, run:

```bash
pytest -q
```
