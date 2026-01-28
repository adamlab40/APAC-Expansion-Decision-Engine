"""Feature engineering pipeline: clean, transform, and standardize market data."""
from typing import Dict, List
from pathlib import Path
import pandas as pd
import numpy as np


def load_raw_data(data_dir: str = "data/raw") -> Dict[str, pd.DataFrame]:
    """
    Load all raw data files.
    
    Args:
        data_dir: Directory containing raw data
        
    Returns:
        Dictionary of DataFrames by source
    """
    data_path = Path(data_dir)
    data_dict = {}
    
    # This will be called after data download, so we look for processed raw files
    # or we can load from API results that were saved
    
    return data_dict


def combine_data_sources(
    wb_data: pd.DataFrame,
    wgi_data: pd.DataFrame,
    cpi_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine data from multiple sources into single DataFrame.
    
    Args:
        wb_data: World Bank indicators (long format with indicator column)
        wgi_data: WGI indicators (long format)
        cpi_data: CPI data with country_code and cpi_score
        
    Returns:
        Combined DataFrame with one row per country
    """
    # Pivot World Bank data
    wb_pivot = wb_data.pivot_table(
        index="country_code",
        columns="indicator",
        values="value",
        aggfunc="first"
    ).reset_index()
    
    # Rename columns
    wb_pivot.columns.name = None
    if "population" in wb_pivot.columns:
        wb_pivot = wb_pivot.rename(columns={"population": "population_total"})
    if "gdp_per_capita" in wb_pivot.columns:
        wb_pivot = wb_pivot.rename(columns={"gdp_per_capita": "gdp_per_capita_usd"})
    if "internet_users_pct" in wb_pivot.columns:
        wb_pivot = wb_pivot.rename(columns={"internet_users_pct": "internet_users_pct"})
    
    # Pivot WGI data
    wgi_pivot = wgi_data.pivot_table(
        index="country_code",
        columns="indicator",
        values="value",
        aggfunc="first"
    ).reset_index()
    wgi_pivot.columns.name = None
    
    # Merge all data
    df = wb_pivot.merge(wgi_pivot, on="country_code", how="outer")
    df = df.merge(cpi_data, on="country_code", how="outer")
    
    return df


def handle_missing_data(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    """
    Handle missing values in market data.
    
    Args:
        df: Input DataFrame
        strategy: Imputation strategy ('median', 'mean', 'forward_fill', 'drop')
        
    Returns:
        DataFrame with missing values handled
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if strategy == "median":
        for col in numeric_cols:
            if col != "country_code":
                df[col] = df[col].fillna(df[col].median())
    elif strategy == "mean":
        for col in numeric_cols:
            if col != "country_code":
                df[col] = df[col].fillna(df[col].mean())
    elif strategy == "forward_fill":
        df[numeric_cols] = df[numeric_cols].fillna(method="ffill")
    elif strategy == "drop":
        df = df.dropna(subset=numeric_cols)
    
    return df


def standardize_features(df: pd.DataFrame, method: str = "zscore") -> pd.DataFrame:
    """
    Standardize features using z-scores or min-max scaling.
    
    Args:
        df: Input DataFrame with features
        method: Standardization method ('zscore' or 'minmax')
        
    Returns:
        DataFrame with standardized features
    """
    df = df.copy()
    numeric_cols = [col for col in df.columns 
                    if col != "country_code" and pd.api.types.is_numeric_dtype(df[col])]
    
    if method == "zscore":
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df[f"{col}_standardized"] = (df[col] - mean) / std
            else:
                df[f"{col}_standardized"] = 0
    elif method == "minmax":
        for col in numeric_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                df[f"{col}_standardized"] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[f"{col}_standardized"] = 0
    
    return df


def build_feature_set(
    wb_data: pd.DataFrame,
    wgi_data: pd.DataFrame,
    cpi_data: pd.DataFrame,
    output_dir: str = "data/processed"
) -> pd.DataFrame:
    """
    Complete feature engineering pipeline.
    
    Args:
        wb_data: World Bank data
        wgi_data: WGI data
        cpi_data: CPI data
        output_dir: Directory to save processed data
        
    Returns:
        Feature-engineered DataFrame
    """
    # Combine sources
    df = combine_data_sources(wb_data, wgi_data, cpi_data)
    
    # Handle missing data
    df = handle_missing_data(df, strategy="median")
    
    # Create composite features
    # Market size score (log of population for better distribution)
    if "population_total" in df.columns:
        df["market_size_score"] = np.log1p(df["population_total"])  # log(1+x) handles zeros
    
    # Purchasing power = GDP per capita (already in dataset)
    if "gdp_per_capita_usd" in df.columns:
        df["purchasing_power_score"] = df["gdp_per_capita_usd"]
    
    # Digital readiness = internet users %
    if "internet_users_pct" in df.columns:
        df["digital_readiness_score"] = df["internet_users_pct"]
    
    # Governance risk = inverse of rule_of_law + regulatory_quality (lower is worse)
    if "rule_of_law" in df.columns and "regulatory_quality" in df.columns:
        # WGI ranges from -2.5 to +2.5, so we invert to make higher = better
        df["governance_risk_score"] = (df["rule_of_law"] + df["regulatory_quality"]) / 2
    elif "rule_of_law" in df.columns:
        df["governance_risk_score"] = df["rule_of_law"]
    elif "regulatory_quality" in df.columns:
        df["governance_risk_score"] = df["regulatory_quality"]
    
    # Corruption risk = CPI (higher is better, 0-100)
    if "cpi_score" in df.columns:
        df["corruption_risk_score"] = df["cpi_score"]
    
    # Standardize all feature scores
    feature_cols = [
        "market_size_score",
        "purchasing_power_score",
        "digital_readiness_score",
        "governance_risk_score",
        "corruption_risk_score"
    ]
    
    # Standardize each feature
    df = standardize_features(df, method="zscore")
    
    # Ensure all standardized features exist (fill with 0 if missing)
    for col in feature_cols:
        std_col = f"{col}_standardized"
        if std_col not in df.columns:
            df[std_col] = 0
    
    # Save processed data
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path / "market_features.csv", index=False)
    
    return df

