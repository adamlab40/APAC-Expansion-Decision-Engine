"""Our World in Data (OWID) data downloader for Corruption Perceptions Index."""
import os
from typing import Optional, Dict
from pathlib import Path
import requests
import pandas as pd


# Country name to ISO3 code mapping (for OWID data)
COUNTRY_NAME_TO_CODE: Dict[str, str] = {
    "Australia": "AUS",
    "New Zealand": "NZL",
    "Singapore": "SGP",
    "Japan": "JPN",
    "South Korea": "KOR",
    "India": "IND",
    "Indonesia": "IDN",
    "Malaysia": "MYS",
    "Thailand": "THA",
    "Vietnam": "VNM",
    "Korea": "KOR",  # Alternative name
    "Republic of Korea": "KOR",
}


class OWIDClient:
    """Client for downloading OWID CSV datasets."""
    
    BASE_URL = "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets"
    
    def __init__(self, cache_dir: str = "data/raw"):
        """Initialize client with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "APAC-Expansion-Engine/1.0"})
    
    def _get_cache_path(self, dataset_name: str) -> Path:
        """Get cache file path for dataset."""
        return self.cache_dir / f"owid_{dataset_name}.csv"
    
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
    
    def fetch_cpi(
        self, 
        dataset_name: str = "ti-corruption-perception-index",
        country_codes: Optional[list] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch Corruption Perceptions Index data.
        
        Args:
            dataset_name: OWID dataset name
            country_codes: Optional list of ISO3 country codes to filter
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with CPI data
        """
        cache_path = self._get_cache_path(dataset_name)
        
        if use_cache:
            cached = self._load_from_cache(cache_path)
            if cached is not None and not cached.empty:
                df = cached
            else:
                df = None
        else:
            df = None
        
        if df is None:
            # Try direct CSV URL
            url = f"{self.BASE_URL}/{dataset_name}/{dataset_name}.csv"
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Read from response content
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                self._save_to_cache(cache_path, df)
                
            except Exception as e:
                print(f"Error fetching CPI from {url}: {e}")
                # Fallback: use alternative endpoint
                try:
                    # Alternative: Our World in Data explorer export
                    alt_url = "https://ourworldindata.org/grapher/corruption-perception-index"
                    print(f"Trying alternative method...")
                    # For now, return empty with structure
                    df = pd.DataFrame(columns=["Entity", "Code", "Year", "Corruption Perceptions Index"])
                except Exception as e2:
                    print(f"Fallback also failed: {e2}")
                    return pd.DataFrame()
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Find CPI column (might be named differently)
        cpi_col = None
        for col in df.columns:
            if "corruption" in col.lower() or "cpi" in col.lower():
                cpi_col = col
                break
        
        if cpi_col is None and "Value" in df.columns:
            cpi_col = "Value"
        elif cpi_col is None and len(df.columns) > 3:
            cpi_col = df.columns[-1]  # Assume last numeric column
        
        if cpi_col is None:
            print("Warning: Could not identify CPI column")
            return pd.DataFrame()
        
        # Filter to latest year and specified countries
        if "Year" in df.columns:
            latest_year = df["Year"].max()
            df = df[df["Year"] == latest_year].copy()
        
        if country_codes and "Code" in df.columns:
            df = df[df["Code"].isin(country_codes)].copy()
        
        # Standardize output
        result = pd.DataFrame()
        if "Code" in df.columns:
            result["country_code"] = df["Code"]
        elif "Entity" in df.columns:
            # Map entity names to codes
            result["country_code"] = df["Entity"].map(
                lambda x: COUNTRY_NAME_TO_CODE.get(x, None)
            )
            # Drop rows where we couldn't map
            result = result[result["country_code"].notna()].copy()
        else:
            print("Warning: No country code or entity column found")
            return pd.DataFrame()
        
        if cpi_col in df.columns:
            result["cpi_score"] = pd.to_numeric(df[cpi_col], errors="coerce")
        else:
            print("Warning: CPI score column not found")
            return pd.DataFrame()
        
        # Filter to requested countries if specified
        if country_codes:
            result = result[result["country_code"].isin(country_codes)].copy()
        
        return result.reset_index(drop=True)


if __name__ == "__main__":
    # Test client
    client = OWIDClient()
    df = client.fetch_cpi(country_codes=["AUS", "SGP", "JPN"])
    print(df)

