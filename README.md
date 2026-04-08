# IG Corporate Bond Valuation

Right now comp selection is just a simple rules-based score.

A suggestion I got while discussing this project, and not something I had originally planned myself, was to try an unsupervised ML approach for comp selection, maybe clustering or nearest neighbors. I liked that idea because bond universes can vary a lot in size and I usually would not have labeled examples of what counts as a "good comp."

Along the same lines, I would only reach for something like LightGBM if I actually had labeled comp-quality data, like trader-selected peers or some historical measure of which comps gave the best pricing support. Without that kind of label set, clustering feels like the more natural place for me to start.

## Overview
This repo is a small pricing exercise for USD investment-grade corporate bonds.

The pipeline does five things:
- builds a Treasury zero curve from par yields
- calculates bond analytics for a small corporate sample
- scores peer bonds with a simple rules-based comp model
- estimates a peer-implied fair spread for each bond
- reprices the bonds and flags the ones that look offside

## Why I Built It
I wanted one project that tied together curve construction, bond math, and relative-value checks.

Most bond examples stop at yield or duration. Here I wanted to go one step further: start with benchmark rates, measure each bond versus Treasury, compare it with a few similar bonds, and finish with a short review list.

## Current Dataset
The current run uses an evaluation date of April 6, 2026.

Raw inputs:
- 2026 year-to-date Treasury par yields in [data/raw/treasury_curve.csv](data/raw/treasury_curve.csv)
- an 8-bond USD investment-grade sample in [data/raw/bond_universe.csv](data/raw/bond_universe.csv)

The bond sample is a curated subset of recent large-cap issuers built from public holdings data and vendor prices. Ratings are normalized issuer-level buckets so the comp logic has a consistent input set.

## What The Project Does

### 1. Treasury curve construction
The project loads Treasury par yields, converts standard tenors into year fractions, and bootstraps discount factors and zero rates.

Output:
- [data/processed/zero_curve_2026-04-06.csv](data/processed/zero_curve_2026-04-06.csv)

### 2. Bond analytics
For each bond in [data/raw/bond_universe.csv](data/raw/bond_universe.csv), the pipeline computes:
- accrued interest
- dirty price
- yield to maturity
- spread to Treasury
- modified duration
- convexity

Output:
- [outputs/bond_analytics.csv](outputs/bond_analytics.csv)

### 3. Comparable-bond selection
Each target bond is scored against the rest of the sample using:
- issuer
- rating
- seniority
- sector
- currency
- maturity gap
- coupon gap
- spread gap

Output:
- [outputs/comp_selection.csv](outputs/comp_selection.csv)

### 4. Fair-spread estimate and repricing
The top-ranked comps are used to estimate a fair spread for each bond. The bond is then repriced off the Treasury zero curve plus that spread.

Outputs:
- [outputs/daily_eval_table.csv](outputs/daily_eval_table.csv)
- [outputs/flagged_bonds.csv](outputs/flagged_bonds.csv)

### 5. Review pack
The repo also writes a short summary with the flagged names and residual charts.

Outputs:
- [outputs/review_summary.csv](outputs/review_summary.csv)
- [outputs/review_pack_flagged.csv](outputs/review_pack_flagged.csv)
- [outputs/review_pack.md](outputs/review_pack.md)
- [outputs/charts/spread_residuals.png](outputs/charts/spread_residuals.png)
- [outputs/charts/price_residuals.png](outputs/charts/price_residuals.png)

## Repository Structure
```text
ig-corporate-bond-valuation/
|-- data/
|   |-- processed/
|   `-- raw/
|       |-- bond_universe.csv
|       `-- treasury_curve.csv
|-- notebooks/
|   |-- 01_curve_build.ipynb
|   |-- 02_bond_analytics.ipynb
|   |-- 03_comp_selection.ipynb
|   |-- 04_evaluated_pricing.ipynb
|   `-- 05_review_pack.ipynb
|-- outputs/
|   |-- charts/
|   |-- bond_analytics.csv
|   |-- comp_selection.csv
|   |-- daily_eval_table.csv
|   |-- flagged_bonds.csv
|   |-- review_pack.md
|   |-- review_pack_flagged.csv
|   `-- review_summary.csv
|-- scripts/
|   |-- build_zero_curve.py
|   |-- generate_review_pack.py
|   |-- run_bond_analytics.py
|   `-- run_evaluated_pricing.py
|-- src/
|   |-- bond_math.py
|   |-- cashflows.py
|   |-- comps.py
|   |-- curve.py
|   |-- evaluator.py
|   `-- qc.py
|-- requirements.txt
`-- README.md
```

## Setup
I ran this locally with Conda on Windows using Anaconda installed at `C:\ProgramData\anaconda3`.

Create the environment:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' create -n bondval python=3.13 -y
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n bondval python -m pip install -r requirements.txt
```

## Run Order
Run the pipeline in this order:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n bondval python scripts\build_zero_curve.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n bondval python scripts\run_bond_analytics.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n bondval python scripts\run_evaluated_pricing.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n bondval python scripts\generate_review_pack.py
```

## Reading The Current Results
Because the bond universe is small and the prices come from public holdings data, the residuals are noisy.

That means:
- the outputs are better read as a relative-value exercise than as tradable signals
- review flags are mainly a way to highlight outliers inside this small sample
- large residuals are not automatically bugs; they often reflect the limited comp set

## Limitations
This version is still simplified:
- one evaluation date
- small curated bond universe
- vendor-priced holdings data rather than recent trade data
- normalized issuer-level ratings rather than a full security-master feed
- no issuer curve fitting
- no liquidity score or trade-timeliness model
- no OAS or optionality handling

## Possible Next Steps
If I keep extending it, the next additions I would look at are:
- a larger issuer universe with richer trade data
- trying clustering or nearest-neighbor methods for comp selection
- issuer spread curve fitting instead of weighted-average comp spreads
- Treasury-move versus spread-move attribution
- trade staleness and liquidity-confidence scoring
- a cleaner daily report export
