# APAC Market Expansion Decision Engine

## TL;DR
End-to-end decision support tool that prioritises APAC expansion markets using public country-level indicators, standardised scoring, and Multi-Criteria Decision Analysis (MCDA) with configurable weights, delivered via an interactive Streamlit dashboard and an executive PowerPoint output.

Base-case Top 5 markets: AUS (0.460), SGP (0.454), JPN (0.272), KOR (0.234), NZL (0.123) (from outputs/market_scores.csv).

Base weights (configurable): Market Size 25%, Purchasing Power 20%, Digital Readiness 20%, Governance Risk 20%, Corruption Risk 15% (from config/weights.yml).

Explainability built-in: component scores are exported per market; for AUS, the strongest positive contributors are Purchasing Power (+0.231), Governance Risk (+0.194), and Digital Readiness (+0.154), offset by Market Size (-0.120) (from outputs/market_scores.csv).

Uncertainty and economics stress-tested: Monte Carlo simulation generates 12-month revenue distributions for the top-ranked market; under the current assumptions the 12-month net revenue is negative on average (mean -$203,686; P10 -$347,955; P90 -$77,555) and payback is not achieved within 12 months (from outputs/monte_carlo_summary.csv and outputs/payback_distribution.csv).

Sensitivity analysis: weight sensitivity is computed in the dashboard using stored sensitivity outputs (outputs/dashboard_data.pkl) to show how top-market recommendations shift under different strategic priorities.

## Overview

This repository contains an end-to-end decision support tool for prioritising market expansion opportunities across the Asia-Pacific (APAC) region. It is designed for situations where expansion decisions involve real trade-offs between opportunity and risk, and where the “right” answer depends on strategic priorities rather than a single metric.

The tool pulls trusted public economic and governance indicators, transforms them into comparable features, and aggregates them into an overall market ranking using Multi-Criteria Decision Analysis (MCDA) with configurable weights. To avoid false confidence, it pairs base-case rankings with stress-testing: users can explore how recommendations shift under different weighting assumptions through the Streamlit dashboard, and assess 12-month revenue uncertainty for the top-ranked market via Monte Carlo simulation. Outputs are packaged for decision-makers, including ranked score tables, simulation summaries, and an executive-style PowerPoint deck.
---

## Business Problem

Companies expanding into new international markets face trade-offs between opportunity and risk. Market size, purchasing power, digital readiness, and regulatory quality all matter, but the relative importance of each depends on strategic priorities.

This project addresses the question:

> *Which APAC markets should be prioritised for expansion, and how confident can we be in those recommendations given uncertainty in assumptions and weighting?*

---

## Approach

The project follows a consulting-style analytical workflow:

1. **Data collection**
   Pulls real, publicly available country-level data from trusted international sources.

2. **Feature engineering**
   Transforms raw indicators into comparable, standardised metrics across markets.

3. **Multi-criteria decision analysis (MCDA)**
   Aggregates multiple drivers into a single comparative ranking using configurable weights.

4. **Sensitivity analysis**
   Tests how rankings change when strategic priorities (weights) are adjusted.

5. **Monte Carlo simulation**
   Models uncertainty in assumptions to assess the stability of rankings and revenue outcomes.

6. **Executive delivery**
   Results are presented through an interactive dashboard and a board-style PowerPoint deck.

---

## Data Sources

All data is sourced from reputable public datasets:

* **World Bank API**

  * GDP per capita
  * Population
  * Internet users (%)

* **Worldwide Governance Indicators (WGI)**

  * Regulatory quality
  * Rule of law

* **Our World in Data (OWID)**

  * Corruption Perceptions Index (CPI)

Downloaded data is cached locally to ensure reproducibility and avoid repeated API calls.

---

## Key Outputs

After running the pipeline, the following outputs are generated in the `outputs/` directory:

* `market_scores.csv`
  Final market rankings and component scores.

* `monte_carlo_results.csv`
  Full simulation results across scenarios.

* `monte_carlo_summary.csv`
  Summary statistics of simulated outcomes.

* `payback_distribution.csv`
  Distribution of estimated payback periods.

* `dashboard_data.pkl`
  Pre-processed data used by the Streamlit dashboard.

* `apac_expansion_recommendations.pptx`
  Executive-ready PowerPoint summarising findings and recommendations.

---

## Interactive Dashboard

An interactive Streamlit dashboard allows users to:

* Explore market rankings dynamically
* Adjust weighting assumptions in real time
* Compare country profiles across key dimensions
* Visualise sensitivity and scenario outcomes

This enables stakeholders to understand **why** a market ranks highly, not just **that** it does.

---

## Project Structure

```
.
├── src/
│   ├── data_sources/        # Data ingestion from public APIs
│   ├── features/            # Feature engineering and standardisation
│   ├── models/              # Scoring, forecasting, and simulation
│   ├── dashboards/          # Streamlit dashboard
│   └── reporting/           # PowerPoint generation
├── config/                  # Markets, weights, and business assumptions
├── data/
│   ├── raw/                 # Cached raw data
│   └── processed/           # Engineered features
├── outputs/                 # Final outputs and reports
├── tests/                   # Unit tests
├── README.md
└── requirements.txt
```

---

## Quick Start

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
python -m src.main
```

This will download data, build features, score markets, run simulations, and generate all outputs.

### Launch the Dashboard

```bash
streamlit run src/dashboards/app.py
```

---

## Configuration

All key assumptions are configurable:

* `config/markets.yml` – markets included in the analysis
* `config/weights.yml` – criteria weights and sensitivity ranges
* `config/assumptions.yml` – business and revenue assumptions

This allows the model to be adapted to different strategic contexts without changing code.

---

## Why Sensitivity Analysis Matters

Single-point rankings can create false confidence. This project explicitly tests how recommendations change when assumptions shift, helping distinguish **robust decisions** from **assumption-driven outcomes**.

This mirrors real consulting practice, where decision quality is judged not just on the answer, but on how resilient it is to uncertainty.

---

## Intended Use

This project was built as a strategy and analytics exercise and is intended for:

* Consulting and strategy roles
* Market entry and international expansion analysis
* Decision-making under uncertainty
* Portfolio prioritisation problems

---

## Author

**Adam Lababidi**
Electrical Engineering student with a strong interest in strategy, analytics, and data-driven decision-making.
