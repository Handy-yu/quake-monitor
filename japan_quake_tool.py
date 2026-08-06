"""
============================================================
🦊 日本地震数据分析 & 九州大学研究室追踪工具
============================================================
为卓远定制的项目 —— 结合土木工程（抗震方向）+ 日本留学目标

功能：
  🟢 阶段一：从 USGS 地震数据库拉取日本近 10 年地震数据
  🟡 阶段二：生成可视化分析图表
  🔴 阶段三：监控九州大学抗震方向教授的最新论文

使用：先装依赖 → pip install -r requirements.txt
     然后 python japan_quake_tool.py
============================================================
"""

import os
import sys
import json
import time
import math
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows 中文显示修复
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ─── 配置区 ───────────────────────────────────────────

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 日本经纬度范围
JAPAN_BOUNDS = {
    "min_lat": 24.0,   # 冲绳以南
    "max_lat": 46.0,   # 北海道以北
    "min_lon": 122.0,  # 包括冲绳
    "max_lon": 149.0,  # 包括小笠原
}

# 九州大学 土木工学 抗震方向 教授（可后续补充）
KYUSHU_PROFESSORS = [
    "Kawano",       # 河野 — 耐震构造
    "Kajita",       # 梶田 — 地震工学
    "Asai",         # 浅井 — 地盘工学/地震
    "Matsumoto",    # 松本 — 混凝土/抗震
]

# ========================================================
# 🟢 阶段一：数据获取
# ========================================================

def fetch_japan_quakes(years=10, min_magnitude=4.0, limit=20000):
    """
    从 USGS Earthquake Catalog API 获取日本区域地震数据
    
    USGS API 免费，无需 API Key，全球地震数据覆盖
    
    参数：
        years: 回溯年份数（默认 10 年）
        min_magnitude: 最小震级（默认 4.0 级）
        limit: 最大返回条数
    
    返回：地震数据列表
    """
    import requests
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=years * 365)
    
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minlatitude": JAPAN_BOUNDS["min_lat"],
        "maxlatitude": JAPAN_BOUNDS["max_lat"],
        "minlongitude": JAPAN_BOUNDS["min_lon"],
        "maxlongitude": JAPAN_BOUNDS["max_lon"],
        "minmagnitude": min_magnitude,
        "orderby": "time",
        "limit": limit,
    }
    
    print(f"\n🌏 正在从 USGS 获取日本地区地震数据...")
    print(f"   时间范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"   震级 ≥ M{min_magnitude}")
    
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        quakes = data.get("features", [])
        print(f"   ✅ 共获取 {len(quakes)} 条地震记录")
        return quakes
        
    except requests.RequestException as e:
        print(f"   ❌ 数据获取失败: {e}")
        return []


def quakes_to_dataframe(quakes):
    """
    将 USGS GeoJSON 格式转为 pandas DataFrame
    提取有用字段：时间、震级、深度、位置、经纬度
    """
    import pandas as pd
    
    records = []
    for q in quakes:
        props = q.get("properties", {})
        geom = q.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])
        
        # 解析时间
        time_ms = props.get("time", 0)
        dt = datetime.fromtimestamp(time_ms / 1000, timezone.utc) if time_ms else None
        
        records.append({
            "时间": dt,
            "震级": props.get("mag"),
            "深度(km)": coords[2] if coords[2] is not None else None,
            "经度": coords[0],
            "纬度": coords[1],
            "地点": props.get("place", ""),
            "类型": props.get("type", ""),
            "海啸预警": "是" if props.get("tsunami", 0) > 0 else "否",
            "USGS链接": props.get("url", ""),
        })
    
    df = pd.DataFrame(records)
    # 去掉无效深度（USGS 有时填 -999）
    df.loc[df["深度(km)"] < 0, "深度(km)"] = None
    return df


def save_and_summary(df):
    """保存 CSV 并打印简要统计"""
    csv_path = OUTPUT_DIR / "japan_quakes.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n📁 数据已保存: {csv_path}")
    
    if df.empty:
        print("   ⚠️  数据为空，无法生成统计")
        return
    
    print(f"\n📊 数据概况:")
    print(f"   记录总数: {len(df)}")
    print(f"   时间跨度: {df['时间'].min().strftime('%Y-%m-%d')} ~ {df['时间'].max().strftime('%Y-%m-%d')}")
    print(f"   震级范围: M{df['震级'].min():.1f} ~ M{df['震级'].max():.1f}")
    print(f"   最大地震: M{df['震级'].max():.1f} — {df.loc[df['震级'].idxmax(), '地点']}")
    print(f"   平均深度: {df['深度(km)'].mean():.1f} km")
    
    # 分级统计
    bins = [0, 4, 5, 6, 7, 10]
    labels = ["M<4", "M4-5", "M5-6", "M6-7", "M7+"]
    df["震级区间"] = pd.cut(df["震级"], bins=bins, labels=labels)
    print(f"\n   震级分布:")
    for label in labels:
        count = (df["震级区间"] == label).sum()
        print(f"     {label}: {count} 次")


