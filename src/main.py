"""Main orchestration script for APAC expansion decision engine."""
import sys
from pathlib import Path
import yaml
import pandas as pd
import pickle
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_sources.worldbank import WorldBankClient
from src.data_sources.wgi import WGIClient
from src.data_sources.owid import OWIDClient
from src.features.build_features import build_feature_set
from src.models.scoring import MarketScorer, run_full_sensitivity
from src.models.forecast import generate_scenarios, RevenueForecaster
from src.models.monte_carlo import MonteCarloSimulator
from src.reporting.make_slides import create_presentation


def load_config(config_path: str) -> Dict:
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    """Main pipeline execution."""
    print("=" * 60)
    print("APAC Expansion Decision Engine")
    print("=" * 60)
    
    # Load configurations
    print("\n[1/7] Loading configurations...")
    config_dir = Path("config")
    
    markets_config = load_config(config_dir / "markets.yml")
    weights_config = load_config(config_dir / "weights.yml")
    assumptions_config = load_config(config_dir / "assumptions.yml")
    
    markets = markets_config["markets"]
    weights = weights_config["weights"]
    
    print(f"  Markets: {', '.join(markets)}")
    print(f"  Criteria weights: {weights}")
    
    # Step 1: Download data
    print("\n[2/7] Downloading data from external sources...")
    
    print("  Fetching World Bank indicators...")
    wb_client = WorldBankClient(cache_dir="data/raw")
    wb_data = wb_client.fetch_all_indicators(markets, year=2022)
    print(f"    Retrieved {len(wb_data)} records")
    
    print("  Fetching WGI indicators...")
    wgi_client = WGIClient(cache_dir="data/raw")
    wgi_data = wgi_client.fetch_all_indicators(markets, year=2022)
    print(f"    Retrieved {len(wgi_data)} records")
    
    print("  Fetching CPI data...")
    owid_client = OWIDClient(cache_dir="data/raw")
    cpi_data = owid_client.fetch_cpi(
        dataset_name="ti-corruption-perception-index",
        country_codes=markets
    )
    print(f"    Retrieved {len(cpi_data)} records")
    
    # Step 2: Build features
    print("\n[3/7] Building features and standardizing data...")
    features_df = build_feature_set(wb_data, wgi_data, cpi_data)
    print(f"  Processed {len(features_df)} markets")
    print(f"  Features: {[col for col in features_df.columns if 'standardized' in col]}")
    
    # Step 3: Score markets
    print("\n[4/7] Scoring markets using MCDA...")
    scorer = MarketScorer(weights)
    scored_df = scorer.score_markets(features_df)
    
    # Save scoring results
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    scored_df.to_csv(outputs_dir / "market_scores.csv", index=False)
    print(f"  Top 3 markets: {', '.join(scored_df.head(3)['country_code'].tolist())}")
    
    # Step 4: Run sensitivity analysis
    print("\n[5/7] Running sensitivity analysis...")
    sensitivity_config = weights_config.get("sensitivity", {})
    sensitivity_results = run_full_sensitivity(
        features_df,
        weights,
        step=sensitivity_config.get("step", 0.05),
        n_runs=sensitivity_config.get("runs", 200)
    )
    print(f"  Completed sensitivity for {len(sensitivity_results)} criteria")
    
    # Step 5: Generate forecasts and Monte Carlo
    print("\n[6/7] Running revenue forecasts and Monte Carlo simulation...")
    
    # Get top market for detailed analysis
    top_market = scored_df.iloc[0]
    market_adjustment = (top_market["total_score"] + 3) / 6  # Rough normalization
    market_adjustment = max(0.5, min(1.5, market_adjustment))
    
    # Generate scenarios
    forecast_scenarios = generate_scenarios(
        assumptions_config,
        market_adjustment=market_adjustment,
        months=assumptions_config["simulation"]["months"]
    )
    
    # Run Monte Carlo for top market
    simulator = MonteCarloSimulator(assumptions_config)
    sim_results, sim_summary = simulator.simulate_revenue(
        months=assumptions_config["simulation"]["months"],
        n_sims=assumptions_config["simulation"]["n_sims"],
        market_adjustment=market_adjustment
    )
    
    # Calculate payback distribution
    entry_cost = assumptions_config["costs"]["market_entry_cost_usd"]
    payback_df, payback_stats = simulator.calculate_payback_distribution(
        sim_results,
        entry_cost=entry_cost
    )
    
    print(f"  Monte Carlo results:")
    print(f"    Mean payback: {payback_stats.get('mean', -1):.1f} months")
    print(f"    Never pays back: {payback_stats.get('never_pays_back_pct', 0):.1f}% of simulations")
    
    # Save simulation results
    sim_results.to_csv(outputs_dir / "monte_carlo_results.csv", index=False)
    sim_summary.to_csv(outputs_dir / "monte_carlo_summary.csv", index=False)
    payback_df.to_csv(outputs_dir / "payback_distribution.csv", index=False)
    
    # Step 6: Prepare dashboard data
    print("\n[7/7] Preparing outputs...")
    
    # Save data for dashboard
    dashboard_data = {
        "market_features": features_df,
        "market_scores": scored_df,
        "sensitivity": sensitivity_results,
        "forecasts": forecast_scenarios,
        "monte_carlo": {
            "results": sim_results,
            "summary": sim_summary,
            "payback_stats": payback_stats
        }
    }
    
    with open(outputs_dir / "dashboard_data.pkl", "wb") as f:
        pickle.dump(dashboard_data, f)
    
    # Step 7: Generate PowerPoint
    print("  Generating PowerPoint presentation...")
    create_presentation(
        market_scores=scored_df,
        sensitivity_results=sensitivity_results,
        forecast_scenarios=forecast_scenarios,
        monte_carlo_stats=payback_stats,
        assumptions=assumptions_config,
        output_path=str(outputs_dir / "apac_expansion_recommendations.pptx")
    )
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)
    print(f"\nOutputs saved to: {outputs_dir.absolute()}")
    print("\nNext steps:")
    print("  1. Review market_scores.csv for rankings")
    print("  2. Launch dashboard: streamlit run src/dashboards/app.py")
    print("  3. Open PowerPoint: outputs/apac_expansion_recommendations.pptx")


if __name__ == "__main__":
    main()

