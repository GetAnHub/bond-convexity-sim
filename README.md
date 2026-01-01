# bond-convexity-sim
A tool to view and analyze the convexity of a bond.

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

You can point the CLI at this file and request analytics and a price–yield curve:

```bash
python -m bondcalc analyze EuroBondExample \
  --bonds tests/data/sample_bond.yaml \
  --price 980 \
  --purchase-date 15/03/2025 \
  --min-price 950 --max-price 1050 --num-points 50 --plot
```
