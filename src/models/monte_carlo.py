"""Monte Carlo simulation for revenue forecasting under uncertainty."""
from typing import Dict, Tuple
import pandas as pd
import numpy as np


class MonteCarloSimulator:
    """Monte Carlo simulation engine for revenue and payback uncertainty."""
    
    def __init__(self, assumptions: Dict):
        """
        Initialize simulator with base assumptions.
        
        Args:
            assumptions: Business assumptions including uncertainty parameters
        """
        self.assumptions = assumptions
        self.simulation_config = assumptions.get("simulation", {})
        self.uncertainty = self.simulation_config.get("uncertainty", {})
    
    def simulate_revenue(
        self,
        months: int = 12,
        n_sims: int = 3000,
        market_adjustment: float = 1.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run Monte Carlo simulation for revenue forecasting.
        
        Args:
            months: Forecast horizon in months
            n_sims: Number of simulation runs
            market_adjustment: Market size adjustment factor
            
        Returns:
            Tuple of (simulation_results_df, summary_statistics_df)
        """
        # Base assumptions
        funnel = self.assumptions.get("funnel", {})
        retention = self.assumptions.get("retention", {})
        commercial = self.assumptions.get("commercial_assumptions", {})
        costs = self.assumptions.get("costs", {})
        
        # Base values
        base_leads = funnel.get("leads_per_month_initial", 120) * market_adjustment
        base_lead_to_opp = funnel.get("lead_to_opportunity", 0.18)
        base_opp_to_win = funnel.get("opportunity_to_win", 0.22)
        base_churn = retention.get("monthly_churn", 0.018)
        base_cac = costs.get("cac_usd_per_customer", 14000)
        acv = commercial.get("acv_usd", 18000)
        gross_margin = commercial.get("gross_margin", 0.82)
        sales_cycle = funnel.get("sales_cycle_months", 2)
        
        # Uncertainty parameters
        lead_to_opp_sd = self.uncertainty.get("lead_to_opportunity_sd", 0.04)
        opp_to_win_sd = self.uncertainty.get("opportunity_to_win_sd", 0.05)
        churn_sd = self.uncertainty.get("churn_sd", 0.006)
        cac_sd = self.uncertainty.get("cac_sd", 2500)
        
        # Storage for results
        all_results = []
        
        np.random.seed(42)  # Reproducibility
        
        for sim in range(n_sims):
            # Sample from distributions
            lead_to_opp = np.clip(
                np.random.normal(base_lead_to_opp, lead_to_opp_sd),
                0.05, 0.50
            )
            opp_to_win = np.clip(
                np.random.normal(base_opp_to_win, opp_to_win_sd),
                0.05, 0.50
            )
            churn_rate = np.clip(
                np.random.normal(base_churn, churn_sd),
                0.005, 0.05
            )
            cac = np.clip(
                np.random.normal(base_cac, cac_sd),
                8000, 25000
            )
            
            # Run forecast for this simulation
            active_customers = 0
            total_revenue = 0
            total_cost = 0
            
            monthly_results = []
            
            for month in range(1, months + 1):
                # Generate leads (add some noise)
                leads = int(np.random.poisson(base_leads))
                
                # Convert to opportunities (with lag)
                if month >= sales_cycle:
                    opps = int(leads * lead_to_opp)
                else:
                    opps = 0
                
                # Convert to wins
                if month >= sales_cycle:
                    wins = int(np.random.binomial(opps, opp_to_win))
                else:
                    wins = 0
                
                # Apply churn
                churned = int(np.random.binomial(active_customers, churn_rate))
                active_customers = max(0, active_customers - churned + wins)
                
                # Calculate revenue
                monthly_revenue = active_customers * (acv / 12)
                total_revenue += monthly_revenue
                
                # Calculate costs
                acquisition_cost = wins * cac
                total_cost += acquisition_cost
                
                monthly_results.append({
                    "simulation": sim,
                    "month": month,
                    "active_customers": active_customers,
                    "monthly_revenue": monthly_revenue,
                    "cumulative_revenue": total_revenue * gross_margin,
                    "cumulative_cost": total_cost,
                    "net_revenue": (total_revenue * gross_margin) - total_cost
                })
            
            all_results.extend(monthly_results)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(all_results)
        
        # Calculate summary statistics by month
        summary_cols = ["monthly_revenue", "cumulative_revenue", "cumulative_cost", "net_revenue", "active_customers"]
        summary_stats = results_df.groupby("month")[summary_cols].agg([
            "mean", "std", "median",
            lambda x: np.percentile(x, 10),  # P10
            lambda x: np.percentile(x, 90)   # P90
        ]).round(2)
        
        # Flatten column names
        summary_stats.columns = ["_".join(col).strip() for col in summary_stats.columns.values]
        summary_stats = summary_stats.reset_index()
        
        return results_df, summary_stats
    
    def calculate_payback_distribution(
        self,
        simulation_results: pd.DataFrame,
        entry_cost: float = 120000
    ) -> pd.DataFrame:
        """
        Calculate payback period distribution across simulations.
        
        Args:
            simulation_results: Full simulation results DataFrame
            entry_cost: Market entry cost
            
        Returns:
            DataFrame with payback statistics per simulation
        """
        payback_periods = []
        
        for sim_id in simulation_results["simulation"].unique():
            sim_data = simulation_results[simulation_results["simulation"] == sim_id].copy()
            sim_data = sim_data.sort_values("month")
            
            # Find first month where net_revenue >= entry_cost
            payback_mask = sim_data["net_revenue"] >= entry_cost
            if payback_mask.any():
                payback_month = sim_data[payback_mask]["month"].iloc[0]
                payback_periods.append(payback_month)
            else:
                payback_periods.append(-1)  # Never pays back
        
        payback_df = pd.DataFrame({
            "simulation": range(len(payback_periods)),
            "payback_period_months": payback_periods
        })
        
        # Calculate statistics
        valid_paybacks = [p for p in payback_periods if p > 0]
        
        if valid_paybacks:
            stats_dict = {
                "mean": np.mean(valid_paybacks),
                "median": np.median(valid_paybacks),
                "std": np.std(valid_paybacks),
                "p10": np.percentile(valid_paybacks, 10),
                "p90": np.percentile(valid_paybacks, 90),
                "never_pays_back_pct": (len(payback_periods) - len(valid_paybacks)) / len(payback_periods) * 100
            }
        else:
            stats_dict = {
                "mean": -1,
                "median": -1,
                "std": 0,
                "p10": -1,
                "p90": -1,
                "never_pays_back_pct": 100.0
            }
        
        return payback_df, stats_dict

