"""
QuakeMonitor 2.0 — Global Earthquake Analysis Platform
========================================================
Data: USGS Earthquake Catalog
Focus: Japan seismic hazard analysis for civil engineering research
Target: Graduate school application portfolio (earthquake engineering)

Author: MuYu (沐雨)
Version: 2.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scipy import stats

# ─── Page Config ───
st.set_page_config(
    page_title="QuakeMonitor 2.0",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Language ───
LANG = {
        "ja": {
        "title": "🌏 QuakeMonitor 2.0 — グローバル地震観測・解析プラットフォーム",
        "subtitle": "データ: USGS | 焦点: 日本地震ハザード | 用途: 地震工学研究",
        "region": "地域",
        "global": "🌍 全世界",
        "japan": "🇯🇵 日本",
        "japan_trench": "🌊 日本海溝",
        "nankai": "🔥 南海トラフ",
        "kanto": "🏙️ 関東",
        "kansai": "🏯 関西",
        "kyushu": "🌋 九州",
        "tohoku": "🏔️ 東北",
        "hokkaido": "❄️ 北海道",
        "custom": "✏️ カスタム",
        "time_range": "期間",
        "min_mag": "最小マグニチュード",
        "refresh": "🔄 更新",
        "total": "📊 総地震数",
        "max_mag": "📈 最大マグニチュード",
        "energy": "⚡ 放出エネルギー",
        "avg_depth": "📉 平均深さ",
        "deepest": "⬇️ 最深",
        "tabs_timeline": "📈 時系列",
        "tabs_heatmap": "🗺️ 震央分布",
        "tabs_stats": "📊 統計",
        "tabs_bvalue": "📐 G-R則(b値)",
        "tabs_cross": "🔬 深度断面",
        "tabs_data": "📋 データ",
        "m6_alert": "📢 M6+速報",
        "about": "ℹ️ 本サイトについて",
        "export": "📥 CSV出力",
        "lang_toggle": "中文",
    },"zh": {
        "title": "🌏 QuakeMonitor 2.0 — 全球地震监测与工程分析平台",
        "subtitle": "数据: USGS | 焦點: 日本地震危险性分析 | 用途: 土木工程·抗震方向研究",
        "region": "快速区域",
        "global": "🌍 全球",
        "japan": "🇯🇵 日本",
        "japan_trench": "🌊 日本海沟",
        "nankai": "🔥 南海海槽",
        "kanto": "🏙️ 关东",
        "kansai": "🏯 关西",
        "kyushu": "🌋 九州",
        "tohoku": "🏔️ 东北",
        "hokkaido": "❄️ 北海道",
        "custom": "✏️ 自定义",
        "time_range": "时间范围",
        "min_mag": "最小震级",
        "refresh": "🔄 刷新数据",
        "total": "📊 地震总数",
        "max_mag": "📈 最大震级",
        "energy": "⚡ 释放能量",
        "avg_depth": "📉 平均深度",
        "deepest": "⬇️ 最深地震",
        "tabs_timeline": "📈 时间趋势",
        "tabs_heatmap": "🗺️ 震中分布",
        "tabs_stats": "📊 统计分析",
        "tabs_bvalue": "📐 GR定律(b值)",
        "tabs_cross": "🔬 深度剖面",
        "tabs_data": "📋 数据浏览",
        "m6_alert": "📢 最新 M6+ 速报",
        "about": "ℹ️ 关于本站",
        "export": "📥 导出 CSV",
        "lang_toggle": "English",
    },
    "en": {
        "title": "🌏 QuakeMonitor 2.0 — Global Earthquake Analysis Platform",
        "subtitle": "Data: USGS | Focus: Japan Seismic Hazard | Application: Earthquake Engineering Research",
        "region": "Region",
        "global": "🌍 Global",
        "japan": "🇯🇵 Japan",
        "japan_trench": "🌊 Japan Trench",
        "nankai": "🔥 Nankai Trough",
        "kanto": "🏙️ Kanto",
        "kansai": "🏯 Kansai",
        "kyushu": "🌋 Kyushu",
        "tohoku": "🏔️ Tohoku",
        "hokkaido": "❄️ Hokkaido",
        "custom": "✏️ Custom",
        "time_range": "Time Range",
        "min_mag": "Min Magnitude",
        "refresh": "🔄 Refresh",
        "total": "📊 Total Events",
        "max_mag": "📈 Max Magnitude",
        "energy": "⚡ Energy Released",
        "avg_depth": "📉 Avg Depth",
        "deepest": "⬇️ Deepest",
        "tabs_timeline": "📈 Timeline",
        "tabs_heatmap": "🗺️ Epicenter Map",
        "tabs_stats": "📊 Statistics",
        "tabs_bvalue": "📐 G-R Law (b-value)",
        "tabs_cross": "🔬 Depth Cross-Section",
        "tabs_data": "📋 Data",
        "m6_alert": "📢 Recent M6+ Alerts",
        "about": "ℹ️ About",
        "export": "📥 Export CSV",
        "lang_toggle": "中文",
    }
}

# Language state
if "lang" not in st.session_state:
    st.session_state.lang = "zh"

# Toggle button in sidebar top
col_lang = st.sidebar.empty()

def t(key):
    return LANG[st.session_state.lang].get(key, key)

# ─── Font ───
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_style("whitegrid")

# ─── Region Presets ───
REGION_PRESETS = {
    "🌍 Global": {"min_lat": -90, "max_lat": 90, "min_lon": -180, "max_lon": 180},
    "🇯🇵 Japan": {"min_lat": 24, "max_lat": 46, "min_lon": 122, "max_lon": 149},
    "🌊 Japan Trench": {"min_lat": 35, "max_lat": 43, "min_lon": 140, "max_lon": 146},
    "🔥 Nankai Trough": {"min_lat": 30, "max_lat": 36, "min_lon": 132, "max_lon": 139},
    "🏙️ Kanto": {"min_lat": 34.5, "max_lat": 36.5, "min_lon": 138.5, "max_lon": 141},
    "🏯 Kansai": {"min_lat": 34, "max_lat": 35.5, "min_lon": 134.5, "max_lon": 136.5},
    "🌋 Kyushu": {"min_lat": 30, "max_lat": 34, "min_lon": 129, "max_lon": 133},
    "🏔️ Tohoku": {"min_lat": 37, "max_lat": 41.5, "min_lon": 139, "max_lon": 143},
    "❄️ Hokkaido": {"min_lat": 41, "max_lat": 46, "min_lon": 139, "max_lon": 148},
    "✏️ Custom": None,
}

# Historical Japan megaquakes
JP_MEGAQUAKES = [
    {"name": "2011 Tohoku M9.1", "lat": 38.30, "lon": 142.37, "mag": 9.1, "year": 2011},
    {"name": "1995 Kobe M6.9", "lat": 34.58, "lon": 135.02, "mag": 6.9, "year": 1995},
    {"name": "2016 Kumamoto M7.0", "lat": 32.78, "lon": 130.73, "mag": 7.0, "year": 2016},
    {"name": "2004 Chuetsu M6.6", "lat": 37.29, "lon": 138.87, "mag": 6.6, "year": 2004},
    {"name": "2003 Tokachi-oki M8.0", "lat": 41.78, "lon": 143.86, "mag": 8.0, "year": 2003},
]

# ─── Data Fetching ───
@st.cache_data(ttl=600)
def fetch_quakes(min_magnitude=2.5, limit=20000, days_back=30,
                 min_lat=-90, max_lat=90, min_lon=-180, max_lon=180):
    """Fetch from USGS Earthquake Catalog"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minlatitude": min_lat, "maxlatitude": max_lat,
        "minlongitude": min_lon, "maxlongitude": max_lon,
        "minmagnitude": min_magnitude,
        "orderby": "time", "limit": limit,
    }
    resp = requests.get(url, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    records = []
    for q in features:
        props = q.get("properties", {})
        geom = q.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])
        time_ms = props.get("time", 0)
        dt = datetime.fromtimestamp(time_ms / 1000, timezone.utc) if time_ms else None
        depth = coords[2]
        if depth is not None and depth < 0:
            depth = None
        mag = props.get("mag")
        records.append({
            "time": dt,
            "mag": round(mag, 1) if mag else None,
            "depth_km": round(depth, 1) if depth is not None else None,
            "lon": round(coords[0], 4) if coords[0] is not None else None,
            "lat": round(coords[1], 4) if coords[1] is not None else None,
            "place": props.get("place", ""),
            "type": props.get("type", ""),
            "tsunami": "⚠️ YES" if props.get("tsunami", 0) > 0 else "No",
            "url": props.get("url", ""),
        })
    return pd.DataFrame(records)

