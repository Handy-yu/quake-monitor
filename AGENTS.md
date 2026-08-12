# AGENTS.md — QuakeMonitor

## 项目目标
Streamlit 全球/日本地震监测与工程分析平台（USGS 数据），用于地震工程研究。

## 目录约定
- app.py：Streamlit 主应用（数据获取、图表、工程分析、多语言 UI）
- japan_quake_tool.py：离线脚本（拉取日本 10 年数据、出图、保存 CSV）
- output/：生成物目录（CSV/PNG），已 gitignore，不要直接修改
- requirements.txt：依赖清单

## 常用命令
- 安装依赖：pip install -r requirements.txt
- 启动应用：streamlit run app.py
- 离线脚本：python japan_quake_tool.py（TODO：确认是否支持命令行参数）
- 测试：暂无（TODO：补充单元测试）
- lint/类型检查：暂无

## 开发规则
- 数据源为 USGS FDSN API；网络在部分地区不稳定，请求已做 3 次重试，失败时须给用户清晰中文提示
- 科研核心公式禁止随意改动：
  - G-R b 值（Aki 1965，compute_bvalue）
  - 地震能量（Kanamori 1977，seismic_energy）
  - 震度/PGA 估算（estimate_jma_intensity / estimate_pga_gal）
- 修改须保持可复现性：不改变数据过滤逻辑、不覆盖 output/ 历史结果
- 函数定义必须在使用之前（本项目曾因定义顺序导致 NameError）
- 新增功能先只读分析，标注涉及文件和行号

## 禁止事项
- 不改 b 值/能量/震度/PGA 公式，除非任务明确要求
- 不提交 output/ 下生成物（CSV/PNG）
- 不删除历史输出文件
- 不修改 .gitignore 的忽略规则

## 完成标准
- streamlit run app.py 能正常启动，无报错
- 数据加载、6 个 tab 图表、CSV 导出、语言切换均可用
- 改动仅涉及约定范围，并已通过 git diff 审查
