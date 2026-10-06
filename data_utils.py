"""Data ingestion, validation, feature engineering and KPI logic.

Everything here is data-driven: drop new CSVs (same columns) into ./data or upload them in the app
and every metric, chart and insight recomputes automatically.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = ["date", "position", "song", "artist", "popularity", "duration_ms",
            "album_type", "total_tracks", "is_explicit", "album_cover_url"]


# --------------------------------------------------------------------------- ingestion
def _parse_dates(s: pd.Series) -> pd.Series:
    out = pd.to_datetime(s, format="%d-%m-%Y", errors="coerce")
    miss = out.isna()
    if miss.any():
        out.loc[miss] = pd.to_datetime(s[miss], errors="coerce", format="mixed", dayfirst=True)
    return out


def _to_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "t"])


def _clean_artist(a: str) -> str:
    a = re.sub(r"\s+", " ", str(a)).strip()
    return re.sub(r"\s*&\s*", " & ", a)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate + standardise. Returns (clean_df, quality_report)."""
    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required column(s): {', '.join(missing_cols)}")
    df = df[REQUIRED]
    q = {"rows_loaded": len(df)}

    df["dt"] = _parse_dates(df["date"])
    q["bad_dates_dropped"] = int(df["dt"].isna().sum())
    df = df.dropna(subset=["dt"])

    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    bad_rank = ~df["position"].between(1, 50)
    q["rank_out_of_range_dropped"] = int(bad_rank.sum())
    df = df[~bad_rank].copy()
    df["position"] = df["position"].astype(int)

    for c in ["popularity", "duration_ms", "total_tracks"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["is_explicit"] = _to_bool(df["is_explicit"])
    df["song"] = df["song"].astype(str).str.strip()
    df["artist"] = df["artist"].map(_clean_artist)
    df["album_type"] = df["album_type"].astype(str).str.strip().str.lower()

    q["missing_values"] = int(df[["song", "artist", "position"]].isna().sum().sum())
    df = df.dropna(subset=["song", "artist"])

    # popularity 0 is a missing-score placeholder in this feed -> treat as unknown
    q["zero_popularity_as_missing"] = int((df["popularity"] == 0).sum())
    df.loc[df["popularity"] == 0, "popularity"] = np.nan

    # a date that appears twice as a full snapshot (e.g. a re-scrape) -> keep the latest snapshot only
    df["_ord"] = np.arange(len(df))
    cnt = df.groupby("dt")["position"].transform("size")
    last_top = df["_ord"].where(df["position"] == 1).groupby(df["dt"]).transform("max")
    stale = (cnt > 50) & (df["_ord"] < last_top)
    q["stale_snapshot_rows_dropped"] = int(stale.sum())
    df = df[~stale].drop(columns="_ord")

    # remaining duplicates: later rows (newer uploads) win
    before = len(df)
    df = df.drop_duplicates(["dt", "song", "artist"], keep="last")
    q["duplicate_song_date_dropped"] = before - len(df)
    before = len(df)
    df = df.drop_duplicates(["dt", "position"], keep="last")
    q["duplicate_rank_date_dropped"] = before - len(df)

    df = df.sort_values(["dt", "position"]).reset_index(drop=True)
    df["song_key"] = df["song"] + "  ·  " + df["artist"]
    df["duration_min"] = df["duration_ms"] / 60000
    df["month"] = df["dt"].dt.to_period("M").dt.to_timestamp()

    snaps = pd.Index(sorted(df["dt"].unique()))
    q["snapshots"] = len(snaps)
    q["date_min"], q["date_max"] = snaps.min(), snaps.max()
    full = pd.date_range(snaps.min(), snaps.max())
    q["missing_days"] = [d.strftime("%d %b %Y") for d in full.difference(snaps)]
    sizes = df.groupby("dt").size()
    q["incomplete_snapshots"] = int((sizes != 50).sum())
    q["rows_clean"] = len(df)
    return df, q


def read_csv_bytes(content: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(content))


def folder_signature(folder: Path) -> tuple:
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(folder.glob("*.csv")))


def load_all(folder: Path, uploads: list[tuple[str, bytes]], replace: bool) -> tuple[pd.DataFrame, dict]:
    frames = []
    if not (replace and uploads):
        frames += [pd.read_csv(p) for p in sorted(folder.glob("*.csv"))]
    frames += [read_csv_bytes(b) for _, b in uploads]
    if not frames:
        raise ValueError("No data found. Add a CSV to the data/ folder or upload one in the sidebar.")
    for f in frames:
        f.columns = [c.strip().lower() for c in f.columns]
    return clean(pd.concat(frames, ignore_index=True))


