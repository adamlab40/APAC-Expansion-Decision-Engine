# Quick Start Guide

## Installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

```bash
# Run complete pipeline (downloads data, processes, scores, simulates, generates outputs)
python -m src.main
```

This will:
1. Download data from World Bank API, WGI, and OWID
2. Build and standardize features
3. Score all markets using MCDA
4. Run sensitivity analysis
5. Generate revenue forecasts and Monte Carlo simulations
6. Create PowerPoint presentation
7. Save all outputs to `outputs/` directory

## Launching the Dashboard

```bash
streamlit run src/dashboards/app.py
```

The dashboard provides:
- Interactive market ranking with adjustable weights
- Radar charts for each market
- Revenue forecasting with scenario toggles
- Sensitivity analysis visualizations

## Outputs

After running the pipeline, check the `outputs/` directory:

- `market_scores.csv` - Market rankings and scores
- `monte_carlo_results.csv` - Full simulation results
- `monte_carlo_summary.csv` - Summary statistics
- `payback_distribution.csv` - Payback period distribution
- `dashboard_data.pkl` - Pickled data for dashboard
- `apac_expansion_recommendations.pptx` - Executive presentation

## Running Tests

```bash
pytest tests/
```

## Configuration

Edit configuration files in `config/`:

- `markets.yml` - List of markets to analyze
- `weights.yml` - Criteria weights and sensitivity settings
- `assumptions.yml` - Business assumptions (ACV, funnel, costs, etc.)

## Troubleshooting

**Issue**: API rate limiting or connection errors
- **Solution**: Data is cached in `data/raw/`. Delete cache files to force re-download.

**Issue**: Missing CPI data for some countries
- **Solution**: The system uses median imputation. Check `data/processed/market_features.csv` for imputed values.

**Issue**: Dashboard shows "Processed data not found"
- **Solution**: Run `python -m src.main` first to generate processed data.

## Data Sources

- **World Bank API V2**: Population, GDP per capita, Internet users %
- **Worldwide Governance Indicators (WGI)**: Rule of Law, Regulatory Quality
- **Our World in Data**: Corruption Perceptions Index

All data is automatically downloaded and cached locally.

