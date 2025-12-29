"""Multi-criteria decision analysis (MCDA) scoring and sensitivity analysis."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from pathlib import Path


class MarketScorer:
    """MCDA scoring engine for market ranking."""
    
    def __init__(self, weights: Dict[str, float]):
        """
        Initialize scorer with criteria weights.
        
        Args:
            weights: Dictionary of feature_name -> weight (should sum to 1.0)
        """
        self.weights = weights
        self._validate_weights()
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            print(f"Warning: Weights sum to {total:.3f}, not 1.0")
    
    def score_markets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score markets using weighted sum of standardized features.
        
        Args:
            df: DataFrame with standardized features
            
        Returns:
            DataFrame with scores and rankings
        """
        df = df.copy()
        
        # Map feature names to standardized columns
        feature_mapping = {
            "market_size": "market_size_score_standardized",
            "purchasing_power": "purchasing_power_score_standardized",
            "digital_readiness": "digital_readiness_score_standardized",
            "governance_risk": "governance_risk_score_standardized",
            "corruption_risk": "corruption_risk_score_standardized",
        }
        
        # Calculate weighted score
        df["total_score"] = 0.0
        
        for weight_name, weight_value in self.weights.items():
            feature_col = feature_mapping.get(weight_name)
            if feature_col and feature_col in df.columns:
                df["total_score"] += weight_value * df[feature_col]
            else:
                print(f"Warning: Feature column {feature_col} not found for weight {weight_name}")
        
        # Add component scores for visualization
        for weight_name, weight_value in self.weights.items():
            feature_col = feature_mapping.get(weight_name)
            if feature_col and feature_col in df.columns:
                df[f"score_{weight_name}"] = weight_value * df[feature_col]
        
        # Rank markets
        df["rank"] = df["total_score"].rank(ascending=False, method="min").astype(int)
        df = df.sort_values("rank")
        
        return df
    
    def sensitivity_analysis(
        self,
        df: pd.DataFrame,
        weight_name: str,
        step: float = 0.05,
        n_runs: int = 200
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on a single weight.
        
        Args:
            df: DataFrame with standardized features
            weight_name: Name of weight to vary
            step: Step size for weight variation
            n_runs: Number of simulation runs
            
        Returns:
            DataFrame with sensitivity results
        """
        if weight_name not in self.weights:
            raise ValueError(f"Weight {weight_name} not found")
        
        results = []
        original_weight = self.weights[weight_name]
        other_weights_sum = sum(v for k, v in self.weights.items() if k != weight_name)
        
        # Generate weight variations
        min_weight = max(0.0, original_weight - (step * n_runs // 2))
        max_weight = min(1.0, original_weight + (step * n_runs // 2))
        weight_values = np.linspace(min_weight, max_weight, n_runs)
        
        for test_weight in weight_values:
            # Normalize other weights proportionally
            test_weights = self.weights.copy()
            test_weights[weight_name] = test_weight
            
            remaining = 1.0 - test_weight
            if other_weights_sum > 0:
                scale = remaining / other_weights_sum
                for k in test_weights:
                    if k != weight_name:
                        test_weights[k] *= scale
            
            # Score with test weights
            scorer = MarketScorer(test_weights)
            scored = scorer.score_markets(df)
            
            # Record rank changes for top 3 markets
            top_markets = scored.head(3)[["country_code", "rank"]].copy()
            for _, row in top_markets.iterrows():
                results.append({
                    "weight_name": weight_name,
                    "weight_value": test_weight,
                    "country_code": row["country_code"],
                    "rank": row["rank"],
                    "total_score": scored[scored["country_code"] == row["country_code"]]["total_score"].iloc[0]
                })
        
        return pd.DataFrame(results)


def run_full_sensitivity(
    df: pd.DataFrame,
    weights: Dict[str, float],
    step: float = 0.05,
    n_runs: int = 200
) -> Dict[str, pd.DataFrame]:
    """
    Run sensitivity analysis for all weights.
    
    Args:
        df: DataFrame with standardized features
        weights: Base weights dictionary
        step: Step size for weight variation
        n_runs: Number of simulation runs per weight
        
    Returns:
        Dictionary of sensitivity results by weight name
    """
    scorer = MarketScorer(weights)
    results = {}
    
    for weight_name in weights.keys():
        sens_df = scorer.sensitivity_analysis(df, weight_name, step, n_runs)
        results[weight_name] = sens_df
    
    return results

