# Evaluated Pricing Pipeline for USD IG Corporate Bonds

## Overview
This project builds a mini evaluated-pricing workflow for USD investment-grade corporate bonds.

Instead of pricing a single bond in isolation, the pipeline:
- bootstraps a Treasury zero curve from market par yields
- computes bond analytics for a small universe of IG corporates
- selects comparable bonds using rule-based similarity scoring
- infers a fair spread for each target bond
- reprices bonds off the benchmark curve plus fair spread
- flags bonds for review when observed levels deviate from model-implied levels

The goal is to mimic the logic of an evaluated-pricing workflow:
consistent market inputs, transparent methodology, and exception-based review.

## Why this project
This project is designed to demonstrate the type of work relevant to fixed income evaluated pricing:
- market data normalization
- curve construction
- bond math and spread analysis
- relative value / comp-based valuation
- quality control and exception handling
- reproducible Python workflow

## Project scope
- 12–20 USD investment-grade corporate bonds
- 3–4 issuers
- plain-vanilla fixed-rate senior unsecured bonds
- maturity bucket roughly 2Y–10Y
- one evaluation date
- optional one-day comparison for rates vs spread attribution

## Methodology

### 1. Treasury benchmark curve
Treasury par yields are used to bootstrap a zero curve.
This provides discount factors for valuing future bond cash flows consistently.

### 2. Bond analytics
For each bond, the pipeline computes:
- accrued interest
- clean and dirty price
- yield to maturity
- modified duration
- convexity
- benchmark Treasury yield
- spread to benchmark

### 3. Comparable bond selection
For each target bond, candidate comps are scored using:
- issuer match
- rating bucket match
- seniority match
- maturity proximity
- coupon proximity
- same currency / plain-vanilla structure

Top-ranked comps are used to anchor fair value.

### 4. Fair spread inference
A fair spread is estimated from selected comps using weighted averaging or issuer-curve interpolation when possible.

### 5. Evaluated pricing
Each bond is repriced using:
- Treasury zero curve
- inferred fair spread

Outputs:
- observed price
- model price
- observed spread
- fair spread
- residuals

### 6. Quality control
Bonds are flagged when:
- spread residual is too large
- price residual is too large
- comp support is weak
- trade evidence is stale
- liquidity proxies are poor

## Repository structure

\`\`\`
ig_evaluator/
│
├─ data/
│  ├─ raw/
│  │  ├─ treasury_curve.csv
│  │  ├─ bond_universe.csv
│  │  └─ trades.csv
│  └─ processed/
│
├─ notebooks/
│  ├─ 01_curve_build.ipynb
│  ├─ 02_bond_analytics.ipynb
│  ├─ 03_comp_selection.ipynb
│  ├─ 04_evaluated_pricing.ipynb
│  └─ 05_review_pack.ipynb
│
├─ src/
│  ├─ curve.py
│  ├─ cashflows.py
│  ├─ bond_math.py
│  ├─ spreads.py
│  ├─ comps.py
│  ├─ evaluator.py
│  └─ qc.py
│
├─ outputs/
│  ├─ daily_eval_table.csv
│  ├─ flagged_bonds.csv
│  └─ charts/
│
├─ requirements.txt
└─ README.md
\`\`\`

## Example output
| Bond | Obs Px | Model Px | Obs Spread | Fair Spread | Residual (bp) | Flag |
|------|-------:|---------:|-----------:|------------:|--------------:|------|
| AAPL 2031 | 101.22 | 101.35 | 64 | 62 | 2 | Normal |
| MSFT 2031 | 100.88 | 101.10 | 59 | 54 | 5 | Review |
| JNJ 2030  | 99.95  | 100.40 | 71 | 60 | 11 | High Review |

## Key takeaways
- Evaluated pricing is more than a formula; it is a market-informed workflow.
- Treasury moves and spread moves should be separated.
- Peer selection quality matters.
- Liquidity and stale trading evidence affect confidence in the mark.

## Future extensions
- issuer spread curve fitting
- more robust liquidity scoring
- day-over-day attribution
- sector / rating spread normalization
- OAS framework for non-plain-vanilla bonds
