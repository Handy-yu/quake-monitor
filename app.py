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
from quake_analysis import compute_bvalue, seismic_energy, format_energy
import time
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
        "lang_toggle": "English",
        "fetching": 'USGS から地震データを取得中…',
        "cap_warning": '⚠️ データは 20,000 件で打ち切られました。期間・マグニチュードを絞ってください。',
        "timeline_title": '📈 地震活動タイムライン',
        "timeline_caption": '色 = 深さ（黄=浅 → 青=深）| 大きさ = マグニチュード | ラベル = M7+',
        "heatmap_title": '🗺️ 震央分布',
        "heatmap_caption": '日本地域を選択すると歴史的大地震マーカーを表示',
        "stats_title": '📊 統計分析',
        "mag_summary": '**マグニチュード概要**  \n最小: M{mn:.1f} | Q1: M{q1:.1f} | 中央値: M{md:.1f}  \nQ3: M{q3:.1f} | 最大: M{mx:.1f} | 標準偏差: {sd:.2f}  \nM≥5: {g5} | M≥6: {g6} | M≥7: {g7}',
        "bvalue_title": '📐 G-R則(b値) 解析',
        "mc_label": '完全性マグニチュード (Mc)',
        "bvalue_insufficient": '⚠️ b値の推定にはデータが不足しています。期間を広げるか Mc を下げてください。',
        "bvalue_notes": '**b値分析**：  \n- b = **{b}**（世界平均 ≈ 1.0）  \n- b値が高い → 小さな地震の割合が高い（火山・群発活動）  \n- b値が低い → 大きな地震の割合が高い（応力蓄積）  \n- 日本の地震ハザード評価に重要な指標です。',
        "cross_title": '🔬 深度断面',
        "cross_caption": '緯度 vs 深さ — 沈み込み帯の幾何学構造',
        "lat_range": '緯度範囲',
        "cross_insufficient": 'ℹ️ 断面図を表示するための深さデータが不足しています。',
        "eng_title": '🏗️ 工学的影響ランキング',
        "eng_caption": '推定 JMA 震度でソート（マグニチュード順ではない）。土木技術者が注目する指標です。',
        "eng_footnote": '*JMA震度は減衰式による推定、PGA は簡易 GMPE による推定です。参考値です。',
        "eng_empty": 'ℹ️ 工学的分析に利用できるデータがありません。',
        "raw_title": '📋 データ閲覧',
        "raw_caption": '並べ替え・検索・フィルター・エクスポート',
        "col_time": '時刻 (UTC)',
        "col_mag": 'マグニチュード',
        "col_jma": 'JMA震度',
        "col_city": '最寄り都市',
        "col_dist": '距離 (km)',
        "col_pga": 'PGA (gal)',
        "col_depth": '深さ (km)',
        "col_place": '場所',
        "col_usgs": 'USGS 詳細',
        "m6_caption": 'マグニチュード(M) | 震度(JMA) | 最寄り都市 | PGA推定 | 工学的意義',
        "m6_line": '{emoji} **M{mag:.1f}** | 震度 {intensity} | {city}から {dist:.0f}km | PGA {pga:.0f} gal | {context}{tsunami}  _{time}_',
        "chart_time_x": '時刻(UTC)',
        "chart_mag_x": 'マグニチュード(M)',
        "chart_timeline_title": '地震活動タイムライン',
        "chart_lon": '経度',
        "chart_lat": '緯度',
        "chart_heatmap_title": '日本の震央分布と歴史的大地震',
        "chart_cum_y": '累積数 ≥ M',
        "chart_bvalue_title": 'G-R則 (Mc={mc})',
        "chart_lat_deg": '緯度(°)',
        "chart_depth_y": '深さ(km)',
        "chart_cross_title": '深度断面（緯度 vs 深さ）',
        "chart_date": '日付',
        "chart_events_day": '1日あたりのイベント数',
        "chart_daily_title": '日別地震頻度',
        "chart_count": '数',
        "chart_hist_title": 'マグニチュード分布',
        "median_fmt": '中央値: {0:.0f} km',
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
        "lang_toggle": "日本語",
        "fetching": '正在从 USGS 获取地震数据…',
        "cap_warning": '⚠️ 数据已达 20,000 条上限。缩小时间/震级范围以获得更高精度。',
        "timeline_title": '📈 地震活动时间线',
        "timeline_caption": '颜色 = 深度（黄=浅 → 蓝=深）| 大小 = 震级 | 标注 = M7+',
        "heatmap_title": '🗺️ 震中分布',
        "heatmap_caption": '选择日本区域以显示历史大地震标记',
        "stats_title": '📊 统计分析',
        "mag_summary": '**震级摘要**  \n最小: M{mn:.1f} | Q1: M{q1:.1f} | 中位数: M{md:.1f}  \nQ3: M{q3:.1f} | 最大: M{mx:.1f} | 标准差: {sd:.2f}  \nM≥5: {g5} | M≥6: {g6} | M≥7: {g7}',
        "bvalue_title": '📐 G-R定律(b值) 分析',
        "mc_label": '完整性震级 (Mc)',
        "bvalue_insufficient": '⚠️ 数据不足以可靠估计 b 值。尝试更大的时间范围或更低的 Mc。',
        "bvalue_notes": '**b 值分析**：  \n- b = **{b}**（全球平均值 ≈ 1.0）  \n- b 值越高 → 小地震占比越大（火山/群震活动）  \n- b 值越低 → 大地震占比越高（应力积累）  \n- 该指标对日本地震危险性评估至关重要。',
        "cross_title": '🔬 深度剖面',
        "cross_caption": '纬度 vs 深度——揭示俯冲带几何结构',
        "lat_range": '纬度范围',
        "cross_insufficient": 'ℹ️ 深度数据不足，无法显示剖面图。',
        "eng_title": '🏗️ 工程影响排名',
        "eng_caption": '按估算的 JMA 震度排序，而非震级。这是土木工程师关注的重点。',
        "eng_footnote": '*JMA 震度通过衰减公式估算，PGA 通过简化 GMPE 估算。仅供参考。',
        "eng_empty": 'ℹ️ 无数据可用于工程分析。',
        "raw_title": '📋 数据浏览',
        "raw_caption": '排序、搜索、筛选、导出',
        "col_time": '时间 (UTC)',
        "col_mag": '震级',
        "col_jma": 'JMA 震度',
        "col_city": '最近城市',
        "col_dist": '距离 (km)',
        "col_pga": 'PGA (gal)',
        "col_depth": '深度 (km)',
        "col_place": '位置',
        "col_usgs": 'USGS 详情',
        "m6_caption": '震级(M) | 震度(JMA) | 最近城市 | PGA估算 | 工程意义',
        "m6_line": '{emoji} **M{mag:.1f}** | 震度 {intensity} | 距{city} {dist:.0f}km | PGA {pga:.0f} gal | {context}{tsunami}  _{time}_',
        "chart_time_x": '时间(UTC)',
        "chart_mag_x": '震级(M)',
        "chart_timeline_title": '地震活动时间线',
        "chart_lon": '经度',
        "chart_lat": '纬度',
        "chart_heatmap_title": '日本震中分布与历史大地震',
        "chart_cum_y": '累计数量 ≥ M',
        "chart_bvalue_title": 'G-R定律 (Mc={mc})',
        "chart_lat_deg": '纬度(°)',
        "chart_depth_y": '深度(km)',
        "chart_cross_title": '深度剖面（纬度 vs 深度）',
        "chart_date": '日期',
        "chart_events_day": '每日事件数',
        "chart_daily_title": '每日地震频率',
        "chart_count": '数量',
        "chart_hist_title": '震级分布',
        "median_fmt": '中位数: {0:.0f} km',
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
        "fetching": 'Fetching from USGS Earthquake Catalog...',
        "cap_warning": '⚠️ Data capped at 20,000 records. Narrow time/magnitude range for precision.',
        "timeline_title": '📈 Earthquake Activity Timeline',
        "timeline_caption": 'Color = Depth (yellow=shallow → blue=deep) | Size = Magnitude | Labels = M7+',
        "heatmap_title": '🗺️ Epicenter Distribution',
        "heatmap_caption": 'Japan region selected to show megaquake markers',
        "stats_title": '📊 Statistical Analysis',
        "mag_summary": '**Magnitude Summary**  \nMin: M{mn:.1f} | Q1: M{q1:.1f} | Median: M{md:.1f}  \nQ3: M{q3:.1f} | Max: M{mx:.1f} | Std: {sd:.2f}  \nM≥5: {g5} | M≥6: {g6} | M≥7: {g7}',
        "bvalue_title": '📐 Gutenberg-Richter Law — b-value Analysis',
        "mc_label": 'Magnitude of Completeness (Mc)',
        "bvalue_insufficient": '⚠️ Insufficient data for reliable b-value estimation. Try a larger time range or lower Mc.',
        "bvalue_notes": '**b-value analysis**:  \n- b = **{b}** (global average ≈ 1.0)  \n- Higher b → more small quakes relative to large ones (volcanic/swarm activity)  \n- Lower b → higher proportion of large events (stress accumulation)  \n- This metric is critical for seismic hazard assessment in Japan.',
        "cross_title": '🔬 Depth Cross-Section',
        "cross_caption": 'Latitude vs Depth — reveals subduction zone geometry',
        "lat_range": 'Latitude range',
        "cross_insufficient": 'ℹ️ Not enough depth data for cross-section view.',
        "eng_title": '🏗️ Engineering Impact Ranking',
        "eng_caption": 'Sorted by estimated JMA intensity, not magnitude. This is what civil engineers care about.',
        "eng_footnote": '*JMA intensity estimated via attenuation formula. PGA via simplified GMPE. For reference only.',
        "eng_empty": 'ℹ️ No data available for engineering analysis.',
        "raw_title": '📋 Raw Data Browser',
        "raw_caption": 'Sort, search, filter, export',
        "col_time": 'Time (UTC)',
        "col_mag": 'Magnitude',
        "col_jma": 'JMA Intensity',
        "col_city": 'Nearest City',
        "col_dist": 'Distance (km)',
        "col_pga": 'PGA (gal)',
        "col_depth": 'Depth (km)',
        "col_place": 'Location',
        "col_usgs": 'USGS Detail',
        "m6_caption": 'Magnitude(M) | JMA Intensity | Nearest City | PGA est. | Engineering Meaning',
        "m6_line": '{emoji} **M{mag:.1f}** | JMA {intensity} | {dist:.0f}km from {city} | PGA {pga:.0f} gal | {context}{tsunami}  _{time}_',
        "chart_time_x": 'Time (UTC)',
        "chart_mag_x": 'Magnitude (M)',
        "chart_timeline_title": 'Earthquake Activity Timeline',
        "chart_lon": 'Longitude',
        "chart_lat": 'Latitude',
        "chart_heatmap_title": 'Japan Epicenter Distribution & Historical Megaquakes',
        "chart_cum_y": 'Cumulative Number ≥ M',
        "chart_bvalue_title": 'Gutenberg-Richter Law (Mc={mc})',
        "chart_lat_deg": 'Latitude (°)',
        "chart_depth_y": 'Depth (km)',
        "chart_cross_title": 'Depth Cross-Section (Latitude vs Depth)',
        "chart_date": 'Date',
        "chart_events_day": 'Events per day',
        "chart_daily_title": 'Daily Earthquake Frequency',
        "chart_count": 'Count',
        "chart_hist_title": 'Magnitude Distribution',
        "median_fmt": 'Median: {0:.0f} km',
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
sns.set_style("whitegrid")
plt.rcParams["font.sans-serif"] = ["SimSun", "KaiTi", "Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

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
# ─── Sample data (offline demo fallback) ───
SAMPLE_EVENTS = [
    {"time": "2026-08-11 08:42:00", "mag": 6.2, "depth_km": 35.0, "lat": 35.80, "lon": 140.20, "place": "Near Choshi, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-10 21:15:00", "mag": 5.4, "depth_km": 48.0, "lat": 37.25, "lon": 141.60, "place": "Off the coast of Fukushima, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-09 14:03:00", "mag": 4.8, "depth_km": 60.0, "lat": 38.50, "lon": 142.10, "place": "Near Miyagi, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-08 06:55:00", "mag": 5.1, "depth_km": 20.0, "lat": 33.90, "lon": 132.10, "place": "Iyonada, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-07 23:30:00", "mag": 6.8, "depth_km": 55.0, "lat": 41.20, "lon": 143.50, "place": "Off the coast of Hokkaido, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-06 11:20:00", "mag": 3.9, "depth_km": 25.0, "lat": 35.10, "lon": 136.80, "place": "Aichi, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-05 19:10:00", "mag": 4.2, "depth_km": 70.0, "lat": 39.80, "lon": 139.90, "place": "Akita, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-04 08:05:00", "mag": 5.6, "depth_km": 15.0, "lat": 34.30, "lon": 131.90, "place": "Yamaguchi, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-03 16:44:00", "mag": 7.1, "depth_km": 40.0, "lat": 36.10, "lon": 140.60, "place": "Ibaraki, Japan", "tsunami": "⚠️ YES", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-02 03:30:00", "mag": 4.5, "depth_km": 90.0, "lat": 40.50, "lon": 141.00, "place": "Aomori, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-08-01 12:12:00", "mag": 5.0, "depth_km": 30.0, "lat": 32.80, "lon": 130.90, "place": "Kumamoto, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
    {"time": "2026-07-30 07:18:00", "mag": 4.1, "depth_km": 80.0, "lat": 35.70, "lon": 137.90, "place": "Nagano, Japan", "tsunami": "No", "url": "https://earthquake.usgs.gov"},
]

def sample_df():
    df = pd.DataFrame(SAMPLE_EVENTS)
    df["time"] = pd.to_datetime(df["time"])
    return df

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
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            last_err = None
            break
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    if last_err is not None:
        return sample_df(), "sample"
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
    return pd.DataFrame(records), "live"

# (Energy/analysis functions moved to quake_analysis.py)
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
    ax.set_xlabel(t("chart_time_x"))
    ax.set_ylabel(t("chart_mag_x"))
    ax.set_title(t("chart_timeline_title"), fontsize=15, fontweight="bold")
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
    ax.set_xlabel(t("chart_lon"))
    ax.set_ylabel(t("chart_lat"))
    ax.set_title(t("chart_heatmap_title"), fontsize=14, fontweight="bold")
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
    ax.set_xlabel(t("chart_mag_x"))
    ax.set_ylabel(t("chart_cum_y"))
    ax.set_title(t("chart_bvalue_title").format(mc=mc), fontsize=14, fontweight="bold")
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
    ax.set_xlabel(t("chart_lat_deg"))
    ax.set_ylabel(t("chart_depth_y"))
    ax.set_title(t("chart_cross_title"), fontsize=14, fontweight="bold")
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
    ax.set_xlabel(t("chart_date"))
    ax.set_ylabel(t("chart_events_day"))
    ax.set_title(t("chart_daily_title"), fontsize=13, fontweight="bold")
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
    ax.set_xlabel(t("chart_mag_x"))
    ax.set_ylabel(t("chart_count"))
    ax.set_title(t("chart_hist_title"), fontweight="bold")
    ax.legend()
    fig.tight_layout()
    return fig

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

# ═══════════════ UI ═══════════════

# Language toggle (3-way: ZH -> JA -> EN -> ZH)
with st.sidebar:
    lang_btn = st.button(t("lang_toggle"), width="stretch")
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
    refresh = st.button(t("refresh"), width="stretch")

# ─── Load ───
if refresh:
    st.cache_data.clear()

with st.spinner(t("fetching")):
    data_source = None
    try:
        df, data_source = fetch_quakes(min_magnitude=min_mag, days_back=days_back,
                                       min_lat=lat_min, max_lat=lat_max,
                                       min_lon=lon_min, max_lon=lon_max)
        load_error = False
    except Exception as e:
        st.error(f"❌ 无法连接 USGS 地震数据服务：{e}")
        st.info("可能原因：当前网络无法直连 USGS（大陆直连常不稳定）。建议：① 检查网络或开启代理；② 点击侧边栏「🔄 刷新数据」重试；③ 稍后再试。")
        df = pd.DataFrame()
        load_error = True

if data_source == "sample":
    st.warning("⚠️ USGS 连接失败，当前展示内置示例数据。点击侧边栏「🔄 刷新数据」可重试真实数据。")

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
        st.warning(t("cap_warning"))

    # ─── Tabs ───
    tabs = st.tabs([t("tabs_timeline"), t("tabs_heatmap"), t("tabs_stats"),
                    t("tabs_bvalue"), t("tabs_cross"), t("tabs_data")])

    with tabs[0]:
        st.subheader(t("timeline_title"))
        st.caption(t("timeline_caption"))
        if not df.empty:
            st.pyplot(plot_timeline(df))
            st.pyplot(plot_daily_trend(df))

    with tabs[1]:
        st.subheader(t("heatmap_title"))
        if region.startswith("🇯🇵"):
            st.pyplot(plot_japan_heatmap(df))
        else:
            st.caption(t("heatmap_caption"))
            st.pyplot(plot_timeline(df))

    with tabs[2]:
        st.subheader(t("stats_title"))
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
                               label=t("median_fmt").format(valid_depths.median()))
                    ax.set_xlabel("Depth (km)")
                    ax.set_ylabel("Count")
                    ax.set_title("Depth Distribution", fontweight="bold")
                    ax.legend()
                    ax.invert_xaxis()
                    fig.tight_layout()
                    st.pyplot(fig)

            # Summary stats
            mags = df["mag"].dropna()
            st.markdown(t("mag_summary").format(
                mn=mags.min(), q1=mags.quantile(0.25), md=mags.median(),
                q3=mags.quantile(0.75), mx=mags.max(), sd=mags.std(),
                g5=len(mags[mags>=5]), g6=len(mags[mags>=6]), g7=len(mags[mags>=7])))

    with tabs[3]:
        st.subheader(t("bvalue_title"))
        mc = st.slider(t("mc_label"), 0.0, 5.0, 2.5, 0.1, key="mc_slider")
        mags = df["mag"].dropna()
        if len(mags[mags >= mc]) >= 20:
            fig, b_val = plot_bvalue(mags, mc)
            st.pyplot(fig)
            st.markdown(t("bvalue_notes").format(b=b_val))
        else:
            st.warning(t("bvalue_insufficient"))

    with tabs[4]:
        st.subheader(t("cross_title"))
        st.caption(t("cross_caption"))
        valid = df.dropna(subset=["depth_km", "lat"])
        if len(valid) > 10:
            lat_min_v = float(valid["lat"].min())
            lat_max_v = float(valid["lat"].max())
            lat_range = st.slider(t("lat_range"), lat_min_v, lat_max_v, (lat_min_v, lat_max_v))
            st.pyplot(plot_depth_cross_section(df, lat_range))
        else:
            st.info(t("cross_insufficient"))

    with tabs[5]:
        # ─── Engineering Impact Ranking ───
        st.subheader(t("eng_title"))
        st.caption(t("eng_caption"))
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
                "time": t("col_time"), "mag": t("col_mag"), "jma_str": t("col_jma"),
                "nearest_city": t("col_city"), "dist_km": t("col_dist"),
                "pga_gal": t("col_pga"), "depth_km": t("col_depth"), "place": t("col_place")
            }), hide_index=True, width="stretch")
            st.caption(t("eng_footnote"))
        else:
            st.info(t("eng_empty"))

        st.divider()
        st.subheader(t("raw_title"))
        st.caption(t("raw_caption"))
        if not df.empty:
            display_cols = ["time", "mag", "depth_km", "lat", "lon", "place", "tsunami", "url"]
            st.dataframe(
                df[display_cols].sort_values("time", ascending=False),
                column_config={
                    "time": st.column_config.DatetimeColumn(t("col_time"), format="YYYY-MM-DD HH:mm"),
                    "url": st.column_config.LinkColumn(t("col_usgs")),
                },
                hide_index=True, width="stretch", height=500,
            )
            csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(t("export"), csv,
                f"earthquake_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv", width="stretch")

    # ─── M6+ Alerts ───
    st.divider()
    st.subheader(t("m6_alert"))
    major = df[df["mag"] >= 6.0].sort_values("time", ascending=False).head(10)
    if not major.empty:
        st.caption(t("m6_caption"))
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
                t("m6_line").format(
                    emoji=emoji, mag=row["mag"], intensity=jma_badge, city=city,
                    dist=dist, pga=pga, context=context[:120], tsunami=tsunami,
                    time=row["time"].strftime("%Y-%m-%d %H:%M UTC"),
                ),
                unsafe_allow_html=True
            )


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







