# US Top 50 Playlist Performance & Song Popularity Trend Analysis

Streamlit analytics dashboard for Atlantic Recording Corporation's US Top 50 playlist (historical analytics only).

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Adding new data (no code changes)
* Save any new CSV with the same 10 columns (`date, position, song, artist, popularity, duration_ms, album_type,
  total_tracks, is_explicit, album_cover_url`) into `data/` and press **R** / "Reload data folder", **or**
* Upload it from the sidebar ▸ *Add / refresh data*.

Overlapping dates are de-duplicated (newer rows win), the date range, filters, KPIs, charts, insights and the
executive summary all recompute automatically.

## Modules (tabs)
| Tab | Covers |
|---|---|
| Timeline | Playlist timeline explorer, chart health, entries vs exits |
| Rank Trends | Song ranking trend charts, daily rank distribution, rank movement, fast risers / slow decliners |
| Songs | Longest presence, highest popularity, peak rank vs longevity, song deep-dive |
| Artists | Dominance leaderboard, dominance over time, breadth vs depth, artist deep-dive |
| Popularity | Popularity vs rank, Top 10/20/50 distribution, stability vs volatility, trend score |
| Content | Explicit vs clean, single vs album, duration, album size |
| Exec Summary | Auto-generated findings and implications (downloadable) |
| Data & Export | Validation report, CSV exports |

## KPI definitions
* **Days on Chart** – distinct snapshot dates a song appears.
* **Rank Volatility Index** – standard deviation of a song's daily rank.
* **Popularity Trend Score** – mean of the latest 7 popularity readings minus the first 7 (rolling-window change).
* **Artist Dominance Index** – artist's share of rank-weighted chart points (rank 1 = 50 pts … rank 50 = 1 pt).
* **Explicit Content Share** – % of chart entries flagged explicit.

## Data cleaning rules
Ranks outside 1–50 dropped · artist names whitespace-normalised · duplicate song-date / rank-date rows removed ·
a date scraped twice keeps only the latest snapshot · popularity `0` treated as a missing score.
