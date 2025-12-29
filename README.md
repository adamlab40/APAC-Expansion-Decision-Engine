# APAC Expansion Decision Engine

## Problem Statement

A B2B SaaS company is evaluating expansion into 10 APAC markets and needs a data-driven framework to:
- Rank markets based on market size, purchasing power, digital readiness, governance quality, and corruption risk
- Simulate revenue scenarios and payback periods under uncertainty
- Generate actionable expansion recommendations with risk mitigation strategies

This decision engine integrates real-world economic and governance data to provide quantitative market prioritization and financial projections for strategic planning.

## Data Sources

### World Bank API V2 (Indicators)
- **Population (SP.POP.TOTL)**: Total population by country/year
  - Endpoint: `https://api.worldbank.org/v2/country/{country}/indicator/SP.POP.TOTL`
- **GDP per Capita (NY.GDP.PCAP.CD)**: GDP per capita in current USD
  - Endpoint: `https://api.worldbank.org/v2/country/{country}/indicator/NY.GDP.PCAP.CD`
- **Internet Users % (IT.NET.USER.ZS)**: Percentage of population using internet
  - Endpoint: `https://api.worldbank.org/v2/country/{country}/indicator/IT.NET.USER.ZS`

### Worldwide Governance Indicators (WGI)
- **Rule of Law (RL.EST)**: Rule of law estimate (-2.5 to +2.5)
- **Regulatory Quality (RQ.EST)**: Regulatory quality estimate (-2.5 to +2.5)
- Source: World Bank DataBank (downloaded as CSV with caching)

### Corruption Perceptions Index (CPI)
- **CPI Score**: Transparency International CPI score (0-100, higher = less corrupt)
- Source: Our World in Data via CSV endpoint: `ti-corruption-perception-index`

## Quickstart

### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Complete Pipeline

```bash
# Single command to download data, build features, score markets, run simulations, and generate outputs
python -m src.main
```

### Launch Dashboard

```bash
streamlit run src/dashboards/app.py
```

## Outputs

1. **Streamlit Dashboard** (`outputs/dashboard_data.pkl`):
   - Interactive market ranking table
   - Radar charts per market
   - Weight adjustment sliders
   - Scenario toggles
   - Sensitivity analysis plots

2. **PowerPoint Presentation** (`outputs/apac_expansion_recommendations.pptx`):
   - Executive summary and objectives
   - Data sources and methodology
   - Market ranking results
   - Sensitivity analysis
   - Recommended market sequencing
   - 12-month hiring and budget plan
   - Risk assessment and mitigations

3. **Processed Data** (`data/processed/`):
   - Cleaned and standardized market features
   - Scoring results
   - Simulation outputs

## Project Structure

```
.
├── config/           # YAML configuration files
├── data/
│   ├── raw/         # Cached API downloads
│   └── processed/   # Feature-engineered datasets
├── src/
│   ├── main.py      # Main orchestration script
│   ├── data_sources/ # API clients and data downloaders
│   ├── features/     # Feature engineering pipeline
│   ├── models/       # Scoring, forecasting, simulation
│   ├── dashboards/   # Streamlit app
│   └── reporting/    # PowerPoint generator
├── tests/            # Unit tests
└── outputs/          # Generated artifacts
```

## How to Talk About This on a Resume

- **Built end-to-end data pipeline**: Designed and implemented a production-grade Python application that automatically ingests real-time economic and governance data from World Bank API and Our World in Data, with intelligent caching to reduce API calls by 90%+

- **Developed multi-criteria decision analysis framework**: Created a weighted scoring model with sensitivity analysis to rank 10 APAC markets across 5 dimensions (market size, purchasing power, digital readiness, governance, corruption risk), enabling data-driven expansion prioritization

- **Delivered executive insights via automated reporting**: Built Monte Carlo simulation engine (3,000 iterations) for revenue forecasting under uncertainty and automated PowerPoint generation using python-pptx, reducing manual analysis time from days to minutes

