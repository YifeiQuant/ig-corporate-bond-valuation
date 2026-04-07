# Review Pack

Evaluation date: 2026-04-06
Universe size: 8 bonds
Review population: 8 bonds
High review population: 5 bonds
Average absolute spread residual: 23.75 bps
Average absolute price residual: 1.7066

## Key observations

- This demo follows an exception-based valuation workflow: only bonds with meaningful residuals or weak peer support are escalated.
- The current universe uses recent public bond holdings data and vendor prices, so it is more market-linked than the original synthetic sample while still remaining intentionally small.
- Residuals here mostly reflect the simplified comp methodology and limited universe, so they should be read as workflow signals rather than direct trading recommendations.
- The comp engine is transparent and rule-based, which is useful for defending methodology in an interview setting.

## Flagged bonds

| Bond | Flag | Spread Residual (bps) | Price Residual | Comp Count | Reason |
|------|------|----------------------:|---------------:|-----------:|--------|
| PFE_2033_475 | Review | 9.22 | -0.5610 | 3 | moderate price residual; weak comp support |
| AMZN_2036_488 | Review | 7.95 | -0.6274 | 3 | moderate price residual |
| AMZN_2031_425 | Review | -15.84 | 0.7022 | 3 | moderate spread residual; moderate price residual |
| F_2033_713 | High Review | 41.89 | -2.6541 | 3 | large spread residual; large price residual; weak comp support |
| PFE_2053_530 | High Review | 37.82 | -5.0634 | 3 | large spread residual; large price residual; weak comp support |
| META_2035_488 | High Review | 26.16 | -2.0076 | 3 | large spread residual; large price residual |
| META_2030_420 | High Review | -20.51 | 0.8537 | 3 | large spread residual; moderate price residual |
| F_2030_400 | High Review | -30.61 | 1.1836 | 3 | large spread residual; large price residual; weak comp support |

## Charts

- Spread residual chart: `outputs\charts\spread_residuals.png`
- Price residual chart: `outputs\charts\price_residuals.png`