# ─── Energy Calculation ───
def seismic_energy(magnitude):
    """Gutenberg-Richter energy: log10(E) = 4.8 + 1.5*M (E in Joules)"""
    return 10 ** (4.8 + 1.5 * magnitude)

def format_energy(joules):
    if joules >= 1e18:
        return f"{joules/1e18:.2f} EJ"
    elif joules >= 1e15:
        return f"{joules/1e15:.2f} PJ"
    elif joules >= 1e12:
        return f"{joules/1e12:.2f} TJ"
    else:
        return f"{joules/1e9:.2f} GJ"

# ─── Gutenberg-Richter b-value ───
def compute_bvalue(magnitudes, mc=2.5):
    """Compute b-value using Maximum Likelihood method (Aki 1965)"""
    mags = magnitudes[magnitudes >= mc]
    if len(mags) < 20:
        return None, None
    b = np.log10(np.e) / (mags.mean() - mc)
    # Standard error
    se = b / np.sqrt(len(mags))
    return round(b, 2), round(se, 2)

# ─── Plots ───
def plot_timeline(df):
    """Enhanced timeline with depth coloring"""
    fig, ax = plt.subplots(figsize=(14, 5))
    depths = df["depth_km"].fillna(df["depth_km"].median()).values
    scatter = ax.scatter(df["time"], df["mag"], c=depths, cmap="turbo_r",
                         s=np.clip(df["mag"]**3, 5, 800), alpha=0.55, edgecolors="none")
    cbar = plt.colorbar(scatter, ax=ax, label="Depth (km)")
    cbar.ax.invert_yaxis()
    for _, row in df[df["mag"] >= 7.0].iterrows():
        label = str(row["place"]).split("of ")[-1].split(",")[0].strip()[:25] if pd.notna(row["place"]) else ""
        if label:
            ax.annotate(label, (row["time"], row["mag"]), fontsize=7, alpha=0.75,
                        xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Magnitude (M)")
    ax.set_title("Earthquake Activity Timeline", fontsize=15, fontweight="bold")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig

def plot_japan_heatmap(df):
    """Japan-focused epicenter map with megaquake markers"""
    fig, ax = plt.subplots(figsize=(14, 12))
    h = ax.hist2d(df["lon"], df["lat"], bins=(80, 60), cmap="YlOrRd", alpha=0.9)
    plt.colorbar(h[3], ax=ax, label="Event Count", shrink=0.75)
    # Mark historical megaquakes
    for eq in JP_MEGAQUAKES:
        ax.plot(eq["lon"], eq["lat"], "X", color="darkred", markersize=12, markeredgewidth=2,
                markeredgecolor="white", zorder=5)
        ax.annotate(eq["name"], (eq["lon"], eq["lat"]), fontsize=7, color="darkred",
                    xytext=(8, 8), textcoords="offset points", fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Japan Epicenter Distribution & Historical Megaquakes", fontsize=14, fontweight="bold")
    # Plate boundary labels
    ax.axhline(y=37, color="gray", linestyle="--", alpha=0.3)
    ax.text(149, 37, "Japan Trench", fontsize=8, alpha=0.5, ha="right")
    ax.axhline(y=33, color="gray", linestyle="--", alpha=0.3)
    ax.text(132, 33, "Nankai", fontsize=8, alpha=0.5, ha="left")
    fig.tight_layout()
    return fig

def plot_bvalue(magnitudes, mc=2.5):
    """Gutenberg-Richter frequency-magnitude distribution"""
    fig, ax = plt.subplots(figsize=(10, 6))
    mags = magnitudes[magnitudes >= mc]
    if len(mags) < 20:
        ax.text(0.5, 0.5, "Insufficient data for b-value analysis", transform=ax.transAxes, ha="center")
        return fig
    bins = np.arange(mc, mags.max() + 0.3, 0.2)
    hist, edges = np.histogram(mags, bins=bins)
    cum_hist = np.cumsum(hist[::-1])[::-1]  # Cumulative from right
    centers = (edges[:-1] + edges[1:]) / 2
    valid = cum_hist > 0
    ax.semilogy(centers[valid], cum_hist[valid], "o-", color="steelblue", markersize=6, label="Cumulative (Observed)")
    # Fit G-R
    slope, intercept, r_value, _, _ = stats.linregress(centers[valid], np.log10(cum_hist[valid]))
    b_val = round(-slope, 2)
    ax.semilogy(centers[valid], 10**(intercept + slope * centers[valid]), "r--",
                linewidth=2, label=f"G-R Fit: b = {b_val}")
    ax.set_xlabel("Magnitude (M)")
    ax.set_ylabel("Cumulative Number ≥ M")
    ax.set_title(f"Gutenberg-Richter Law (Mc={mc})", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig, b_val

def plot_depth_cross_section(df, lat_range=None):
    """Depth cross-section along latitude (subduction zone view)"""
    fig, ax = plt.subplots(figsize=(14, 5))
    valid = df.dropna(subset=["depth_km", "lat"])
    if lat_range:
        valid = valid[(valid["lat"] >= lat_range[0]) & (valid["lat"] <= lat_range[1])]
    scatter = ax.scatter(valid["lat"], valid["depth_km"], c=valid["mag"], cmap="plasma",
                         s=np.clip(valid["mag"]**2.5, 10, 500), alpha=0.6, edgecolors="none")
    cbar = plt.colorbar(scatter, ax=ax, label="Magnitude")
    ax.invert_yaxis()
    ax.set_xlabel("Latitude (°)")
    ax.set_ylabel("Depth (km)")
    ax.set_title("Depth Cross-Section (Latitude vs Depth)", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig

def plot_daily_trend(df):
    """Daily event frequency"""
    fig, ax = plt.subplots(figsize=(14, 4))
    df["date"] = df["time"].dt.date
    daily = df.groupby("date").size()
    ax.fill_between(pd.to_datetime(daily.index), daily.values, alpha=0.3, color="steelblue")
    ax.plot(pd.to_datetime(daily.index), daily.values, color="steelblue", linewidth=1)
    ax.set_xlabel("Date")
    ax.set_ylabel("Events per day")
    ax.set_title("Daily Earthquake Frequency", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig

def plot_magnitude_histogram(df):
    """Magnitude distribution histogram"""
    fig, ax = plt.subplots(figsize=(10, 5))
    valid = df["mag"].dropna()
    ax.hist(valid, bins=40, color="steelblue", edgecolor="white", alpha=0.85)
    ax.axvline(valid.median(), color="crimson", linestyle="--", linewidth=1.5,
               label=f"Median: M{valid.median():.1f}")
    ax.axvline(7.0, color="darkred", linestyle=":", linewidth=1, label="M7.0 threshold")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Count")
    ax.set_title("Magnitude Distribution", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    return fig

# ═══════════════ UI ═══════════════

# Language toggle (3-way: ZH -> JA -> EN -> ZH)
with st.sidebar:
    lang_btn = st.button(t("lang_toggle"), use_container_width=True)
    if lang_btn:
        cycle = {"zh": "ja", "ja": "en", "en": "zh"}
        st.session_state.lang = cycle[st.session_state.lang]
        st.rerun()

# Header
st.title(t("title"))
st.caption(t("subtitle"))

# Sidebar controls
with st.sidebar:
    st.header(f"🔬 {t('region')}")
    region = st.selectbox(t("region"), list(REGION_PRESETS.keys()), index=1)  # Default: Japan
    if region == "✏️ Custom":
        col_a, col_b = st.columns(2)
        lat_min = col_a.number_input("South Lat", -90.0, 90.0, 24.0)
        lat_max = col_b.number_input("North Lat", -90.0, 90.0, 46.0)
        lon_min = col_a.number_input("West Lon", -180.0, 180.0, 122.0)
        lon_max = col_b.number_input("East Lon", -180.0, 180.0, 149.0)
    else:
        preset = REGION_PRESETS[region]
        lat_min, lat_max = preset["min_lat"], preset["max_lat"]
        lon_min, lon_max = preset["min_lon"], preset["max_lon"]
        st.caption(f"Lat {lat_min}°~{lat_max}° | Lon {lon_min}°~{lon_max}°")

    st.divider()
    time_range = st.selectbox(t("time_range"),
        ["Past 24h", "Past 7 days", "Past 30 days", "Past 1 year", "Past 10 years"],
        index=2)
    days_map = {"Past 24h": 1, "Past 7 days": 7, "Past 30 days": 30, "Past 1 year": 365, "Past 10 years": 3650}
    days_back = days_map[time_range]
    min_mag = st.slider(t("min_mag"), 0.0, 6.0, 2.5, 0.5)
    st.divider()
    refresh = st.button(t("refresh"), use_container_width=True)

# ─── Load ───
if refresh:
    st.cache_data.clear()

with st.spinner("Fetching from USGS Earthquake Catalog..."):
    try:
        df = fetch_quakes(min_magnitude=min_mag, days_back=days_back,
                          min_lat=lat_min, max_lat=lat_max,
                          min_lon=lon_min, max_lon=lon_max)
        load_error = False
    except Exception as e:
        st.error(f"Data fetch failed: {e}")
        df = pd.DataFrame()
        load_error = True

# ─── Metrics ───
if not df.empty:
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    total_energy = df["mag"].dropna().apply(seismic_energy).sum()
    c1.metric(t("total"), f"{len(df):,}")
    c2.metric(t("max_mag"), f"M{df['mag'].max():.1f}")
    c3.metric(t("energy"), format_energy(total_energy))
    c4.metric(t("avg_depth"), f"{df['depth_km'].mean():.0f} km" if df["depth_km"].notna().any() else "N/A")
    c5.metric(t("deepest"), f"{df['depth_km'].max():.0f} km" if df["depth_km"].notna().any() else "N/A")

    if len(df) >= 20000:
        st.warning("⚠️ Data capped at 20,000 records. Narrow time/magnitude range for precision.")

    # ─── Tabs ───
    tabs = st.tabs([t("tabs_timeline"), t("tabs_heatmap"), t("tabs_stats"),
                    t("tabs_bvalue"), t("tabs_cross"), t("tabs_data")])

    with tabs[0]:
        st.subheader("Earthquake Activity Timeline")
        st.caption("Color = Depth (yellow=shallow → blue=deep) | Size = Magnitude | Labels = M7+")
        if not df.empty:
            st.pyplot(plot_timeline(df))
            st.pyplot(plot_daily_trend(df))

    with tabs[1]:
        st.subheader("Epicenter Distribution")
        if region.startswith("🇯🇵"):
            st.pyplot(plot_japan_heatmap(df))
        else:
            st.caption("Japan region selected to show megaquake markers")
            st.pyplot(plot_timeline(df))

    with tabs[2]:
        st.subheader("Statistical Analysis")
        if not df.empty:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.pyplot(plot_magnitude_histogram(df))
            with col_s2:
                valid_depths = df["depth_km"].dropna()
                if len(valid_depths) > 0:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.hist(valid_depths, bins=50, color="coral", edgecolor="white", alpha=0.85)
                    ax.axvline(valid_depths.median(), color="navy", linestyle="--",
                               label=f"Median: {valid_depths.median():.0f} km")
                    ax.set_xlabel("Depth (km)")
                    ax.set_ylabel("Count")
                    ax.set_title("Depth Distribution", fontweight="bold")
                    ax.legend()
                    ax.invert_xaxis()
                    fig.tight_layout()
                    st.pyplot(fig)

            # Summary stats
            mags = df["mag"].dropna()
            st.markdown(f"""
            **Magnitude Summary**  
            Min: M{mags.min():.1f} | Q1: M{mags.quantile(0.25):.1f} | Median: M{mags.median():.1f}  
            Q3: M{mags.quantile(0.75):.1f} | Max: M{mags.max():.1f} | Std: {mags.std():.2f}  
            M≥5: {len(mags[mags>=5])} | M≥6: {len(mags[mags>=6])} | M≥7: {len(mags[mags>=7])}
            """)

    with tabs[3]:
        st.subheader("Gutenberg-Richter Law — b-value Analysis")
        mc = st.slider("Magnitude of Completeness (Mc)", 0.0, 5.0, 2.5, 0.1, key="mc_slider")
        mags = df["mag"].dropna()
        if len(mags[mags >= mc]) >= 20:
            fig, b_val = plot_bvalue(mags, mc)
            st.pyplot(fig)
            st.markdown(f"""
            **b-value analysis**:  
            - b = **{b_val}** (global average ≈ 1.0)  
            - Higher b → more small quakes relative to large ones (volcanic/swarm activity)  
            - Lower b → higher proportion of large events (stress accumulation)  
            - This metric is critical for seismic hazard assessment in Japan.
            """)
        else:
            st.warning("Insufficient data for reliable b-value estimation. Try a larger time range or lower Mc.")

    with tabs[4]:
        st.subheader("Depth Cross-Section")
        st.caption("Latitude vs Depth — reveals subduction zone geometry")
        valid = df.dropna(subset=["depth_km", "lat"])
        if len(valid) > 10:
            lat_min_v = float(valid["lat"].min())
            lat_max_v = float(valid["lat"].max())
            lat_range = st.slider("Latitude range", lat_min_v, lat_max_v, (lat_min_v, lat_max_v))
            st.pyplot(plot_depth_cross_section(df, lat_range))
        else:
            st.info("Not enough depth data for cross-section view.")

    with tabs[5]:
            # ─── Engineering Impact Ranking ───
    st.subheader("🏗️ Engineering Impact Ranking")
    st.caption("Sorted by estimated JMA intensity, not magnitude. This is what civil engineers care about.")
    valid_eng = df.dropna(subset=["mag", "depth_km", "lat", "lon"]).copy()
    if len(valid_eng) > 0:
        # Calculate distance to nearest city for each quake
        cities_data = []
        for _, row in valid_eng.iterrows():
            city, dist = nearest_city(row["lat"], row["lon"])
            jma, jma_str, _ = estimate_jma_intensity(row["mag"], row["depth_km"], dist)
            pga, pga_str, _ = estimate_pga_gal(row["mag"], dist, row["depth_km"])
            cities_data.append({
                "time": row["time"], "mag": row["mag"], "depth_km": row["depth_km"],
                "place": row["place"], "nearest_city": city, "dist_km": dist,
                "jma": jma, "jma_str": jma_str, "pga_gal": pga,
                "tsunami": row["tsunami"]
            })
        eng_df = pd.DataFrame(cities_data).sort_values("jma", ascending=False, na_position="last").head(20)
        st.dataframe(eng_df[[
            "time", "mag", "jma_str", "nearest_city", "dist_km", "pga_gal", "depth_km", "place", "tsunami"
        ]].rename(columns={
            "time": "Time (UTC)", "mag": "Magnitude", "jma_str": "JMA Intensity",
            "nearest_city": "Nearest City", "dist_km": "Distance (km)",
            "pga_gal": "PGA (gal)", "depth_km": "Depth (km)", "place": "Location"
        }), hide_index=True, use_container_width=True)
        st.caption("*JMA intensity estimated via attenuation formula. PGA via simplified GMPE. For reference only.")
    else:
        st.info("No data available for engineering analysis.")

    st.divider()
    st.subheader("Raw Data Browser")
        st.caption("Sort, search, filter, export")
        if not df.empty:
            display_cols = ["time", "mag", "depth_km", "lat", "lon", "place", "tsunami", "url"]
            st.dataframe(
                df[display_cols].sort_values("time", ascending=False),
                column_config={
                    "time": st.column_config.DatetimeColumn("Time (UTC)", format="YYYY-MM-DD HH:mm"),
                    "url": st.column_config.LinkColumn("USGS Detail"),
                },
                hide_index=True, use_container_width=True, height=500,
            )
            csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(t("export"), csv,
                f"earthquake_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv", use_container_width=True)

    # ─── M6+ Alerts ───
    st.divider()
    st.subheader(t("m6_alert"))
    major = df[df["mag"] >= 6.0].sort_values("time", ascending=False).head(10)
    if not major.empty:
        st.caption("震级(M) | 震度(JMA) | 最近城市 | PGA估算 | 工程意义")
        for _, row in major.iterrows():
            emoji = "🔴" if row["mag"] >= 7.0 else "🟠"
            tsunami = " ⚠️TSUNAMI" if "YES" in str(row["tsunami"]) else ""
            city, dist = nearest_city(row["lat"], row["lon"])
            jma, jma_str, jma_col = estimate_jma_intensity(row["mag"], row["depth_km"], dist)
            pga, pga_str, pga_col = estimate_pga_gal(row["mag"], dist, row["depth_km"])
            context = engineering_context(row["mag"], row["depth_km"], dist)
            
            # Color-coded badge
            jma_badge = f"<span style='background:{jma_col};color:white;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:bold'>{jma_str}</span>"
            
            st.markdown(
                f"{emoji} **M{row['mag']:.1f}** | "
                f"震度 {jma_badge} | "
                f"距{city} {dist:.0f}km | "
                f"PGA {pga:.0f} gal | "
                f"{context[:120]}..."
                f"{tsunami}"
                f"  _{row['time'].strftime('%Y-%m-%d %H:%M UTC')}_",
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════
# ENGINEERING UTILITIES — Real analysis tools
# ═══════════════════════════════════════════════

# Japanese major cities (for distance calculation)
JP_CITIES = {
    "Tokyo": (35.68, 139.76), "Osaka": (34.69, 135.50),
    "Nagoya": (35.18, 136.90), "Fukuoka": (33.59, 130.40),
    "Sapporo": (43.06, 141.35), "Sendai": (38.27, 140.87),
    "Hiroshima": (34.39, 132.46), "Kobe": (34.69, 135.20),
    "Kyoto": (35.01, 135.77), "Naha": (26.21, 127.68),
}

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points (km)"""
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def nearest_city(lat, lon):
    """Find nearest Japanese city and distance"""
    best_city, best_dist = None, float("inf")
    for city, (clat, clon) in JP_CITIES.items():
        d = haversine_km(lat, lon, clat, clon)
        if d < best_dist:
            best_dist, best_city = d, city
    return best_city, round(best_dist, 0)

def estimate_jma_intensity(mag, depth_km, dist_km):
    """Estimate JMA seismic intensity (震度) using simplified empirical formula.
    Based on Matsuoka and Midorikawa (1994) with adjustments.
    Returns: (intensity_float, intensity_str, color_class)
    """
    if depth_km is None or dist_km is None or mag is None:
        return None, "N/A", "#888"
    # Simplified attenuation: I = mag - log10(dist) - 0.0015*dist - 0.005*depth + 1.5
    i_float = mag - np.log10(max(dist_km, 1)) - 0.0015 * dist_km - 0.005 * depth_km + 1.5
    i_float = max(0, min(7, i_float))
    # Map to JMA scale labels (0-7)
    labels = {0: "0", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5弱", 6: "5強", 7: "6弱以上"}
    colors = {0: "#4CAF50", 1: "#8BC34A", 2: "#FFC107", 3: "#FF9800", 4: "#F44336", 5: "#E91E63", 6: "#9C27B0", 7: "#7B1FA2"}
    idx = min(int(i_float), 7)
    return round(i_float, 1), labels[idx], colors[idx]

def estimate_pga_gal(mag, dist_km, depth_km=None):
    """Simple PGA estimation (gal = cm/s^2) using Joyner-Boore type attenuation.
    log10(PGA) = 0.43*M - log10(R) - 0.0027*R + 1.3
    where R = sqrt(dist^2 + h^2), h is focal depth proxy.
    Returns: (pga_gal, category_str, hazard_color)
    """
    if mag is None or dist_km is None:
        return None, "N/A", "#888"
    h = max(depth_km, 8) if depth_km else 10
    R = np.sqrt(dist_km**2 + h**2)
    log_pga = 0.43 * mag - np.log10(max(R, 1)) - 0.0027 * R + 1.3
    pga = 10 ** log_pga  # gal (cm/s2)
    if pga < 1: cat, col = "Negligible (<1 gal)", "#4CAF50"
    elif pga < 10: cat, col = "Light (1-10 gal)", "#8BC34A"
    elif pga < 80: cat, col = "Moderate (10-80 gal)", "#FFC107"
    elif pga < 250: cat, col = "Strong (80-250 gal)", "#FF9800"
    elif pga < 400: cat, col = f"Very Strong ({pga:.0f} gal)", "#F44336"
    else: cat, col = f"Severe ({pga:.0f} gal)", "#9C27B0"
    return round(pga, 1), cat, col

# Engineering insight for each magnitude range
def engineering_context(mag, depth_km, dist_km):
    """Provide engineering significance of an earthquake"""
    if mag is None: return ""
    jma, jma_str, _ = estimate_jma_intensity(mag, depth_km, dist_km)
    pga, pga_str, _ = estimate_pga_gal(mag, dist_km, depth_km)
    insights = []
    if mag >= 9.0: insights.append("Giant earthquake. Can trigger tsunamis >10m. Building codes test for this level.")
    elif mag >= 8.0: insights.append("Great earthquake. Subduction zone megathrust events. Key for seismic design spectra.")
    elif mag >= 7.0: insights.append("Major earthquake. Can cause severe damage near epicenter. Requires ductile design.")
    elif mag >= 6.0: insights.append("Strong earthquake. Damage potential in populated areas. Equivalent to design-basis earthquake.")
    elif mag >= 5.0: insights.append("Moderate earthquake. Usually felt but minor damage. Useful for seismicity analysis.")
    else: insights.append("Small earthquake. Important for b-value statistics and background seismicity.")
    
    if depth_km and depth_km <= 70:
        insights.append(f"Shallow crustal ({depth_km:.0f}km). Higher damage potential at surface.")
    elif depth_km and depth_km > 300:
        insights.append(f"Deep focus ({depth_km:.0f}km). Low surface shaking despite high magnitude.")
    
    if dist_km and dist_km <= 50:
        insights.append(f"Near-field ({dist_km:.0f}km from city). Peak ground acceleration is a key concern.")
    
    return " ".join(insights)
# ─── About ───
st.divider()
with st.expander(t("about")):
    lang = st.session_state.lang
    if lang == "zh":
        st.markdown("""
        ### QuakeMonitor 2.0 — 全球地震监测与工程分析平台

        **开发动机**  
        本平台为土木工程抗震方向研究而建。日本位于环太平洋地震带上,是全球地震活动最频繁的国家之一。
        理解和分析地震数据是地震工程研究的基础。

        **技术栈**  
        - 数据源: USGS Earthquake Catalog (FDSN API)
        - 前端: Streamlit
        - 分析: NumPy, SciPy, Pandas
        - 可视化: Matplotlib, Seaborn
        - G-R b值: 最大似然法 (Aki, 1965)

        **学术价值**  
        - Gutenberg-Richter b值分析 — 地震危险性评估核心参数
        - 深度剖面 — 俯冲带几何结构可视化
        - 能量释放计算 — 基于 Kanamori (1977)
        - 日本历史大震标注 — 2011東北、1995阪神等

        **作者**: 沐雨  
        **研究方向**: 地震工学 · 耐震設計  
        **联系**: GitHub Issues
        """)
    elif lang == "ja":
        st.markdown("""
        ### QuakeMonitor 2.0 — グローバル地震観測・解析プラットフォーム

        **開発動機**  
        本プラットフォームは地震工学研究のために構築されました。日本は環太平洋造山帯に位置し、
        世界で最も地震活動が活発な国の一つです。地震データの理解と分析は、
        地震ハザード評価の基礎となります。

        **技術スタック**  
        - データソース: USGS Earthquake Catalog (FDSN API)
        - フロントエンド: Streamlit
        - 解析: NumPy, SciPy, Pandas
        - 可視化: Matplotlib, Seaborn
        - b値: 最尤法 (Aki, 1965)

        **主な機能**  
        - Gutenberg-Richter b値解析 — 地震ハザード評価の核心パラメータ
        - 深度断面図 — 沈み込み帯の幾何学構造の可視化
        - エネルギー解放量 — Kanamori (1977) に基づく
        - 日本歴史的巨大地震マーカー — 2011年東北地方太平洋沖地震、1995年阪神・淡路大震災など

        **著者**: MuYu (沐雨)  
        **研究分野**: 地震工学 · 耐震設計  
        **連絡先**: GitHub Issues
        """)

    else:
        st.markdown("""
        ### QuakeMonitor 2.0 — Global Earthquake Analysis Platform

        **Motivation**  
        Built for earthquake engineering research. Japan sits on the Pacific Ring of Fire,
        making it one of the most seismically active countries. Understanding and analyzing
        earthquake data is fundamental to seismic hazard assessment.

        **Tech Stack**  
        - Data: USGS Earthquake Catalog (FDSN API)
        - Frontend: Streamlit
        - Analysis: NumPy, SciPy, Pandas
        - Visualization: Matplotlib, Seaborn
        - b-value: Maximum Likelihood (Aki, 1965)

        **Key Features**  
        - Gutenberg-Richter b-value — core seismic hazard parameter
        - Depth cross-section — subduction zone geometry visualization
        - Energy release — based on Kanamori (1977)
        - Historical megaquake markers — 2011 Tohoku, 1995 Kobe, etc.

        **Author**: MuYu  
        **Research Interest**: Earthquake Engineering · Seismic Design  
        **Contact**: GitHub Issues
        """)

st.caption("— MuYu (沐雨)")





