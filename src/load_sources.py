from __future__ import annotations
from pathlib import Path
import json
from functools import lru_cache
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=None)
def load_json(rel_path: str):
    with open(ROOT / rel_path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load_sources() -> dict:
    return load_json("config/sources.json")


@lru_cache(maxsize=None)
def load_symbol_rules() -> dict:
    return load_json("config/symbol_rules.json")


@lru_cache(maxsize=None)
def load_fallback_language() -> dict:
    return load_json("config/fallback_language.json")


@lru_cache(maxsize=None)
def load_keyword_mappings() -> dict:
    return load_json("data/keyword_mappings2.json")


@lru_cache(maxsize=None)
def load_data(population: str) -> pd.DataFrame:
    sources = load_sources()
    if population not in sources:
        raise ValueError(f"Unknown population {population!r}; expected one of {list(sources)}")
    path = ROOT / sources[population]["file"]
    df = pd.read_csv(path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce")
    for col in ["Outcome (or Indicator)", "col_label", "Group", "Confidence Interval", "Title", "Description"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    return df
