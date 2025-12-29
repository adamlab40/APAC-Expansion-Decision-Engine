"""Tests for market scoring module."""
import pytest
import pandas as pd
import numpy as np
from src.models.scoring import MarketScorer


def test_market_scorer_initialization():
    """Test MarketScorer initialization."""
    weights = {
        "market_size": 0.3,
        "purchasing_power": 0.2,
        "digital_readiness": 0.2,
        "governance_risk": 0.15,
        "corruption_risk": 0.15
    }
    scorer = MarketScorer(weights)
    assert scorer.weights == weights


def test_market_scoring():
    """Test market scoring functionality."""
    weights = {
        "market_size": 0.5,
        "purchasing_power": 0.5,
        "digital_readiness": 0.0,
        "governance_risk": 0.0,
        "corruption_risk": 0.0
    }
    
    # Create test data
    test_data = pd.DataFrame({
        "country_code": ["AUS", "SGP"],
        "market_size_score_standardized": [1.0, 0.5],
        "purchasing_power_score_standardized": [0.8, 1.0],
        "digital_readiness_score_standardized": [0.5, 0.5],
        "governance_risk_score_standardized": [0.5, 0.5],
        "corruption_risk_score_standardized": [0.5, 0.5]
    })
    
    scorer = MarketScorer(weights)
    scored = scorer.score_markets(test_data)
    
    assert len(scored) == 2
    assert "total_score" in scored.columns
    assert "rank" in scored.columns
    assert scored.iloc[0]["rank"] == 1
    assert scored.iloc[1]["rank"] == 2


def test_scoring_with_missing_features():
    """Test scoring handles missing features gracefully."""
    weights = {
        "market_size": 1.0,
        "purchasing_power": 0.0,
        "digital_readiness": 0.0,
        "governance_risk": 0.0,
        "corruption_risk": 0.0
    }
    
    test_data = pd.DataFrame({
        "country_code": ["AUS"],
        "market_size_score_standardized": [1.0]
        # Missing other features
    })
    
    scorer = MarketScorer(weights)
    scored = scorer.score_markets(test_data)
    
    assert len(scored) == 1
    assert scored.iloc[0]["total_score"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__])

