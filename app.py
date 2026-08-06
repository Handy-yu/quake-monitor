"""
============================================================
🌏 全球地震监测平台 — QuakeMonitor
============================================================
数据来源：USGS Earthquake Catalog
数据覆盖：全球
更新频率：实时（USGS 每 5-15 分钟更新）
============================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── 页面配置 ────────────────────────────
st.set_page_config(
    page_title="全球地震监测平台",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 中文字体
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# ─── 区域预设 ────────────────────────────
REGION_PRESETS = {
    "🌍 全球": {"min_lat": -90, "max_lat": 90, "min_lon": -180, "max_lon": 180},
    "🇯🇵 日本": {"min_lat": 24, "max_lat": 46, "min_lon": 122, "max_lon": 149},
    "🇨🇳 中国": {"min_lat": 18, "max_lat": 54, "min_lon": 73, "max_lon": 135},
    "🇹🇼 台湾": {"min_lat": 21, "max_lat": 26, "min_lon": 119, "max_lon": 123},
    "🇺🇸 加州": {"min_lat": 32, "max_lat": 42, "min_lon": -125, "max_lon": -114},
    "🇹🇷 土耳其": {"min_lat": 36, "max_lat": 42, "min_lon": 26, "max_lon": 45},
    "🔥 环太平洋火山带": {"min_lat": -60, "max_lat": 60, "min_lon": 100, "max_lon": -60},
    "✏️ 自定义": None,
}


# ─── 数据获取 ────────────────────────────
@st.cache_data(ttl=600)
def fetch_quakes(
    min_magnitude=2.5,
    limit=20000,
    days_back=30,
    min_lat=-90,
    max_lat=90,
    min_lon=-180,
    max_lon=180,
):
    """从 USGS 获取全球地震数据"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minlatitude": min_lat,
        "maxlatitude": max_lat,
        "minlongitude": min_lon,
        "maxlongitude": max_lon,
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": limit,
    }

    resp = requests.get(url, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    quakes = data.get("features", [])

    records = []
    for q in quakes:
        props = q.get("properties", {})
        geom = q.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])
        time_ms = props.get("time", 0)
        dt = datetime.fromtimestamp(time_ms / 1000, timezone.utc) if time_ms else None

        depth = coords[2]
        if depth is not None and depth < 0:
            depth = None

        records.append(
            {
                "时间(UTC)": dt,
                "震级": round(props.get("mag"), 1) if props.get("mag") else None,
                "深度(km)": round(depth, 1) if depth is not None else None,
                "经度": round(coords[0], 4) if coords[0] is not None else None,
                "纬度": round(coords[1], 4) if coords[1] is not None else None,
                "地点": props.get("place", ""),
                "类型": props.get("type", ""),
                "海啸预警": "⚠️ 是" if props.get("tsunami", 0) > 0 else "否",
                "USGS详情": props.get("url", ""),
            }
        )

    return pd.DataFrame(records)


# ─── 可视化 ────────────────────────────
def style_negative(val):
    return "color: red; font-weight: bold" if isinstance(val, str) and "是" in val else ""


def plot_timeline(df):
    """时间趋势散点图"""
    fig, ax = plt.subplots(figsize=(14, 5))
    depths = df["深度(km)"].fillna(df["深度(km)"].median()).values

    scatter = ax.scatter(
        df["时间(UTC)"],
        df["震级"],
        c=depths,
        cmap="turbo_r",
        s=np.clip(df["震级"] ** 3, 5, 800),
        alpha=0.55,
        edgecolors="none",
    )

    cbar = plt.colorbar(scatter, ax=ax, label="深度 (km)")
    cbar.ax.invert_yaxis()

    # 标注 M7+
    for _, row in df[df["震级"] >= 7.0].iterrows():
        label = str(row["地点"]).split("of ")[-1].split(",")[0].strip()[:25] if pd.notna(row["地点"]) else ""
        if label:
            ax.annotate(
                label,
                (row["时间(UTC)"], row["震级"]),
                fontsize=7,
                alpha=0.75,
                xytext=(5, 5),
                textcoords="offset points",
            )

    ax.set_xlabel("时间 (UTC)")
    ax.set_ylabel("震级 (M)")
    ax.set_title("地震活动时间线", fontsize=15, fontweight="bold")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def plot_globe_heatmap(df):
    """全球震中分布热力图"""
    fig, ax = plt.subplots(figsize=(16, 8))

    h = ax.hist2d(
        df["经度"], df["纬度"],
        bins=(120, 70),
        cmap="inferno",
        alpha=0.85,
    )
    cbar = plt.colorbar(h[3], ax=ax, label="地震次数", shrink=0.75)
    cbar.ax.tick_params(labelsize=8)

    # 标注板块边界（简化的大致位置）
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    ax.set_title("全球地震震中分布", fontsize=15, fontweight="bold")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    fig.tight_layout()
    return fig


