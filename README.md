# 🌏 QuakeMonitor 2.0 — Global Earthquake Analysis Platform

A Streamlit-based interactive global earthquake monitoring and engineering analysis platform.  
Data sourced from **USGS Earthquake Catalog** (FDSN API).



## ✨ Features

### 📊 Monitoring
- **Global coverage** — 10 preset regions including Japan sub-regions (Kanto, Kansai, Kyushu, Tohoku, Hokkaido, Japan Trench, Nankai Trough)
- **Real-time data** — USGS updates every 5-15 minutes
- **M6+ alerts** — Latest major earthquake information

### 🔬 Engineering Analysis (NEW in v2.0)
- **Gutenberg-Richter b-value** — Maximum likelihood estimation (Aki, 1965), core seismic hazard parameter
- **Depth cross-section** — Subduction zone geometry visualization
- **Energy release** — Seismic moment energy (Kanamori, 1977)
- **Historical megaquake markers** — 2011 Tohoku M9.1, 1995 Kobe M6.9, etc.

### 🌐 Professional Presentation
- **Bilingual** — English / Chinese toggle
- **Academic-style plots** — Seaborn-styled, publication-ready
- **Japan-focused** — Sub-region analysis for targeted research

### 📥 Export
- Search, sort, filter raw data
- One-click CSV export

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 Live Demo

[https://quake-monitor.streamlit.app](https://quake-monitor.streamlit.app)

## 📊 Tech Stack

- **Data**: USGS Earthquake Catalog API
- **Frontend**: Streamlit
- **Analysis**: NumPy, SciPy, Pandas
- **Visualization**: Matplotlib, Seaborn

## 🎯 Research Context

This platform was developed to support earthquake engineering research, particularly for:

- Seismic hazard assessment in Japan
- Subduction zone earthquake analysis
- Understanding frequency-magnitude relationships (G-R law)
- Supporting graduate school applications in civil/earthquake engineering

## ⚠️ Disclaimer

Data from USGS may have delays. Earthquake disaster warnings should follow official local authority announcements.

## 👤 Author

**MuYu (沐雨)**

---

*"Understanding earthquakes is the first step to living with them."*