# ========================================================
# 🟡 阶段二：数据可视化
# ========================================================

def plot_magnitude_time(df):
    """震级-时间散点图"""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    colors = df["深度(km)"].fillna(0).values
    scatter = ax.scatter(
        df["时间"], df["震级"],
        c=colors, cmap="viridis_r",
        s=df["震级"] ** 2.5,  # 震级越大点越大
        alpha=0.5, edgecolors="none"
    )
    
    cbar = plt.colorbar(scatter, ax=ax, label="震源深度 (km)")
    cbar.ax.invert_yaxis()  # 浅=红, 深=绿
    
    ax.set_xlabel("时间")
    ax.set_ylabel("震级 (M)")
    ax.set_title("日本近 10 年地震活动趋势\n（颜色=深度, 大小=震级）", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.3)
    
    # 标注 311、熊本等大震
    major_quakes = df[df["震级"] >= 7.0]
    for _, row in major_quakes.iterrows():
        ax.annotate(
            row["地点"].split(",")[0] if pd.notna(row["地点"]) else "",
            (row["时间"], row["震级"]),
            fontsize=8, alpha=0.7,
            xytext=(5, 5), textcoords="offset points"
        )
    
    fig.tight_layout()
    path = OUTPUT_DIR / "quake_timeline.png"
    fig.savefig(path, dpi=150)
    print(f"📈 时间趋势图已保存: {path}")
    plt.close(fig)


