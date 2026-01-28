"""Tests for revenue forecasting."""
import pytest
from src.models.forecast import RevenueForecaster


def test_revenue_forecaster():
    """Test revenue forecasting."""
    assumptions = {
        "funnel": {
            "leads_per_month_initial": 100,
            "lead_to_opportunity": 0.2,
            "opportunity_to_win": 0.25,
            "sales_cycle_months": 2
        },
        "retention": {
            "monthly_churn": 0.02
        },
        "commercial_assumptions": {
            "acv_usd": 20000,
            "gross_margin": 0.8
        },
        "costs": {
            "cac_usd_per_customer": 15000
        }
    }
    
    forecaster = RevenueForecaster(assumptions)
    forecast = forecaster.forecast_revenue(months=12)
    
    assert len(forecast) == 12
    assert "month" in forecast.columns
    assert "active_customers" in forecast.columns
    assert "monthly_revenue" in forecast.columns
    assert forecast["month"].min() == 1
    assert forecast["month"].max() == 12


def test_payback_period():
    """Test payback period calculation."""
    assumptions = {
        "funnel": {
            "leads_per_month_initial": 100,
            "lead_to_opportunity": 0.2,
            "opportunity_to_win": 0.25,
            "sales_cycle_months": 2
        },
        "retention": {
            "monthly_churn": 0.02
        },
        "commercial_assumptions": {
            "acv_usd": 20000,
            "gross_margin": 0.8
        },
        "costs": {
            "cac_usd_per_customer": 15000
        }
    }
    
    forecaster = RevenueForecaster(assumptions)
    forecast = forecaster.forecast_revenue(months=12)
    
    payback = forecaster.calculate_payback_period(forecast, entry_cost=100000)
    
    # Payback should be a number (or -1 if never pays back)
    assert isinstance(payback, (int, float))
    assert payback == -1 or (payback >= 1 and payback <= 12)


if __name__ == "__main__":
    pytest.main([__file__])

