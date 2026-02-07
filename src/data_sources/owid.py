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

# Fallback CPI values (2023 data) if download fails
FALLBACK_CPI: Dict[str, float] = {
    "AUS": 75.0,  # Australia
    "NZL": 85.0,  # New Zealand
    "SGP": 83.0,  # Singapore
    "JPN": 73.0,  # Japan
    "KOR": 63.0,  # South Korea
    "IND": 39.0,  # India
    "IDN": 34.0,  # Indonesia
    "MYS": 50.0,  # Malaysia
    "THA": 36.0,  # Thailand
    "VNM": 42.0,  # Vietnam
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
            # Try OWID grapher CSV export (more reliable endpoint)
            url = "https://ourworldindata.org/grapher/corruption-perception-index.csv"
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Read from response content
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                self._save_to_cache(cache_path, df)
                
            except Exception as e:
                print(f"Error fetching CPI from grapher CSV: {e}")
                # Fallback: try GitHub raw URL
                try:
                    alt_url = f"{self.BASE_URL}/{dataset_name}/{dataset_name}.csv"
                    print(f"Trying GitHub raw URL: {alt_url}")
                    response = self.session.get(alt_url, timeout=30)
                    response.raise_for_status()
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    self._save_to_cache(cache_path, df)
                except Exception as e2:
                    print(f"Fallback also failed: {e2}")
                    print("Using fallback CPI values from known data")
                    # Use fallback CPI values
                    if country_codes:
                        fallback_data = {
                            "country_code": [],
                            "cpi_score": []
                        }
                        for code in country_codes:
                            if code in FALLBACK_CPI:
                                fallback_data["country_code"].append(code)
                                fallback_data["cpi_score"].append(FALLBACK_CPI[code])
                        return pd.DataFrame(fallback_data)
                    else:
                        # Return all fallback values
                        return pd.DataFrame({
                            "country_code": list(FALLBACK_CPI.keys()),
                            "cpi_score": list(FALLBACK_CPI.values())
                        })
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Find CPI column (might be named differently)
        cpi_col = None
        for col in df.columns:
            col_lower = col.lower()
            if ("corruption" in col_lower or "cpi" in col_lower) and col_lower not in ["code", "entity", "year"]:
                cpi_col = col
                break
        
        if cpi_col is None and "Corruption Perceptions Index" in df.columns:
            cpi_col = "Corruption Perceptions Index"
        elif cpi_col is None and "Value" in df.columns:
            cpi_col = "Value"
        elif cpi_col is None:
            # Find first numeric column that's not Code, Entity, or Year
            exclude_cols = {"Code", "Entity", "Year", "code", "entity", "year"}
            for col in df.columns:
                if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col]):
                    cpi_col = col
                    break
        
        if cpi_col is None:
            print("Warning: Could not identify CPI column")
            print(f"Available columns: {list(df.columns)}")
            return pd.DataFrame(columns=["country_code", "cpi_score"])
        
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
            print(f"Available columns: {list(df.columns)}")
            return pd.DataFrame(columns=["country_code", "cpi_score"])
        
        if cpi_col in df.columns:
            result["cpi_score"] = pd.to_numeric(df[cpi_col], errors="coerce")
        else:
            print("Warning: CPI score column not found")
            print(f"CPI column searched: {cpi_col}, Available columns: {list(df.columns)}")
            return pd.DataFrame(columns=["country_code", "cpi_score"])
        
        # Filter to requested countries if specified
        if country_codes:
            result = result[result["country_code"].isin(country_codes)].copy()
        
        # If result is empty and we have country codes, use fallback
        if len(result) == 0 and country_codes:
            print("CPI download returned no data, using fallback values")
            fallback_data = {
                "country_code": [],
                "cpi_score": []
            }
            for code in country_codes:
                if code in FALLBACK_CPI:
                    fallback_data["country_code"].append(code)
                    fallback_data["cpi_score"].append(FALLBACK_CPI[code])
            if fallback_data["country_code"]:
                result = pd.DataFrame(fallback_data)
        
        # Debug output
        if len(result) > 0:
            print(f"CPI data loaded: {len(result)} countries, latest year: {df['Year'].max() if 'Year' in df.columns and len(df) > 0 else 'N/A'}")
            if country_codes and len(result) < len(country_codes):
                missing = set(country_codes) - set(result["country_code"].unique())
                if missing:
                    print(f"Warning: CPI missing for countries: {missing}")
                    # Fill missing with fallback if available
                    for code in missing:
                        if code in FALLBACK_CPI:
                            result = pd.concat([
                                result,
                                pd.DataFrame({"country_code": [code], "cpi_score": [FALLBACK_CPI[code]]})
                            ], ignore_index=True)
                            print(f"  Using fallback CPI for {code}: {FALLBACK_CPI[code]}")
        
        return result.reset_index(drop=True)


if __name__ == "__main__":
    # Test client
    client = OWIDClient()
    df = client.fetch_cpi(country_codes=["AUS", "SGP", "JPN"])
    print(df)

