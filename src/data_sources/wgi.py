"""Worldwide Governance Indicators (WGI) downloader."""
import os
from typing import Dict, Optional
from pathlib import Path
import requests
import pandas as pd


class WGIClient:
    """Client for downloading WGI data from World Bank DataBank."""
    
    # WGI DataBank CSV export URL (this is a static export approach)
    # Alternative: Use World Bank API for individual indicators
    WGI_INDICATORS = {
        "rule_of_law": "RL.EST",
        "regulatory_quality": "RQ.EST"
    }
    
    # Direct CSV download from World Bank (alternative method)
    # Note: This uses a pre-exported CSV approach since direct API is complex
    WGI_CSV_URL = "https://databank.worldbank.org/data/download/WGI_csv.zip"
    
    def __init__(self, cache_dir: str = "data/raw"):
        """Initialize client with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "APAC-Expansion-Engine/1.0"})
    
    def _get_cache_path(self, indicator_code: str) -> Path:
        """Get cache file path for indicator."""
        return self.cache_dir / f"wgi_{indicator_code}.csv"
    
    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Load data from cache if available."""
        if cache_path.exists():
            try:
                return pd.read_csv(cache_path)
            except Exception:
                return None
        return None
    
    def _save_to_cache(self, cache_path: Path, df: pd.DataFrame) -> None:
        """Save data to cache."""
        df.to_csv(cache_path, index=False)
    
    def _fetch_indicator_api(
        self, 
        country_code: str, 
        indicator_code: str,
        year: int = 2022
    ) -> Optional[float]:
        """
        Fetch WGI indicator via World Bank API (fallback method).
        
        Args:
            country_code: ISO3 country code
            indicator_code: WGI indicator code (e.g., RL.EST)
            year: Target year
            
        Returns:
            Indicator value or None
        """
        # World Bank API endpoint for WGI
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
        params = {
            "format": "json",
            "date": f"{year-5}:{year}",
            "per_page": 1000
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2 or not data[1]:
                return None
            
            # Get most recent non-null value
            for item in sorted(data[1], key=lambda x: x.get("date", ""), reverse=True):
                value = item.get("value")
                if value is not None:
                    return float(value)
            
            return None
            
        except Exception as e:
            print(f"Error fetching WGI {indicator_code} for {country_code}: {e}")
            return None
    
    def fetch_all_indicators(
        self, 
        country_codes: list,
        year: int = 2022,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch WGI indicators for multiple countries.
        
        Args:
            country_codes: List of ISO3 country codes
            year: Target year
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with WGI data
        """
        results = []
        
        for country in country_codes:
            for indicator_name, indicator_code in self.WGI_INDICATORS.items():
                cache_path = self._get_cache_path(f"{country}_{indicator_code}")
                
                value = None
                if use_cache:
                    cached = self._load_from_cache(cache_path)
                    if cached is not None and not cached.empty:
                        if "value" in cached.columns:
                            value = cached["value"].iloc[0]
                        else:
                            value = cached.iloc[0, -1]  # Last column
                
                if value is None:
                    value = self._fetch_indicator_api(country, indicator_code, year)
                    if value is not None:
                        # Cache the result
                        cache_df = pd.DataFrame({"country_code": [country], "value": [value]})
                        self._save_to_cache(cache_path, cache_df)
                
                results.append({
                    "country_code": country,
                    "indicator": indicator_name,
                    "value": value,
                    "year": year
                })
        
        df = pd.DataFrame(results)
        return df


if __name__ == "__main__":
    # Test client
    client = WGIClient()
    test_countries = ["AUS", "SGP", "JPN"]
    df = client.fetch_all_indicators(test_countries)
    print(df)

