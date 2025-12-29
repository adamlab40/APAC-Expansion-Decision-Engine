"""Tests for feature engineering."""
import pytest
import pandas as pd
import numpy as np
from src.features.build_features import (
    combine_data_sources,
    handle_missing_data,
    standardize_features
)


def test_combine_data_sources():
    """Test combining data from multiple sources."""
    wb_data = pd.DataFrame({
        "country_code": ["AUS", "SGP"],
        "indicator": ["population", "population"],
        "value": [25000000, 5500000]
    })
    
    wgi_data = pd.DataFrame({
        "country_code": ["AUS", "SGP"],
        "indicator": ["rule_of_law", "rule_of_law"],
        "value": [1.5, 1.8]
    })
    
    cpi_data = pd.DataFrame({
        "country_code": ["AUS", "SGP"],
        "cpi_score": [75, 83]
    })
    
    combined = combine_data_sources(wb_data, wgi_data, cpi_data)
    
    assert len(combined) == 2
    assert "population" in combined.columns or "population_total" in combined.columns
    assert "rule_of_law" in combined.columns
    assert "cpi_score" in combined.columns


def test_handle_missing_data():
    """Test missing data imputation."""
    df = pd.DataFrame({
        "country_code": ["AUS", "SGP", "JPN"],
        "value1": [1.0, np.nan, 3.0],
        "value2": [2.0, 4.0, np.nan]
    })
    
    # Test median imputation
    filled = handle_missing_data(df, strategy="median")
    
    assert not filled["value1"].isna().any()
    assert not filled["value2"].isna().any()
    assert filled["value1"].iloc[1] == 2.0  # Median of [1.0, 3.0]


def test_standardize_features():
    """Test feature standardization."""
    df = pd.DataFrame({
        "country_code": ["AUS", "SGP", "JPN"],
        "value": [10.0, 20.0, 30.0]
    })
    
    standardized = standardize_features(df, method="zscore")
    
    assert "value_standardized" in standardized.columns
    # Mean should be ~0, std should be ~1
    assert abs(standardized["value_standardized"].mean()) < 0.01
    assert abs(standardized["value_standardized"].std() - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])

