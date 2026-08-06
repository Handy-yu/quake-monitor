# 🌏 全球地震监测平台

一个基于 Python Streamlit 的交互式全球地震数据可视化平台。数据来源于 USGS（美国地质调查局）公开地震目录。

## ✨ 功能

- 🌍 **全球覆盖** — 支持 7 个预设区域（日本、中国、台湾、加州、土耳其、环太平洋火山带）+ 自定义范围
- ⏱ **实时数据** — USGS 每 5-15 分钟更新
- 📊 **可视化分析** — 时间趋势、震中热力图、深度/震级分布、每日频次
- 📋 **数据浏览** — 搜索、排序、筛选，一键导出 CSV
- 🚨 **M6+ 速报** — 最新大地震信息列表

## 🚀 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
streamlit run app.py
```

## 📦 部署到 Streamlit Cloud

1. Fork 本仓库
2. 在 [streamlit.io/cloud](https://streamlit.io/cloud) 关联 GitHub 仓库
3. 设 `app.py` 为入口文件
4. 自动部署

## 📡 数据来源

[USGS Earthquake Catalog API](https://earthquake.usgs.gov/fdsnws/event/1/)

## ⚠️ 免责声明

本站数据仅供参考，地震灾害预警请以当地官方机构发布为准。

---

— 沐雨