def plot_depth_distribution(df):
    """震源深度分布直方图"""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 深度直方图
    ax = axes[0]
    valid_depth = df["深度(km)"].dropna()
    ax.hist(valid_depth, bins=50, color="steelblue", edgecolor="white", alpha=0.8)
    ax.set_xlabel("深度 (km)")
    ax.set_ylabel("地震次数")
    ax.set_title("震源深度分布", fontsize=13, fontweight="bold")
    ax.axvline(valid_depth.mean(), color="red", linestyle="--", label=f"平均: {valid_depth.mean():.1f} km")
    ax.legend()
    
    # 深度 vs 震级
    ax = axes[1]
    ax.scatter(df["深度(km)"], df["震级"], alpha=0.3, s=10, c="coral")
    ax.set_xlabel("深度 (km)")
    ax.set_ylabel("震级 (M)")
    ax.set_title("深度 vs 震级", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    
    fig.tight_layout()
    path = OUTPUT_DIR / "quake_depth.png"
    fig.savefig(path, dpi=150)
    print(f"📊 深度分析图已保存: {path}")
    plt.close(fig)


def plot_monthly_counts(df):
    """月度地震频次趋势"""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # 按月统计
    df_monthly = df.set_index("时间").resample("ME").size()
    
    ax = axes[0]
    ax.fill_between(df_monthly.index, df_monthly.values, alpha=0.3, color="steelblue")
    ax.plot(df_monthly.index, df_monthly.values, color="steelblue", linewidth=1)
    ax.set_ylabel("地震次数")
    ax.set_title("日本 M4+ 地震月度频次", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    
    # 按年统计 M5+ 次数
    df["年份"] = df["时间"].dt.year
    yearly_m5 = df[df["震级"] >= 5].groupby("年份").size()
    
    ax = axes[1]
    ax.bar(yearly_m5.index, yearly_m5.values, color="coral", alpha=0.8)
    ax.set_xlabel("年份")
    ax.set_ylabel("M5+ 地震次数")
    ax.set_title("日本 M5+ 地震年度频次", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3, axis="y")
    
    fig.tight_layout()
    path = OUTPUT_DIR / "quake_frequency.png"
    fig.savefig(path, dpi=150)
    print(f"📊 频次分析图已保存: {path}")
    plt.close(fig)


def plot_heatmap(df):
    """震中分布热力图"""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    h = ax.hist2d(
        df["经度"], df["纬度"],
        bins=(80, 60),
        cmap="hot",
        alpha=0.8
    )
    
    plt.colorbar(h[3], ax=ax, label="地震次数")
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    ax.set_title("日本及周边地震热力图 (震中分布)", fontsize=14, fontweight="bold")
    
    # 标注主要城市
    cities = {
        "东京": (139.7, 35.7),
        "大阪": (135.5, 34.7),
        "福冈": (130.4, 33.6),
        "札幌": (141.4, 43.1),
        "仙台": (140.9, 38.3),
    }
    for name, (lon, lat) in cities.items():
        ax.plot(lon, lat, "bo", markersize=4)
        ax.annotate(name, (lon, lat), fontsize=9, color="white",
                   xytext=(3, 3), textcoords="offset points",
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.5))
    
    ax.set_aspect("equal")
    fig.tight_layout()
    path = OUTPUT_DIR / "quake_heatmap.png"
    fig.savefig(path, dpi=150)
    print(f"🗺️  震中热力图已保存: {path}")
    plt.close(fig)


def run_visualizations(df):
    """生成所有可视化图表"""
    print(f"\n🎨 正在生成可视化图表...")
    plot_magnitude_time(df)
    plot_depth_distribution(df)
    plot_monthly_counts(df)
    plot_heatmap(df)
    print(f"   ✅ 全部图表已生成至 {OUTPUT_DIR}/")


# ========================================================
# 🔴 阶段三：教授论文监控（基础版）
# ========================================================

def check_professors(use_real_api=False):
    """
    查询九州大学抗震教授的最新信息
    
    当前为基础版：使用 Google Scholar 公开页面搜索
    进阶版：可接入 Semantic Scholar API 或 CiNii API
    """
    import requests
    
    print(f"\n🔬 正在搜索九州大学抗震方向教授信息...")
    print(f"   目标教授: {', '.join(KYUSHU_PROFESSORS)}")
    
    results = []
    
    for prof in KYUSHU_PROFESSORS:
        query = f"Kyushu University {prof} earthquake engineering"
        print(f"\n   📄 搜索: {prof}")
        
        try:
            # 使用 Semantic Scholar API（免费，无需 Key）
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": query,
                "limit": 5,
                "fieldsOfStudy": "Engineering",
                "fields": "title,year,authors,externalIds,url"
            }
            resp = requests.get(url, params=params, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                papers = data.get("data", [])
                
                for p in papers[:3]:
                    title = p.get("title", "N/A")
                    year = p.get("year", "N/A")
                    authors = ", ".join([a.get("name", "") for a in p.get("authors", [])[:3]])
                    paper_url = p.get("url", "")
                    
                    print(f"     [{year}] {title[:80]}...")
                    print(f"      作者: {authors}")
                    results.append({
                        "教授关键词": prof,
                        "论文标题": title,
                        "年份": year,
                        "作者": authors,
                        "链接": paper_url,
                    })
            else:
                print(f"     ⚠️ API 返回状态 {resp.status_code}")
                
        except requests.RequestException as e:
            print(f"     ⚠️ 搜索失败: {e}")
        
        time.sleep(1)  # 礼貌地限速
    
    # 保存结果
    if results:
        df = __import__("pandas").DataFrame(results)
        path = OUTPUT_DIR / "professor_papers.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n📁 论文信息已保存: {path}")
    
    return results


# ========================================================
# 🚀 主入口
# ========================================================

def main():
    print("=" * 60)
    print("🦊  日本地震数据分析 & 九州大学追踪工具")
    print("=" * 60)
    
    # ─── 阶段一：获取数据 ───
    print("\n" + "─" * 40)
    print("🟢 阶段一：地震数据获取")
    print("─" * 40)
    
    quakes = fetch_japan_quakes(years=10, min_magnitude=4.0)
    
    if not quakes:
        print("❌ 未获取到数据，退出。请检查网络连接后重试。")
        return
    
    df = quakes_to_dataframe(quakes)
    save_and_summary(df)
    
    # ─── 阶段二：可视化 ───
    print("\n" + "─" * 40)
    print("🟡 阶段二：数据可视化")
    print("─" * 40)
    
    run_visualizations(df)
    
    # ─── 阶段三：教授追踪 ───
    print("\n" + "─" * 40)
    print("🔴 阶段三：九州大学教授论文")
    print("─" * 40)
    
    check_professors()
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！查看 output/ 目录获取结果。")
    print("=" * 60)


if __name__ == "__main__":
    main()
