# Evaluated Pricing Pipeline for USD IG Corporate Bonds

## Overview
This project is my attempt to build a small evaluated-pricing workflow for USD investment-grade corporate bonds.

Instead of looking at one bond in isolation, the pipeline:
- bootstraps a Treasury zero curve from par yields
- computes bond-level analytics for a small corporate universe
- scores comparable bonds using transparent rule-based logic
- infers a fair spread for each target bond from peer bonds
- reprices each bond off Treasury plus fair spread
- flags exceptions for analyst review

What I like about this problem is that it sits in between bond math and market workflow. You need a benchmark curve, security-level analytics, a sensible way to choose comps, and then some process for deciding which names actually deserve attention.

## Why I Built This
I wanted to understand evaluated pricing as a process rather than as a single pricing formula.

The parts that interested me most were:
- market data normalization
- benchmark curve construction
- bond analytics and spread measurement
- peer-based relative value
- exception-based review

This also felt like a good way to learn more fixed-income workflow while keeping the implementation transparent enough that I can follow every step.

## What The Project Does

### 1. Treasury curve construction
The project loads Treasury par yields from [treasury_curve.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\data\raw\treasury_curve.csv), converts standard tenors into year fractions, and bootstraps discount factors and zero rates.

Output:
- [zero_curve_1991-03-14.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\data\processed\zero_curve_1991-03-14.csv)

### 2. Bond analytics
For each bond in [bond_universe.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\data\raw\bond_universe.csv), the pipeline computes:
- accrued interest
- dirty price
- yield to maturity
- spread to Treasury curve
- modified duration
- convexity

Output:
- [bond_analytics.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\bond_analytics.csv)

### 3. Comparable bond selection
Each target bond is matched against peer bonds using a simple score based on:
- issuer match
- rating match
- seniority match
- sector match
- currency match
- maturity proximity
- coupon proximity
- spread proximity

Output:
- [comp_selection.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\comp_selection.csv)

### 4. Evaluated pricing
The top-ranked comps are used to infer a fair spread for each bond. Each bond is then repriced off the Treasury curve plus that fair spread.

Outputs:
- [daily_eval_table.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\daily_eval_table.csv)
- [flagged_bonds.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\flagged_bonds.csv)

### 5. Review pack
The repo also generates a short review pack with summary metrics, flagged bonds, and charts.

Outputs:
- [review_summary.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\review_summary.csv)
- [review_pack_flagged.csv](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\review_pack_flagged.csv)
- [review_pack.md](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\review_pack.md)
- [spread_residuals.png](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\charts\spread_residuals.png)
- [price_residuals.png](C:\Users\Yifei\Documents\GitHub\jpm-ig-bond-valuation\outputs\charts\price_residuals.png)

## Repository Structure
```text
jpm-ig-bond-valuation/
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

## Interpreting The Current Results
The current bond universe is a small synthetic sample, so the point here is the workflow more than the exact market levels.

That means:
- the process is realistic even if the inputs are simplified
- flagged bonds should be read as examples of exception review
- large or negative residuals are not a bug by themselves; in this setup they mostly reflect synthetic data

## Workflow Summary
The workflow is:

1. Build a Treasury benchmark curve from par yields.
2. Compute bond-level analytics from observed prices.
3. Select comparable bonds using transparent similarity rules.
4. Infer a fair spread from the selected peers.
5. Reprice each bond off Treasury plus fair spread.
6. Flag bonds whose observed levels differ meaningfully from the model view.

## Limitations
This version is still pretty simplified:
- one evaluation date
- small bond universe
- synthetic bond sample
- no issuer curve fitting
- no liquidity score or trade-timeliness model
- no OAS or optionality handling

## Next Extensions
If I keep extending this, the next things I would want to add are:
- larger issuer universe and more realistic bond reference data
- issuer spread curve fitting instead of weighted-average comp spreads
- day-over-day attribution of Treasury move versus spread move
- trade evidence staleness and liquidity-confidence scoring
- automated notebook or slide export for daily review
