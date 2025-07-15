import hashlib
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


def hash_path(path: str, length: int = 8) -> str:
    """
    Turn any file path into a short hex string.
    By default we use the first `length` chars of a SHA-256 digest.
    """
    h = hashlib.sha256(path.encode("utf-8")).hexdigest()
    return h[:length]


def parquet_cache_file(path: str | Path) -> Path:
    name = path.name
    # TODO: what if path is a str?
    return cache_dir() / f"{hash_path(str(path))}-{name}.parquet"


def object_columns_cache_file(path: str | Path) -> Path:
    name = path.name
    # TODO: what if path is a str?
    return cache_dir() / f"{hash_path(str(path))}-{name}_object_columns.pkl"


def save_df_cache_file(df: pd.DataFrame, path: str | Path) -> None:
    """
    Saves a DataFrame to one or two files in the Texase cache directory:
      - <name>.parquet              : all non-object columns, as Parquet
      - <name>_object_columns.pkl   : all object-dtype columns, pickled

    On load, these will be recombined with identical dtypes.
    """
    # 1) isolate object columns
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # 2) pickle them (if any)
    if obj_cols:
        df[obj_cols].to_pickle(object_columns_cache_file(path))

    # 3) drop them and parquet the rest
    df.drop(columns=obj_cols).to_parquet(parquet_cache_file(path), index=False)


def load_df_cache_file(path: str) -> pd.DataFrame:
    """
    Reads back the two cache files and recombines them:
      - <name>.parquet            → non-object columns
      - <name>_object_columns.pkl → object-dtype columns (if it exists)
    Returns a single DataFrame with original dtypes restored.
    """
    # load the non-object columns
    df = pd.read_parquet(parquet_cache_file(path))

    # if there was a pickle of object columns, load and concat
    obj_path = object_columns_cache_file(path)
    if obj_path.exists():
        obj_df = pd.read_pickle(obj_path)

        # re-attach object columns (index-aligned)
        df = pd.concat([df, obj_df], axis=1)

    return df


def columns_file() -> Path:
    return cache_dir() / "columns.json"