# --------------------------------------------------------------------------- features
def _trend(g: pd.DataFrame, w: int = 7) -> float:
    p = g.sort_values("dt")["popularity"].dropna()
    if len(p) < 2:
        return np.nan
    k = min(w, len(p) // 2 or 1)
    return float(p.iloc[-k:].mean() - p.iloc[:k].mean())


def _slope(g: pd.DataFrame) -> float:
    g = g.sort_values("dt")
    if len(g) < 2:
        return np.nan
    x = (g["dt"] - g["dt"].min()).dt.days.to_numpy(float)
    if x.std() == 0:
        return np.nan
    return float(np.polyfit(x, g["position"].to_numpy(float), 1)[0])


def song_metrics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("song_key")
    m = g.agg(song=("song", "first"), artist=("artist", "first"),
              days_on_chart=("dt", "nunique"), avg_rank=("position", "mean"),
              best_rank=("position", "min"), worst_rank=("position", "max"),
              rank_volatility=("position", "std"), avg_popularity=("popularity", "mean"),
              pop_volatility=("popularity", "std"),
              first_seen=("dt", "min"), last_seen=("dt", "max"),
              explicit=("is_explicit", "first"), album_type=("album_type", "first"),
              duration_min=("duration_min", "mean"), total_tracks=("total_tracks", "first"),
              cover=("album_cover_url", "last"))
    m["rank_volatility"] = m["rank_volatility"].fillna(0)
    m["pop_trend"] = g.apply(_trend, include_groups=False)
    m["rank_slope"] = g.apply(_slope, include_groups=False)  # positions per day; negative = climbing
    return m.reset_index()


def add_movement(df: pd.DataFrame) -> pd.DataFrame:
    """Day-over-day rank movement (positive = climbed) between consecutive chart snapshots."""
    snaps = {d: i for i, d in enumerate(sorted(df["dt"].unique()))}
    d = df.sort_values(["song_key", "dt"]).copy()
    d["snap"] = d["dt"].map(snaps)
    consecutive = d.groupby("song_key")["snap"].diff().eq(1)
    d["movement"] = (-d.groupby("song_key")["position"].diff()).where(consecutive)
    return d.sort_values(["dt", "position"])


def entry_exit(df: pd.DataFrame) -> pd.DataFrame:
    snaps = sorted(df["dt"].unique())
    sets = {d: set(x) for d, x in df.groupby("dt")["song_key"]}
    rows = []
    for prev, cur in zip(snaps[:-1], snaps[1:]):
        rows.append({"dt": cur, "entries": len(sets[cur] - sets[prev]), "exits": len(sets[prev] - sets[cur])})
    return pd.DataFrame(rows)


def artist_metrics(df: pd.DataFrame, split_collabs: bool = False) -> pd.DataFrame:
    d = df
    if split_collabs:
        d = df.assign(artist=df["artist"].str.split(r"\s&\s", regex=True)).explode("artist")
    d = d.assign(points=51 - d["position"])
    total_pts = (51 - df["position"]).sum()
    a = d.groupby("artist").agg(unique_songs=("song", "nunique"), chart_slot_days=("dt", "size"),
                                days_present=("dt", "nunique"), avg_rank=("position", "mean"),
                                best_rank=("position", "min"), avg_popularity=("popularity", "mean"),
                                points=("points", "sum"))
    a["dominance_index"] = a["points"] / total_pts * 100
    a["slot_share"] = a["chart_slot_days"] / len(df) * 100
    return a.drop(columns="points").sort_values("dominance_index", ascending=False).reset_index()


def kpis(df: pd.DataFrame, sm: pd.DataFrame, am: pd.DataFrame) -> dict:
    return {
        "snapshots": df["dt"].nunique(),
        "songs": df["song_key"].nunique(),
        "artists": df["artist"].nunique(),
        "median_days": float(sm["days_on_chart"].median()),
        "avg_rank": float(df["position"].mean()),
        "avg_volatility": float(sm.loc[sm["days_on_chart"] >= 7, "rank_volatility"].mean()),
        "avg_pop": float(df["popularity"].mean()),
        "pop_trend": float(sm["pop_trend"].mean()),
        "top_artist": am.iloc[0]["artist"] if len(am) else "—",
        "top_dom": float(am.iloc[0]["dominance_index"]) if len(am) else 0.0,
        "explicit_share": float(df["is_explicit"].mean() * 100),
    }