def plot_magnitude_donut(df):
    """震级分布饼图"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 深度直方图
    ax = axes[0]
    valid = df["深度(km)"].dropna()
    if len(valid) > 0:
        ax.hist(valid, bins=50, color="steelblue", edgecolor="white", alpha=0.85)
        ax.axvline(valid.median(), color="crimson", linestyle="--", linewidth=1.5, label=f"中位数: {valid.median():.0f} km")
        ax.set_xlabel("深度 (km)")
        ax.set_ylabel("地震次数")
        ax.set_title("震源深度分布", fontweight="bold")
        ax.legend(fontsize=9)

    # 震级分布
    ax = axes[1]
    bins = [0, 2.5, 4.0, 5.0, 6.0, 7.0, 10.0]
    labels = ["< M2.5", "M2.5-4", "M4-5", "M5-6", "M6-7", "M7+"]
    mags = df["震级"].dropna()
    binned = pd.cut(mags, bins=bins, labels=labels)
    counts = binned.value_counts().sort_index()
    colors = ["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#F44336", "#9C27B0"]
    ax.bar(range(len(counts)), counts.values, color=colors[:len(counts)], edgecolor="white")
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45, ha="right")
    ax.set_ylabel("地震次数")
    ax.set_title("震级分布", fontweight="bold")

    fig.tight_layout()
    return fig


def plot_daily_trend(df):
    """每日地震频次趋势"""
    fig, ax = plt.subplots(figsize=(14, 4))
    df["日期"] = df["时间(UTC)"].dt.date
    daily = df.groupby("日期").size()

    ax.fill_between(pd.to_datetime(daily.index), daily.values, alpha=0.3, color="steelblue")
    ax.plot(pd.to_datetime(daily.index), daily.values, color="steelblue", linewidth=1)
    ax.set_xlabel("日期")
    ax.set_ylabel("地震次数")
    ax.set_title("每日地震频次", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


# ─── 页面 UI ────────────────────────────

# 顶部导航
st.title("🌏 全球地震监测平台")
st.caption("数据来源：USGS Earthquake Catalog  |  实时更新  |  免费公开")

# 侧边栏
with st.sidebar:
    st.header("🔧 筛选条件")

    region = st.selectbox("快速区域", list(REGION_PRESETS.keys()), index=0)

    if region == "✏️ 自定义":
        col_a, col_b = st.columns(2)
        lat_min = col_a.number_input("南纬", -90.0, 90.0, -90.0)
        lat_max = col_b.number_input("北纬", -90.0, 90.0, 90.0)
        lon_min = col_a.number_input("西经", -180.0, 180.0, -180.0)
        lon_max = col_b.number_input("东经", -180.0, 180.0, 180.0)
    else:
        preset = REGION_PRESETS[region]
        lat_min, lat_max = preset["min_lat"], preset["max_lat"]
        lon_min, lon_max = preset["min_lon"], preset["max_lon"]
        st.caption(f"纬度 {lat_min}° ~ {lat_max}°  |  经度 {lon_min}° ~ {lon_max}°")

    st.divider()

    time_range = st.selectbox(
        "时间范围",
        ["过去 24 小时", "过去 7 天", "过去 30 天", "过去 1 年", "过去 10 年"],
        index=2,
    )
    days_map = {"过去 24 小时": 1, "过去 7 天": 7, "过去 30 天": 30, "过去 1 年": 365, "过去 10 年": 3650}
    days_back = days_map[time_range]

    min_mag = st.slider("最小震级", 0.0, 6.0, 2.5, 0.5)

    depth_min = st.slider("最小深度 (km)", 0, 700, 0, 10)
    depth_max = st.slider("最大深度 (km)", 10, 700, 700, 10)

    st.divider()
    refresh = st.button("🔄 刷新数据", use_container_width=True)

# ─── 加载数据 ────────────────────────────
if refresh:
    st.cache_data.clear()

with st.spinner("正在从 USGS 获取全球地震数据...⏳"):
    try:
        df = fetch_quakes(
            min_magnitude=min_mag,
            days_back=days_back,
            min_lat=lat_min,
            max_lat=lat_max,
            min_lon=lon_min,
            max_lon=lon_max,
        )
        # 深度筛选
        df = df[(df["深度(km)"].isna()) | (df["深度(km)"].between(depth_min, depth_max))]
        load_error = False
    except Exception as e:
        st.error(f"数据获取失败: {e}")
        st.info("可能是网络问题，请稍后重试")
        df = pd.DataFrame()
        load_error = True

# ─── 数据概览 ────────────────────────────
if not df.empty:
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📊 地震总数", f"{len(df):,}")
    c2.metric("📈 最大震级", f"M{df['震级'].max():.1f}")
    c3.metric("🌊 海啸预警", f"{len(df[df['海啸预警'].str.contains('是')])}")
    c4.metric("📏 平均深度", f"{df['深度(km)'].mean():.0f} km" if df["深度(km)"].notna().any() else "N/A")
    c5.metric("📅 数据跨度", f"{df['时间(UTC)'].min().strftime('%m/%d')} ~ {df['时间(UTC)'].max().strftime('%m/%d')}" if not df.empty else "N/A")

    # 如果数据太多，显示提示
    if len(df) >= 20000:
        st.warning("⚠️ 数据量达到上限（20,000条），结果已截断。请缩小时间范围或提高震级阈值以获取更精确的结果。")

    # ─── 图表标签 ──────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 时间趋势", "🗺️ 全球分布", "📊 统计分析", "📋 数据浏览"])

    with tab1:
        st.subheader("地震活动时间线")
        st.caption("颜色 = 深度（黄=浅 → 蓝=深）  |  点大小 = 震级  |  标注 = M7+ 大震")
        if not df.empty:
            fig = plot_timeline(df)
            st.pyplot(fig)

            st.subheader("每日频次趋势")
            fig2 = plot_daily_trend(df)
            st.pyplot(fig2)

    with tab2:
        st.subheader("地震震中分布")
        st.caption("颜色越亮 = 地震越密集  |  直观展示地球板块边界和地震带")
        if not df.empty:
            fig = plot_globe_heatmap(df)
            st.pyplot(fig)

    with tab3:
        st.subheader("深度与震级分析")
        if not df.empty:
            fig = plot_magnitude_donut(df)
            st.pyplot(fig)

    with tab4:
        st.subheader("原始数据")
        st.caption("点击列名排序  |  搜索  |  筛选  |  一键导出")
        if not df.empty:
            st.dataframe(
                df.sort_values("时间(UTC)", ascending=False),
                column_config={
                    "时间(UTC)": st.column_config.DatetimeColumn("时间 (UTC)", format="YYYY-MM-DD HH:mm"),
                    "USGS详情": st.column_config.LinkColumn("USGS详情"),
                },
                hide_index=True,
                use_container_width=True,
                height=500,
            )

            csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 导出 CSV",
                csv,
                f"earthquake_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True,
            )

    # ─── 最近大地震 ──────────────────────────
    st.divider()
    st.subheader("📰 最新 M6+ 地震速报")
    major = df[df["震级"] >= 6.0].sort_values("时间(UTC)", ascending=False).head(10)
    if not major.empty:
        for _, row in major.iterrows():
            emoji = "🔴" if row["震级"] >= 7.0 else "🟠"
            tsunami_flag = f" {row['海啸预警']}" if "是" in str(row["海啸预警"]) else ""
            st.markdown(
                f"{emoji} **M{row['震级']:.1f}** — {row['地点']}"
                f"  ({row['深度(km)']:.0f} km)"
                f"{tsunami_flag}"
                f"  |  {row['时间(UTC)'].strftime('%Y-%m-%d %H:%M UTC')}"
            )

# ─── 底部 ────────────────────────────
st.divider()
st.caption("数据来源：U.S. Geological Survey Earthquake Hazards Program")
st.caption("本站仅供信息参考，实际地震信息以各国官方机构发布为准")

# 关于 — 匿名
with st.expander("ℹ️ 关于本站"):
    st.markdown("""
    ### 全球地震监测平台

    本平台数据来自美国地质调查局（USGS）地震目录，通过其公开 API 实时获取全球地震记录。

    **功能特点：**
    - 覆盖全球范围，支持按区域筛选
    - 实时数据（USGS 每 5-15 分钟更新）
    - 可视化分析图表
    - 数据可导出为 CSV

    **免责声明：**
    本站数据来源于 USGS，可能存在数分钟到数小时的延迟。
    地震灾害预警请以当地官方机构发布为准。
    """)

st.caption("— 沐雨 制作")
