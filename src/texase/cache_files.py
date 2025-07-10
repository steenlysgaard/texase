import os
from pathlib import Path

import pandas as pd
from platformdirs import user_cache_dir


def cache_dir() -> Path:
    """
    Returns the path to the user cache directory for Texase.
    This is where cached files and configurations are stored.
    """
    if env_path := os.environ.get("TEXASE_CACHE_DIR"):
        cd = Path(env_path)
    else:
        cd = Path(user_cache_dir("texase")).resolve()

    cd.mkdir(parents=True, exist_ok=True)
    return cd


def save_parquet_cache(df: pd.DataFrame, name: str) -> None:
    """
    Saves a DataFrame to a Parquet file in the Texase cache directory.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        name (str): The name of the Parquet file (without extension).
    """
    cache_path = cache_dir() / f"{name}.parquet"
    df.to_parquet(cache_path, index=False)
