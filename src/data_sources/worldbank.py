"""World Bank API V2 client for downloading economic indicators."""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import requests
import pandas as pd


class WorldBankClient:
    """Client for downloading World Bank indicators via API V2."""
    
    BASE_URL = "https://api.worldbank.org/v2/country"
    INDICATORS = {
        "population": "SP.POP.TOTL",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "internet_users_pct": "IT.NET.USER.ZS",
    }
    
    def __init__(self, cache_dir: str = "data/raw"):
        """Initialize client with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "APAC-Expansion-Engine/1.0"})
    
    def _get_cache_path(self, country_code: str, indicator_code: str) -> Path:
        """Get cache file path for indicator."""
        return self.cache_dir / f"wb_{country_code}_{indicator_code}.json"
    
    def _load_from_cache(self, cache_path: Path) -> Optional[Dict]:
        """Load data from cache if available."""
        if cache_path.exists():
            with open(cache_path, "r") as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, cache_path: Path, data: Dict) -> None:
        """Save data to cache."""
        with open(cache_path, "w") as f:
            json.dump(data, f)
    
    def _fetch_indicator(
        self, 
        country_code: str, 
        indicator_code: str, 
        year: int = 2022,
        use_cache: bool = True
    ) -> Optional[float]:
        """
        Fetch latest available indicator value for country.
        
        Args:
            country_code: ISO3 country code (e.g., 'AUS')
            indicator_code: World Bank indicator code
            year: Target year (default 2022)
            use_cache: Whether to use cached data
            
        Returns:
            Latest available value or None if not found
        """
        cache_path = self._get_cache_path(country_code, indicator_code)
        
        if use_cache:
            cached = self._load_from_cache(cache_path)
            if cached and "value" in cached:
                return cached["value"]
        
        url = f"{self.BASE_URL}/{country_code}/indicator/{indicator_code}"
        params = {
            "format": "json",
            "date": f"{year-5}:{year}",  # Get last 5 years
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
                    self._save_to_cache(cache_path, {"value": value, "year": item.get("date")})
                    return float(value)
            
            return None
            
        except Exception as e:
            print(f"Error fetching {indicator_code} for {country_code}: {e}")
            return None
    
    def fetch_all_indicators(
        self, 
        country_codes: List[str], 
        year: int = 2022
    ) -> pd.DataFrame:
        """
        Fetch all indicators for multiple countries.
        
        Args:
            country_codes: List of ISO3 country codes
            year: Target year
            
        Returns:
            DataFrame with country, indicator, and value columns
        """
        results = []
        
        for country in country_codes:
            for indicator_name, indicator_code in self.INDICATORS.items():
                value = self._fetch_indicator(country, indicator_code, year)
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
    client = WorldBankClient()
    test_countries = ["AUS", "SGP", "JPN"]
    df = client.fetch_all_indicators(test_countries)
    print(df)

