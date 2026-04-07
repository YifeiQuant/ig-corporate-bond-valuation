# Review Pack

Evaluation date: 1991-03-14
Universe size: 8 bonds
Review population: 6 bonds
High review population: 3 bonds
Average absolute spread residual: 19.70 bps
Average absolute price residual: 1.1745

## Key observations

- This demo follows an exception-based valuation workflow: only bonds with meaningful residuals or weak peer support are escalated.
- Residuals here are driven by synthetic sample data, so the review list demonstrates process rather than real market dislocations.
- The comp engine is transparent and rule-based, which is useful for defending methodology in an interview setting.

## Flagged bonds

| Bond | Flag | Spread Residual (bps) | Price Residual | Comp Count | Reason |
|------|------|----------------------:|---------------:|-----------:|--------|
| GE_1998_725 | Review | 15.26 | -0.9236 | 3 | moderate spread residual; moderate price residual |
| IBM_1996_700 | Review | -13.04 | 0.6186 | 3 | moderate spread residual; moderate price residual |
| XOM_1997_710 | Review | -13.75 | 0.6810 | 3 | moderate spread residual; moderate price residual |
| XOM_2001_760 | High Review | 50.53 | -3.8602 | 3 | large spread residual; large price residual |
| JNJ_2000_740 | High Review | 30.29 | -2.0936 | 3 | large spread residual; large price residual |
| JNJ_1995_675 | High Review | -26.60 | 1.0374 | 3 | large spread residual; large price residual |

## Charts

- Spread residual chart: `outputs\charts\spread_residuals.png`
- Price residual chart: `outputs\charts\price_residuals.png`
