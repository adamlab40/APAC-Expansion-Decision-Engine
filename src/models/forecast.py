"""Revenue forecasting and scenario modeling."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


class RevenueForecaster:
    """Forecasts revenue based on market assumptions and funnel metrics."""
    
    def __init__(self, assumptions: Dict):
        """
        Initialize forecaster with business assumptions.
        
        Args:
            assumptions: Dictionary with funnel, retention, and cost assumptions
        """
        self.assumptions = assumptions
        self.funnel = assumptions.get("funnel", {})
        self.retention = assumptions.get("retention", {})
        self.commercial = assumptions.get("commercial_assumptions", {})
        self.costs = assumptions.get("costs", {})
    
    def forecast_revenue(
        self,
        months: int = 12,
        market_adjustment: float = 1.0,
        scenario: str = "base"
    ) -> pd.DataFrame:
        """
        Forecast monthly revenue based on funnel assumptions.
        
        Args:
            months: Number of months to forecast
            market_adjustment: Multiplier for market size/readiness (0-2.0)
            scenario: Scenario type ('base', 'optimistic', 'pessimistic')
        
        Returns:
            DataFrame with monthly forecasts
        """
        # Get base assumptions
        leads_per_month = self.funnel.get("leads_per_month_initial", 120)
        lead_to_opp = self.funnel.get("lead_to_opportunity", 0.18)
        opp_to_win = self.funnel.get("opportunity_to_win", 0.22)
        sales_cycle = self.funnel.get("sales_cycle_months", 2)
        acv = self.commercial.get("acv_usd", 18000)
        monthly_churn = self.retention.get("monthly_churn", 0.018)
        
        # Apply scenario adjustments
        if scenario == "optimistic":
            lead_to_opp *= 1.2
            opp_to_win *= 1.2
            monthly_churn *= 0.8
            market_adjustment *= 1.15
        elif scenario == "pessimistic":
            lead_to_opp *= 0.8
            opp_to_win *= 0.8
            monthly_churn *= 1.2
            market_adjustment *= 0.85
        
        # Apply market adjustment
        leads_per_month = int(leads_per_month * market_adjustment)
        
        # Initialize tracking
        results = []
        active_customers = 0
        total_acquisition_cost = 0
        
        for month in range(1, months + 1):
            # New leads
            new_leads = leads_per_month
            
            # Convert to opportunities (with sales cycle lag)
            if month >= sales_cycle:
                opps_from_month = new_leads * lead_to_opp
            else:
                opps_from_month = 0
            
            # Convert to wins
            if month >= sales_cycle:
                new_wins = int(opps_from_month * opp_to_win)
            else:
                new_wins = 0
            
            # Apply churn to existing customers
            churned = int(active_customers * monthly_churn)
            active_customers = max(0, active_customers - churned + new_wins)
            
            # Calculate revenue
            monthly_revenue = active_customers * (acv / 12)  # Monthly ACV
            
            # Track costs
            cac = self.costs.get("cac_usd_per_customer", 14000)
            acquisition_cost = new_wins * cac
            total_acquisition_cost += acquisition_cost
            
            # Net revenue (after gross margin)
            gross_margin = self.commercial.get("gross_margin", 0.82)
            gross_revenue = monthly_revenue * gross_margin
            
            results.append({
                "month": month,
                "new_leads": new_leads,
                "new_opportunities": int(opps_from_month) if month >= sales_cycle else 0,
                "new_wins": new_wins,
                "churned": churned,
                "active_customers": active_customers,
                "monthly_revenue": monthly_revenue,
                "gross_revenue": gross_revenue,
                "acquisition_cost": acquisition_cost,
                "cumulative_acquisition_cost": total_acquisition_cost,
                "net_revenue": gross_revenue - acquisition_cost,
                "cumulative_net_revenue": sum(r["net_revenue"] for r in results) + (gross_revenue - acquisition_cost)
            })
        
        df = pd.DataFrame(results)
        return df
    
    def calculate_payback_period(
        self,
        forecast_df: pd.DataFrame,
        entry_cost: float = 120000
    ) -> float:
        """
        Calculate payback period in months.
        
        Args:
            forecast_df: Revenue forecast DataFrame
            entry_cost: Initial market entry cost
            
        Returns:
            Payback period in months (or -1 if never pays back)
        """
        cumulative_net = forecast_df["cumulative_net_revenue"].values
        
        # Find first month where cumulative net revenue exceeds entry cost
        payback_mask = cumulative_net >= entry_cost
        if payback_mask.any():
            payback_month = forecast_df[payback_mask]["month"].iloc[0]
            return float(payback_month)
        
        return -1.0  # Never pays back


def generate_scenarios(
    assumptions: Dict,
    market_adjustment: float = 1.0,
    months: int = 12
) -> Dict[str, pd.DataFrame]:
    """
    Generate forecasts for multiple scenarios.
    
    Args:
        assumptions: Business assumptions
        market_adjustment: Market size adjustment factor
        months: Forecast horizon
        
    Returns:
        Dictionary of scenario forecasts
    """
    forecaster = RevenueForecaster(assumptions)
    
    scenarios = {}
    for scenario in ["base", "optimistic", "pessimistic"]:
        forecast = forecaster.forecast_revenue(
            months=months,
            market_adjustment=market_adjustment,
            scenario=scenario
        )
        scenarios[scenario] = forecast
    
    return scenarios

