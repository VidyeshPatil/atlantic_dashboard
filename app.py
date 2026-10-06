"""US Top 50 Playlist Performance & Song Popularity Trend Analysis — Streamlit dashboard.

Run:  streamlit run app.py
New data: drop more CSVs (same columns) into ./data, or upload them from the sidebar.
"""
from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_utils as du

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------- theme
TEAL, SKY, CORAL, AMBER, LIME, VIOLET = "#2DD4BF", "#38BDF8", "#FB7185", "#FBBF24", "#A3E635", "#A78BFA"
SEQ = [TEAL, SKY, CORAL, AMBER, LIME, VIOLET, "#F472B6", "#5EEAD4", "#93C5FD", "#FDBA74"]
SCALE = [[0, "#0F3B53"], [0.5, TEAL], [1, "#FDE68A"]]
SCALE_R = [[0, "#FDE68A"], [0.5, TEAL], [1, "#0F3B53"]]
INK = "#E6F6F4"
px.defaults.color_discrete_sequence = SEQ
px.defaults.template = "plotly_dark"

st.set_page_config(page_title="US Top 50 · Playlist Analytics", page_icon="🎧", layout="wide",
                   initial_sidebar_state="expanded")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


BG, HERO = b64(ROOT / "assets/bg_main.jpg"), b64(ROOT / "assets/bg_hero.jpg")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input {{ font-family: 'Poppins', sans-serif; }}
.stApp {{
  background: linear-gradient(180deg, rgba(5,16,28,.55), rgba(5,12,24,.88)),
              url("data:image/jpeg;base64,{BG}") center / cover fixed no-repeat, #06121f;
  color: {INK};
}}
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, rgba(7,30,42,.93), rgba(8,16,32,.96));
  border-right: 1px solid rgba(45,212,191,.25);
}}
[data-testid="stSidebar"] * {{ color: {INK}; }}
.block-container {{ padding-top: 1.2rem; max-width: 1500px; }}
h1, h2, h3, h4 {{ color: #fff !important; letter-spacing: -.01em; }}
h3 {{ border-left: 4px solid {TEAL}; padding-left: .6rem; margin-top: .6rem; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: rgba(10, 30, 44, .58); backdrop-filter: blur(10px);
  border: 1px solid rgba(94,234,212,.18) !important; border-radius: 18px;
  box-shadow: 0 10px 30px rgba(0,0,0,.28);
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; flex-wrap: wrap; }}
.stTabs [data-baseweb="tab"] {{
  background: rgba(10,30,44,.6); border-radius: 12px; padding: 8px 12px; color: {INK}; font-size: .86rem;
  border: 1px solid rgba(94,234,212,.15);
}}
.stTabs [aria-selected="true"] {{ background: linear-gradient(90deg, {TEAL}, {SKY}); color:#04202b !important; font-weight:600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}
.hero {{
  position: relative; overflow: hidden; border-radius: 24px; padding: 34px 38px; margin-bottom: 18px;
  background: linear-gradient(100deg, rgba(4,24,34,.80) 25%, rgba(4,24,34,.15)),
              url("data:image/jpeg;base64,{HERO}") center / cover;
  border: 1px solid rgba(94,234,212,.3); box-shadow: 0 18px 50px rgba(0,0,0,.35);
}}
.hero {{ padding-right: 400px; }}
.hero h1 {{ font-size: 2.1rem; font-weight: 800; margin: 0 0 6px 0; line-height: 1.15; }}
.hero p {{ color: #bfe9e4; max-width: 640px; margin: 0 0 14px 0; font-size: .95rem; }}
.pill {{ display:inline-block; padding: 4px 12px; margin: 0 6px 6px 0; border-radius: 999px; font-size:.78rem;
        background: rgba(45,212,191,.16); border: 1px solid rgba(45,212,191,.45); color:#b6f5ec; }}
.mosaic {{ position:absolute; right: 28px; top: 50%; transform: translateY(-50%); display:grid;
          grid-template-columns: repeat(4, 80px); gap: 8px; transform: translateY(-50%) rotate(-3deg); }}
.mosaic img {{ width:80px; height:80px; border-radius: 12px; object-fit: cover; opacity:.92;
              box-shadow: 0 6px 18px rgba(0,0,0,.45); border: 1px solid rgba(255,255,255,.18); }}
@media (max-width: 1150px) {{ .mosaic {{ display:none; }} .hero {{ padding-right: 38px; }} }}
.kpi {{ border-radius: 16px; padding: 14px 16px; height: 100%;
       background: linear-gradient(145deg, rgba(45,212,191,.16), rgba(56,189,248,.07));
       border: 1px solid rgba(94,234,212,.28); }}
.kpi .l {{ font-size:.72rem; text-transform: uppercase; letter-spacing:.08em; color:#8ddfd5; }}
.kpi .v {{ font-size:1.65rem; font-weight:700; color:#fff; line-height:1.2; }}
.kpi .s {{ font-size:.74rem; color:#a8cfcb; }}
.insight {{ border-left: 3px solid {CORAL}; padding: 8px 14px; margin: 8px 0; border-radius: 0 12px 12px 0;
           background: rgba(251,113,133,.08); color:#ffe4e8; font-size:.92rem; }}
[data-testid="stDataFrame"] {{ border-radius: 12px; overflow:hidden; }}
</style>
""", unsafe_allow_html=True)


def style(fig: go.Figure, h: int = 420) -> go.Figure:
    fig.update_layout(template="plotly_dark", height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Poppins, sans-serif", color=INK), colorway=SEQ,
                      margin=dict(l=10, r=10, t=48, b=10), legend=dict(bgcolor="rgba(0,0,0,0)"),
                      title=dict(font=dict(size=15)), hoverlabel=dict(bgcolor="#0b2a3a"))
    fig.update_xaxes(gridcolor="rgba(148,210,200,.10)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,210,200,.10)", zeroline=False)
    return fig


def kpi(label: str, value: str, sub: str = "") -> str:
    return f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}&nbsp;</div></div>'


def insight(text: str):
    st.markdown(f'<div class="insight">💡 {text}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------- data
@st.cache_data(show_spinner="Loading & validating data…")
def get_data(signature: tuple, uploads: tuple, replace: bool):
    return du.load_all(DATA_DIR, list(uploads), replace)


@st.cache_data(show_spinner="Computing song metrics…")
def get_song_metrics(df: pd.DataFrame):
    return du.song_metrics(df)


@st.cache_data(show_spinner=False)
def get_artist_metrics(df: pd.DataFrame, split: bool):
    return du.artist_metrics(df, split)


@st.cache_data(show_spinner=False)
def get_movement(df: pd.DataFrame):
    return du.add_movement(df)


with st.sidebar:
    st.markdown("## 🎧 Control Room")
    st.caption("Everything recomputes from the data — add new snapshots any time.")
    with st.expander("➕ Add / refresh data", expanded=False):
        files = st.file_uploader("Upload new CSV snapshot(s)", type="csv", accept_multiple_files=True,
                                 help="Same 10 columns as the base file. Newer rows override duplicates.")
        replace = st.checkbox("Use ONLY uploaded files (ignore data/ folder)", value=False)
        if st.button("↻ Reload data folder", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.caption("Tip: CSVs saved into the `data/` folder are picked up automatically.")
uploads = tuple((f.name, f.getvalue()) for f in (files or []))

try:
    full, quality = get_data(du.folder_signature(DATA_DIR), uploads, replace)
except Exception as e:  # noqa: BLE001
    st.error(f"Could not load data: {e}")
    st.stop()

dmin, dmax = full["dt"].min().date(), full["dt"].max().date()
with st.sidebar:
    st.markdown("### Filters")
    rng = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax, format="DD/MM/YYYY")
    d0, d1 = (rng if isinstance(rng, (tuple, list)) and len(rng) == 2 else (dmin, dmax))
    r0, r1 = st.slider("Rank range", 1, 50, (1, 50))
    types = sorted(full["album_type"].unique())
    sel_types = st.multiselect("Album type", types, default=types)
    base = full[(full["dt"].dt.date.between(d0, d1)) & full["position"].between(r0, r1) & full["album_type"].isin(sel_types)]
    sel_artists = st.multiselect("Artist(s)", sorted(base["artist"].unique()), placeholder="All artists")
    if sel_artists:
        base = base[base["artist"].isin(sel_artists)]
    sel_songs = st.multiselect("Song(s)", sorted(base["song_key"].unique()), placeholder="All songs")
    if sel_songs:
        base = base[base["song_key"].isin(sel_songs)]
    split = st.checkbox("Credit collaborators individually", value=False,
                        help="Splits 'A & B' so both artists get credit in the Artist tab.")
    st.markdown("---")
    st.caption(f"Data window: **{dmin:%d %b %Y} → {dmax:%d %b %Y}**")

df = base
if df.empty:
    st.warning("No rows match the current filters. Widen the date range, rank range, or clear artist/song filters.")
    st.stop()

sm = get_song_metrics(df)
am = get_artist_metrics(df, split)
mv = get_movement(df)
K = du.kpis(df, sm, am)
span_days = (df["dt"].max() - df["dt"].min()).days
df = df.assign(bucket=df["dt"].dt.to_period("W").dt.start_time if span_days <= 120 else df["month"])
bucket_name = "week" if span_days <= 120 else "month"

# ----------------------------------------------------------------------------- hero
latest = full[full["dt"] == full["dt"].max()].nsmallest(12, "position")
tiles = "".join(f'<img src="{u}" loading="lazy" alt="" onerror="this.style.visibility=\'hidden\'">' for u in latest["album_cover_url"])
st.markdown(f"""
<div class="hero">
  <div class="mosaic">{tiles}</div>
  <h1>United States Top 50<br>Playlist Performance &amp; Popularity Trends</h1>
  <p>Historical playlist analytics for Atlantic Recording Corporation — ranking stability, song longevity,
     artist dominance and the content traits behind sustained chart success.</p>
  <span class="pill">📅 {df['dt'].min():%d %b %Y} – {df['dt'].max():%d %b %Y}</span>
  <span class="pill">🗂 {K['snapshots']:,} daily snapshots</span>
  <span class="pill">🎵 {K['songs']:,} songs</span>
  <span class="pill">🎤 {K['artists']:,} artists</span>
</div>
""", unsafe_allow_html=True)

cols = st.columns(6)
cards = [
    ("Days on Chart", f"{K['median_days']:.0f}", "median per song · longevity"),
    ("Average Rank", f"{K['avg_rank']:.1f}", "overall performance"),
    ("Rank Volatility", f"{K['avg_volatility']:.1f}", "avg σ of rank · songs ≥7 days"),
    ("Popularity Trend", f"{K['pop_trend']:+.1f}", f"avg score {K['avg_pop']:.1f}"),
    ("Artist Dominance", f"{K['top_dom']:.1f}%", K["top_artist"][:28]),
    ("Explicit Share", f"{K['explicit_share']:.1f}%", "of chart entries"),
]
for c, (a, b, s) in zip(cols, cards):
    c.markdown(kpi(a, b, s), unsafe_allow_html=True)
st.write("")

tabs = st.tabs(["🏠 Timeline", "📈 Rank Trends", "🎵 Songs", "🎤 Artists",
                "🎯 Popularity", "🔥 Content", "📝 Exec Summary", "🧪 Data & Export"])

# ============================================================================ 1. TIMELINE
with tabs[0]:
    with st.container(border=True):
        st.markdown("### Playlist timeline explorer")
        snaps = sorted(df["dt"].unique())
        pick = st.select_slider("Pick a snapshot date", options=snaps, value=snaps[-1],
                                format_func=lambda d: pd.Timestamp(d).strftime("%d %b %Y"))
        day = mv[mv["dt"] == pick].copy()
        day["Move"] = day["movement"].map(lambda m: "NEW" if pd.isna(m) else ("▲ %d" % m if m > 0 else ("▼ %d" % -m if m < 0 else "—")))
        left, right = st.columns([1.55, 1])
        with left:
            st.dataframe(
                day[["position", "album_cover_url", "song", "artist", "popularity", "Move", "is_explicit", "album_type"]],
                hide_index=True, width="stretch", height=470,
                column_config={"position": st.column_config.NumberColumn("#", width="small"),
                               "album_cover_url": st.column_config.ImageColumn("Cover", width="small"),
                               "song": "Song", "artist": "Artist",
                               "popularity": st.column_config.ProgressColumn("Popularity", min_value=0, max_value=100, format="%d"),
                               "is_explicit": st.column_config.CheckboxColumn("Explicit", width="small"),
                               "album_type": "Type"})
        with right:
            fig = px.bar(day.sort_values("position"), x="popularity", y="song", orientation="h", color="popularity",
                         color_continuous_scale=SCALE, title=f"Popularity by rank · {pd.Timestamp(pick):%d %b %Y}")
            fig.update_yaxes(autorange="reversed", showticklabels=False, title="rank 1 → 50")
            fig.update_xaxes(range=[max(0, day["popularity"].min() - 5 if day["popularity"].notna().any() else 0), 101])
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(style(fig, 470), width="stretch")

    with st.container(border=True):
        st.markdown("### Chart health over time")
        daily = df.groupby("dt").agg(pop=("popularity", "mean")).reset_index()
        t10 = df[df["position"] <= 10].groupby("dt")["popularity"].mean().rename("top10pop")
        daily = daily.merge(t10, on="dt", how="left")
        daily["pop7"] = daily["pop"].rolling(7, min_periods=1).mean()
        c1, c2 = st.columns(2)
        f = go.Figure()
        f.add_trace(go.Scatter(x=daily["dt"], y=daily["pop"], name="Daily avg", line=dict(color="rgba(56,189,248,.35)", width=1)))
        f.add_trace(go.Scatter(x=daily["dt"], y=daily["pop7"], name="7-day rolling", line=dict(color=TEAL, width=3)))
        f.add_trace(go.Scatter(x=daily["dt"], y=daily["top10pop"].rolling(7, min_periods=1).mean(), name="Top 10 (7-day)",
                               line=dict(color=CORAL, width=2, dash="dot")))
        f.update_layout(title="Average popularity score")
        c1.plotly_chart(style(f, 360), width="stretch")
        ee = du.entry_exit(df)
        if not ee.empty:
            f2 = go.Figure()
            f2.add_trace(go.Bar(x=ee["dt"], y=ee["entries"], name="New entries", marker_color=LIME))
            f2.add_trace(go.Bar(x=ee["dt"], y=-ee["exits"], name="Exits", marker_color=CORAL))
            f2.update_layout(barmode="relative", title="Chart turnover per snapshot (entries ▲ / exits ▼)")
            c2.plotly_chart(style(f2, 360), width="stretch")
            big = ee.loc[ee["entries"].idxmax()]
            insight(f"Typical turnover is about <b>{ee['entries'].median():.0f}</b> new songs per snapshot; the biggest reshuffle "
                    f"was <b>{pd.Timestamp(big['dt']):%d %b %Y}</b> with <b>{int(big['entries'])}</b> new entries.")

# ============================================================================ 2. RANKING TRENDS
with tabs[1]:
    with st.container(border=True):
        st.markdown("### Song ranking trend charts")
        top_default = sm.nlargest(5, "days_on_chart")["song_key"].tolist()
        chosen = st.multiselect("Songs to compare", sorted(sm["song_key"]), default=top_default)
        smooth = st.toggle("Smooth with 7-day rolling average", value=False)
        sub = df[df["song_key"].isin(chosen)].copy()
        if smooth:
            sub["position"] = sub.sort_values("dt").groupby("song_key")["position"].transform(lambda s: s.rolling(7, min_periods=1).mean())
        if sub.empty:
            st.info("Select at least one song.")
        else:
            fig = px.line(sub, x="dt", y="position", color="song_key", title="Chart position over time (1 = top)")
            fig.update_yaxes(autorange="reversed", range=[50, 1])
            fig.update_traces(line=dict(width=2.4))
            fig.update_layout(legend=dict(orientation="h", y=-0.18, title=""))
            fig.update_xaxes(title="")
            st.plotly_chart(style(fig, 480), width="stretch")

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("### Daily rank distribution")
        churn = df.groupby(["bucket", "position"])["song_key"].nunique().reset_index(name="songs")
        pv = churn.pivot(index="position", columns="bucket", values="songs")
        fig = px.imshow(pv, aspect="auto", color_continuous_scale=SCALE, origin="upper",
                        labels=dict(x=bucket_name.capitalize(), y="Rank", color="Distinct songs"),
                        title=f"Distinct songs that held each rank, per {bucket_name}")
        st.plotly_chart(style(fig, 440), width="stretch")
        top_churn = churn[churn["position"] <= 10]["songs"].mean(); low_churn = churn[churn["position"] > 40]["songs"].mean()
        insight(f"Ranks 1–10 change hands less ({top_churn:.0f} distinct songs per rank-{bucket_name}) than ranks 41–50 "
                f"({low_churn:.0f}) — the top of the chart is stickier.")
    with c2, st.container(border=True):
        st.markdown("### Rank movement patterns")
        m = mv.dropna(subset=["movement"])
        fig = px.histogram(m, x="movement", nbins=60, title="Day-over-day rank change (positive = climbed)",
                           color_discrete_sequence=[SKY])
        fig.update_xaxes(range=[-20, 20])
        fig.update_yaxes(type="log", title="entries (log)")
        st.plotly_chart(style(fig, 230), width="stretch")
        band = pd.cut(m["position"], [0, 10, 20, 30, 40, 50], labels=["1–10", "11–20", "21–30", "31–40", "41–50"])
        mab = m.assign(band=band).groupby("band", observed=True)["movement"].apply(lambda s: s.abs().mean()).reset_index()
        fig = px.bar(mab, x="band", y="movement", color="movement", color_continuous_scale=SCALE,
                     title="Average absolute daily move by rank band")
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(style(fig, 190), width="stretch")

    with st.container(border=True):
        st.markdown("### Fast risers & slow decliners")
        min_days = st.slider("Minimum days on chart", 5, 120, 14)
        elig = sm[sm["days_on_chart"] >= min_days].dropna(subset=["rank_slope"]).copy()
        elig["pos_per_week"] = elig["rank_slope"] * 7
        r, d = st.columns(2)
        up = elig.nsmallest(10, "pos_per_week"); dn = elig.nlargest(10, "pos_per_week")
        fig = px.bar(up.sort_values("pos_per_week", ascending=False), x="pos_per_week", y="song_key", orientation="h",
                     color_discrete_sequence=[LIME], title="Fastest climbers (positions gained / week)")
        fig.update_yaxes(title="", tickfont=dict(size=10))
        r.plotly_chart(style(fig, 420), width="stretch")
        fig = px.bar(dn.sort_values("pos_per_week"), x="pos_per_week", y="song_key", orientation="h",
                     color_discrete_sequence=[CORAL], title="Slowest decliners (positions lost / week)")
        fig.update_yaxes(title="", tickfont=dict(size=10))
        d.plotly_chart(style(fig, 420), width="stretch")
        jumps = mv.dropna(subset=["movement"]).nlargest(10, "movement").assign(from_pos=lambda x: (x["position"] + x["movement"]).astype(int))
        st.markdown("**Biggest single-day jumps**")
        st.dataframe(jumps[["dt", "song", "artist", "from_pos", "position", "movement"]].rename(
            columns={"dt": "Date", "song": "Song", "artist": "Artist", "from_pos": "From", "position": "To", "movement": "Places gained"}),
            hide_index=True, width="stretch", column_config={"Date": st.column_config.DateColumn(format="DD MMM YYYY")})

# ============================================================================ 3. SONG PERFORMANCE
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("### Longest playlist presence")
        n = st.slider("How many songs", 5, 30, 15, key="n_long")
        t = sm.nlargest(n, "days_on_chart").sort_values("days_on_chart")
        fig = px.bar(t, x="days_on_chart", y="song_key", orientation="h", color="avg_rank", color_continuous_scale=SCALE_R,
                     labels=dict(days_on_chart="Days on chart", avg_rank="Avg rank"), title="Days on chart (colour = average rank)")
        fig.update_yaxes(title="", tickfont=dict(size=10))
        st.plotly_chart(style(fig, 520), width="stretch")
    with c2, st.container(border=True):
        st.markdown("### Highest average popularity")
        mind = st.slider("Minimum days on chart", 1, 60, 14, key="min_pop")
        t = sm[sm["days_on_chart"] >= mind].nlargest(n, "avg_popularity").sort_values("avg_popularity")
        fig = px.bar(t, x="avg_popularity", y="song_key", orientation="h", color="days_on_chart", color_continuous_scale=SCALE,
                     labels=dict(avg_popularity="Avg popularity", days_on_chart="Days"), title="Average popularity score")
        fig.update_xaxes(range=[max(0, t["avg_popularity"].min() - 4), 100]); fig.update_yaxes(title="", tickfont=dict(size=10))
        st.plotly_chart(style(fig, 520), width="stretch")

    with st.container(border=True):
        st.markdown("### Peak rank vs longevity")
        s = sm.assign(pop_size=sm["avg_popularity"].fillna(sm["avg_popularity"].median()).clip(lower=1))
        a, b = st.columns([1.5, 1])
        fig = px.scatter(s, x="best_rank", y="days_on_chart", size="pop_size", color="album_type", hover_name="song_key",
                         opacity=.75, size_max=18,
                         labels=dict(best_rank="Best rank achieved", days_on_chart="Days on chart"),
                         title="Does a higher peak mean a longer stay?")
        fig.update_xaxes(autorange="reversed"); fig.update_yaxes(type="log")
        a.plotly_chart(style(fig, 430), width="stretch")
        s["peak_band"] = pd.cut(s["best_rank"], [0, 1, 5, 10, 20, 50], labels=["#1", "2–5", "6–10", "11–20", "21–50"])
        fig = px.box(s, x="peak_band", y="days_on_chart", color="peak_band", color_discrete_sequence=SEQ, points=False,
                     title="Longevity by peak-rank band", labels=dict(peak_band="Best rank reached", days_on_chart="Days"))
        fig.update_yaxes(type="log"); fig.update_layout(showlegend=False)
        b.plotly_chart(style(fig, 430), width="stretch")
        corr = s[["best_rank", "days_on_chart"]].corr(method="spearman").iloc[0, 1]
        insight(f"Spearman correlation between peak rank and days on chart: <b>{corr:+.2f}</b> "
                f"(negative = songs that peak higher tend to stay longer).")

    with st.container(border=True):
        st.markdown("### Song deep-dive")
        song = st.selectbox("Choose a song", sm.sort_values("days_on_chart", ascending=False)["song_key"])
        row = sm[sm["song_key"] == song].iloc[0]
        a, b = st.columns([1, 3])
        a.image(row["cover"], width=190)
        a.markdown(f"**{row['song']}**  \n{row['artist']}")
        a.caption(f"{row['album_type'].title()} · {row['duration_min']:.2f} min · {'Explicit' if row['explicit'] else 'Clean'}")
        mcols = b.columns(5)
        for c, (l, v) in zip(mcols, [("Days", f"{row['days_on_chart']}"), ("Avg rank", f"{row['avg_rank']:.1f}"),
                                      ("Best rank", f"#{row['best_rank']}"), ("Volatility σ", f"{row['rank_volatility']:.1f}"),
                                      ("Avg popularity", f"{row['avg_popularity']:.0f}" if pd.notna(row['avg_popularity']) else "–")]):
            c.markdown(kpi(l, v), unsafe_allow_html=True)
        ts = df[df["song_key"] == song].sort_values("dt")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts["dt"], y=ts["position"], name="Rank", line=dict(color=TEAL, width=3), yaxis="y"))
        fig.add_trace(go.Scatter(x=ts["dt"], y=ts["popularity"], name="Popularity", line=dict(color=CORAL, width=2, dash="dot"), yaxis="y2"))
        fig.update_layout(yaxis=dict(autorange="reversed", title="Rank"), yaxis2=dict(overlaying="y", side="right", title="Popularity", showgrid=False),
                          legend=dict(orientation="h", y=1.12))
        b.plotly_chart(style(fig, 300), width="stretch")

# ============================================================================ 4. ARTISTS
with tabs[3]:
    with st.container(border=True):
        st.markdown("### Artist dominance leaderboard")
        topn = st.slider("Show top N artists", 5, 40, 15)
        t = am.head(topn)
        a, b = st.columns([1.1, 1])
        fig = px.bar(t.sort_values("dominance_index"), x="dominance_index", y="artist", orientation="h", color="unique_songs",
                     color_continuous_scale=SCALE, labels=dict(dominance_index="Dominance index (%)", unique_songs="Unique songs"),
                     title="Artist Dominance Index = share of rank-weighted chart points")
        fig.update_yaxes(title="")
        a.plotly_chart(style(fig, 560), width="stretch")
        b.dataframe(t[["artist", "unique_songs", "chart_slot_days", "days_present", "avg_rank", "best_rank", "dominance_index"]],
                    hide_index=True, width="stretch", height=560,
                    column_config={"artist": "Artist", "unique_songs": "Unique songs", "chart_slot_days": "Total chart slots",
                                   "days_present": "Days present", "avg_rank": st.column_config.NumberColumn("Avg rank", format="%.1f"),
                                   "best_rank": "Best", "dominance_index": st.column_config.ProgressColumn(
                                       "Dominance %", min_value=0, max_value=float(am["dominance_index"].max()), format="%.2f")})
        top5 = am.head(5)["dominance_index"].sum()
        insight(f"The top 5 artists hold <b>{top5:.1f}%</b> of all rank-weighted chart points; "
                f"<b>{am.iloc[0]['artist']}</b> leads with {am.iloc[0]['dominance_index']:.1f}%.")

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("### Dominance over time")
        d2 = df.assign(artist=df["artist"].str.split(r"\s&\s", regex=True)).explode("artist") if split else df
        d2 = d2.assign(pts=51 - d2["position"])
        tot = (51 - df["position"]).groupby(df["bucket"]).sum()
        top_art = am.head(8)["artist"].tolist()
        g = d2[d2["artist"].isin(top_art)].groupby(["bucket", "artist"])["pts"].sum().reset_index()
        g["share"] = g.apply(lambda r: r["pts"] / tot[r["bucket"]] * 100, axis=1)
        fig = px.area(g, x="bucket", y="share", color="artist", title=f"Share of chart points per {bucket_name} (top 8 artists)",
                      labels=dict(share="% of points", bucket=""))
        fig.update_layout(legend=dict(orientation="h", y=-0.25, title=""))
        st.plotly_chart(style(fig, 420), width="stretch")
    with c2, st.container(border=True):
        st.markdown("### Breadth vs depth")
        fig = px.scatter(am.head(60), x="unique_songs", y="chart_slot_days", size="dominance_index", color="avg_rank",
                         color_continuous_scale=SCALE_R, hover_name="artist", size_max=34, log_y=True,
                         labels=dict(unique_songs="Unique songs charted", chart_slot_days="Total chart slots", avg_rank="Avg rank"),
                         title="Catalog depth vs total presence (top 60 artists)")
        st.plotly_chart(style(fig, 420), width="stretch")

    with st.container(border=True):
        st.markdown("### Artist deep-dive")
        art = st.selectbox("Choose an artist", am["artist"])
        arow = am[am["artist"] == art].iloc[0]
        cc = st.columns(4)
        for c, (l, v) in zip(cc, [("Unique songs", f"{arow['unique_songs']}"), ("Chart slots", f"{arow['chart_slot_days']:,}"),
                                   ("Best rank", f"#{arow['best_rank']}"), ("Dominance", f"{arow['dominance_index']:.2f}%")]):
            c.markdown(kpi(l, v), unsafe_allow_html=True)
        mask = sm["artist"].str.contains(art, regex=False)
        st.dataframe(sm[mask].sort_values("days_on_chart", ascending=False)[
            ["cover", "song", "days_on_chart", "avg_rank", "best_rank", "avg_popularity", "first_seen", "last_seen"]],
            hide_index=True, width="stretch",
            column_config={"cover": st.column_config.ImageColumn("Cover", width="small"), "song": "Song",
                           "days_on_chart": "Days", "avg_rank": st.column_config.NumberColumn("Avg rank", format="%.1f"),
                           "best_rank": "Best", "avg_popularity": st.column_config.NumberColumn("Avg pop", format="%.0f"),
                           "first_seen": st.column_config.DateColumn("First seen", format="DD MMM YYYY"),
                           "last_seen": st.column_config.DateColumn("Last seen", format="DD MMM YYYY")})

# ============================================================================ 5. POPULARITY
pdf = df.dropna(subset=["popularity"])
with tabs[4]:
    with st.container(border=True):
        st.markdown("### Popularity vs rank")
        pe = pdf[["position", "popularity"]].corr(method="pearson").iloc[0, 1]
        sp = pdf[["position", "popularity"]].corr(method="spearman").iloc[0, 1]
        a, b = st.columns([1.5, 1])
        sample = pdf.sample(min(len(pdf), 6000), random_state=1)
        fig = px.density_heatmap(pdf, x="position", y="popularity", nbinsx=50, nbinsy=40, color_continuous_scale=SCALE,
                                 title="Density of chart entries · popularity vs rank")
        fig.add_trace(go.Scatter(x=sample["position"], y=sample["popularity"], mode="markers", name="sample",
                                 marker=dict(size=3, color="rgba(255,255,255,.18)"), hoverinfo="skip"))
        z = np.polyfit(pdf["position"], pdf["popularity"], 1)
        xs = np.array([1, 50])
        fig.add_trace(go.Scatter(x=xs, y=z[0] * xs + z[1], mode="lines", name="linear trend", line=dict(color=CORAL, width=3)))
        fig.update_layout(showlegend=False)
        a.plotly_chart(style(fig, 440), width="stretch")
        b.markdown(kpi("Pearson r", f"{pe:+.2f}", "popularity vs rank"), unsafe_allow_html=True)
        b.write("")
        b.markdown(kpi("Spearman ρ", f"{sp:+.2f}", "rank-based, robust to outliers"), unsafe_allow_html=True)
        b.write("")
        b.markdown(f"<div class='insight'>Negative values mean <b>higher-ranked</b> (smaller position number) songs score higher popularity — "
                   f"but the relationship is {'weak' if abs(sp) < .3 else 'moderate' if abs(sp) < .6 else 'strong'}, "
                   f"so rank is far from fully explained by the popularity score.</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("### Distribution across Top 10 / 20 / 50")
        parts = [pdf[pdf["position"] <= k].assign(tier=f"Top {k}") for k in (10, 20, 50)]
        tiers = pd.concat(parts)
        fig = px.box(tiers, x="tier", y="popularity", color="tier", color_discrete_sequence=[CORAL, AMBER, TEAL], points=False,
                     title="Popularity score by chart tier")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(range=[max(0, pdf["popularity"].quantile(.002) - 2), 101])
        st.plotly_chart(style(fig, 400), width="stretch")
    with c2, st.container(border=True):
        st.markdown("### Popularity stability vs chart volatility")
        stab = sm[sm["days_on_chart"] >= 14].dropna(subset=["pop_volatility"])
        fig = px.scatter(stab, x="pop_volatility", y="rank_volatility", color="avg_rank", color_continuous_scale=SCALE_R,
                         hover_name="song_key", opacity=.8, size_max=14,
                         labels=dict(pop_volatility="Popularity σ", rank_volatility="Rank σ", avg_rank="Avg rank"),
                         title="Songs with ≥14 days on chart")
        st.plotly_chart(style(fig, 400), width="stretch")
        if len(stab) > 3:
            cs = stab[["pop_volatility", "rank_volatility"]].corr(method="spearman").iloc[0, 1]
            insight(f"Popularity σ vs rank σ Spearman: <b>{cs:+.2f}</b> — "
                    f"{'songs whose popularity swings also swing on the chart' if cs > .3 else 'rank volatility is only loosely tied to popularity swings'}.")

    with st.container(border=True):
        st.markdown("### Popularity Trend Score (first vs latest 7 appearances)")
        tr = sm[sm["days_on_chart"] >= 14].dropna(subset=["pop_trend"])
        g1, g2 = st.columns(2)
        fig = px.bar(tr.nlargest(10, "pop_trend").sort_values("pop_trend"), x="pop_trend", y="song_key", orientation="h",
                     color_discrete_sequence=[LIME], title="Biggest popularity gainers")
        fig.update_yaxes(title="", tickfont=dict(size=10)); g1.plotly_chart(style(fig, 380), width="stretch")
        fig = px.bar(tr.nsmallest(10, "pop_trend").sort_values("pop_trend", ascending=False), x="pop_trend", y="song_key", orientation="h",
                     color_discrete_sequence=[CORAL], title="Biggest popularity decliners")
        fig.update_yaxes(title="", tickfont=dict(size=10)); g2.plotly_chart(style(fig, 380), width="stretch")

# ============================================================================ 6. CONTENT
def group_table(frame: pd.DataFrame, col: str) -> pd.DataFrame:
    e = frame.groupby(col).agg(entries=("song_key", "size"), avg_rank=("position", "mean"), avg_pop=("popularity", "mean"),
                               top10_share=("position", lambda s: (s <= 10).mean() * 100))
    key = "explicit" if col == "is_explicit" else col
    sdf = sm.groupby(key).agg(songs=("song_key", "size"), median_days=("days_on_chart", "median"))
    out = e.join(sdf, how="left").reset_index()
    out["entry_share"] = out["entries"] / out["entries"].sum() * 100
    return out


with tabs[5]:
    with st.container(border=True):
        st.markdown("### Explicit vs non-explicit performance")
        ex = group_table(df, "is_explicit"); ex["label"] = ex["is_explicit"].map({True: "Explicit", False: "Non-explicit"})
        cols = st.columns(len(ex))
        for c, (_, r) in zip(cols, ex.iterrows()):
            c.markdown(kpi(r["label"], f"{r['entry_share']:.1f}%", f"avg rank {r['avg_rank']:.1f} · pop {r['avg_pop']:.1f} · "
                           f"median stay {r['median_days']:.0f}d"), unsafe_allow_html=True)
        st.write("")
        a, b, c = st.columns(3)
        sh = df.groupby("bucket")["is_explicit"].mean().mul(100).reset_index()
        fig = px.area(sh, x="bucket", y="is_explicit", title=f"Explicit share of entries per {bucket_name}", color_discrete_sequence=[CORAL],
                      labels=dict(is_explicit="% explicit", bucket=""))
        a.plotly_chart(style(fig, 340), width="stretch")
        fig = px.bar(ex, x="label", y=["avg_rank", "top10_share"], barmode="group", title="Avg rank & Top-10 share (%)",
                     labels=dict(value="", label="", variable=""), color_discrete_sequence=[TEAL, AMBER])
        b.plotly_chart(style(fig, 340), width="stretch")
        fig = px.violin(pdf.assign(label=pdf["is_explicit"].map({True: "Explicit", False: "Non-explicit"})), x="label", y="popularity",
                        color="label", color_discrete_sequence=[CORAL, TEAL], box=True, points=False, title="Popularity distribution")
        fig.update_layout(showlegend=False); fig.update_yaxes(range=[60, 101]); fig.update_xaxes(title="")
        c.plotly_chart(style(fig, 340), width="stretch")

    with st.container(border=True):
        st.markdown("### Single vs album track (and compilation)")
        at = group_table(df, "album_type")
        a, b = st.columns([1, 1.4])
        a.dataframe(at.rename(columns={"album_type": "Type", "entries": "Entries", "entry_share": "Share %", "avg_rank": "Avg rank",
                                       "avg_pop": "Avg pop", "top10_share": "Top-10 %", "songs": "Songs", "median_days": "Median days"})
                    [["Type", "Songs", "Entries", "Share %", "Avg rank", "Avg pop", "Top-10 %", "Median days"]].round(1),
                    hide_index=True, width="stretch")
        mix = df.groupby(["bucket", "album_type"]).size().reset_index(name="n")
        mix["share"] = mix["n"] / mix.groupby("bucket")["n"].transform("sum") * 100
        fig = px.area(mix, x="bucket", y="share", color="album_type", title=f"Release-format mix per {bucket_name} (% of entries)",
                      labels=dict(share="%", bucket="", album_type=""))
        b.plotly_chart(style(fig, 320), width="stretch")

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("### Song duration impact")
        dur = df.dropna(subset=["duration_min"]).copy()
        dur["bin"] = pd.cut(dur["duration_min"], [0, 2, 2.5, 3, 3.5, 4, 5, 20], labels=["<2", "2–2.5", "2.5–3", "3–3.5", "3.5–4", "4–5", "5+"])
        db = dur.groupby("bin", observed=True).agg(entries=("position", "size"), avg_rank=("position", "mean"), avg_pop=("popularity", "mean")).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=db["bin"].astype(str), y=db["entries"], name="Entries", marker_color="rgba(56,189,248,.45)", yaxis="y"))
        fig.add_trace(go.Scatter(x=db["bin"].astype(str), y=db["avg_rank"], name="Avg rank", mode="lines+markers", line=dict(color=CORAL, width=3), yaxis="y2"))
        fig.update_layout(title="Entries & average rank by duration (minutes)", yaxis2=dict(overlaying="y", side="right", autorange="reversed", showgrid=False, title="Avg rank"),
                          legend=dict(orientation="h", y=1.12))
        st.plotly_chart(style(fig, 380), width="stretch")
        r1 = dur[["duration_min", "popularity"]].corr(method="spearman").iloc[0, 1]
        r2 = dur[["duration_min", "position"]].corr(method="spearman").iloc[0, 1]
        insight(f"Duration vs popularity ρ = <b>{r1:+.2f}</b>; duration vs rank ρ = <b>{r2:+.2f}</b> "
                f"(median length {dur['duration_min'].median():.2f} min).")
    with c2, st.container(border=True):
        st.markdown("### Album size vs song success")
        sm2 = sm.copy()
        sm2["size_band"] = pd.cut(sm2["total_tracks"], [0, 1, 5, 12, 20, 40, 500], labels=["1 (single)", "2–5", "6–12", "13–20", "21–40", "40+"])
        tb = sm2.groupby("size_band", observed=True).agg(songs=("song_key", "size"), avg_rank=("avg_rank", "mean"),
                                                         median_days=("days_on_chart", "median"), avg_pop=("avg_popularity", "mean")).reset_index()
        fig = px.bar(tb, x="size_band", y="median_days", color="avg_rank", color_continuous_scale=SCALE_R, text="songs",
                     labels=dict(size_band="Tracks on the release", median_days="Median days on chart", avg_rank="Avg rank"),
                     title="Median longevity by release size (label = number of songs)")
        st.plotly_chart(style(fig, 380), width="stretch")

# ============================================================================ 7. EXECUTIVE SUMMARY
def build_summary() -> str:
    p10 = sm[sm["best_rank"] <= 10]["days_on_chart"].median(); rest = sm[sm["best_rank"] > 10]["days_on_chart"].median()
    short = (sm["days_on_chart"] <= 7).mean() * 100; long_ = (sm["days_on_chart"] >= 100).sum()
    top_song = sm.loc[sm["days_on_chart"].idxmax()]
    n1 = df[df["position"] == 1]["song_key"].value_counts()
    most_songs = am.sort_values("unique_songs", ascending=False).iloc[0]
    ex_g = df.groupby("is_explicit")["position"].mean()
    ex_diff = ex_g.get(True, np.nan) - ex_g.get(False, np.nan)
    sg = df.groupby("album_type")["position"].agg(["size", "mean"])
    sp = pdf[["position", "popularity"]].corr(method="spearman").iloc[0, 1]
    dur_med = df["duration_min"].median()
    if abs(ex_diff) < 1:
        ex_txt = "Explicit and non-explicit tracks perform comparably on average rank, so content rating is not a strong lever on its own."
    elif ex_diff < 0:
        ex_txt = f"Explicit tracks average a better rank ({ex_g[True]:.1f} vs {ex_g[False]:.1f}); explicit releases are not penalised on this chart."
    else:
        ex_txt = f"Non-explicit tracks average a better rank ({ex_g[False]:.1f} vs {ex_g[True]:.1f}); clean versions may be worth prioritising for playlist fit."
    single_share = sg.loc["single", "size"] / sg["size"].sum() * 100 if "single" in sg.index else 0
    return f"""# Executive Summary — US Top 50 Playlist Analysis
**Scope:** {K['snapshots']:,} daily snapshots from {df['dt'].min():%d %b %Y} to {df['dt'].max():%d %b %Y}
({K['songs']:,} songs, {K['artists']:,} artists). Historical analytics only — not prediction or recommendation of individual tracks.

## Headline findings
1. **Most songs are short-lived.** The median song stays {K['median_days']:.0f} days; {short:.0f}% last a week or less, while only {long_} songs
   exceeded 100 days. The longest run belongs to *{top_song['song']}* by {top_song['artist']} ({top_song['days_on_chart']} days).
2. **Reaching the Top 10 buys staying power.** Songs that peaked in the Top 10 stayed a median of {p10:.0f} days versus {rest:.0f} for the rest.
3. **A few artists dominate.** {am.iloc[0]['artist']} leads with a {am.iloc[0]['dominance_index']:.1f}% dominance index; the top 5 artists
   together hold {am.head(5)['dominance_index'].sum():.1f}%. {most_songs['artist']} placed the most distinct songs ({most_songs['unique_songs']}).
4. **The top of the chart is stable; the bottom churns.** Average rank volatility is {K['avg_volatility']:.1f} positions (σ). The #1 spot was held by
   {len(n1)} different songs, led by *{n1.index[0].split('  ·  ')[0]}* ({n1.iloc[0]} days).
5. **Popularity explains rank only partly.** Spearman ρ between rank and popularity is {sp:+.2f}; average popularity is {K['avg_pop']:.1f} and the average
   popularity trend score is {K['pop_trend']:+.1f}.
6. **Content traits:** {K['explicit_share']:.0f}% of entries are explicit; singles account for {single_share:.0f}% of entries;
   the median track is {dur_med:.2f} minutes long.

## Implications for Atlantic Recording Corporation
- **Artist promotion:** {short:.0f}% of songs last a week or less, so concentrate activity in the first week and reinforce tracks that break into the Top 10 ({p10:.0f} vs {rest:.0f} median days).
- **Release timing:** use the turnover view to avoid launching into weeks with heavy chart reshuffles unless the campaign is strong enough to break through.
- **Marketing spend:** favour sustained support for songs showing rising popularity trend scores and low rank volatility over one-off spikes.
- **Catalog strategy:** artists with many charting songs capture the largest share of chart points; multi-single rollouts widen presence.
- **Content strategy:** {ex_txt}

*Associations are descriptive: this analysis does not establish causation.*
"""


with tabs[6]:
    with st.container(border=True):
        summary = build_summary()
        st.markdown(summary)
        st.download_button("⬇ Download summary (.md)", summary, "executive_summary.md", mime="text/markdown")

# ============================================================================ 8. DATA QUALITY
with tabs[7]:
    with st.container(border=True):
        st.markdown("### Ingestion & validation report")
        q = quality
        a = st.columns(4)
        for c, (l, v, s) in zip(a, [("Rows loaded", f"{q['rows_loaded']:,}", "all CSVs combined"), ("Rows after cleaning", f"{q['rows_clean']:,}", "used for analysis"),
                                    ("Snapshots", f"{q['snapshots']:,}", f"{q['date_min']:%d %b %Y} → {q['date_max']:%d %b %Y}"),
                                    ("Rank range", "1–50 ✓" if q["rank_out_of_range_dropped"] == 0 else "issues", f"{q['rank_out_of_range_dropped']} out-of-range dropped")]):
            c.markdown(kpi(l, v, s), unsafe_allow_html=True)
        st.write("")
        checks = pd.DataFrame([
            ("Invalid / unparseable dates dropped", q["bad_dates_dropped"]),
            ("Ranks outside 1–50 dropped", q["rank_out_of_range_dropped"]),
            ("Missing song/artist values", q["missing_values"]),
            ("Stale duplicate snapshot rows removed (same date scraped twice)", q["stale_snapshot_rows_dropped"]),
            ("Duplicate song-date rows removed", q["duplicate_song_date_dropped"]),
            ("Duplicate rank-date rows removed", q["duplicate_rank_date_dropped"]),
            ("Popularity = 0 treated as missing", q["zero_popularity_as_missing"]),
            ("Snapshots without exactly 50 rows", q["incomplete_snapshots"]),
        ], columns=["Check", "Count"])
        st.dataframe(checks, hide_index=True, width="stretch")
        if q["missing_days"]:
            st.warning(f"Days with no snapshot in the date span: {', '.join(q['missing_days'])}. Day-over-day moves skip these gaps.")
        st.caption("Artist names are whitespace-normalised and ' & ' spacing standardised. Popularity of 0 is treated as a missing score "
                   "(it would otherwise distort averages). When two snapshots share a date, the latest one is kept.")

    with st.container(border=True):
        st.markdown("### Export")
        e = st.columns(3)
        e[0].download_button("⬇ Filtered data", df.drop(columns=["bucket"]).to_csv(index=False), "filtered_chart_data.csv", "text/csv", width="stretch")
        e[1].download_button("⬇ Song metrics", sm.to_csv(index=False), "song_metrics.csv", "text/csv", width="stretch")
        e[2].download_button("⬇ Artist metrics", am.to_csv(index=False), "artist_metrics.csv", "text/csv", width="stretch")
        with st.expander("Preview filtered data"):
            st.dataframe(df.drop(columns=["bucket", "song_key"]).head(500), width="stretch", hide_index=True,
                         column_config={"album_cover_url": st.column_config.ImageColumn("Cover")})
