# 大宗绿测前端对接映射表

本文档用于将 `streamlit_app_0325.py` 的页面功能映射到 `backend_api.py` 的 REST API，便于前后端分离联调。

## 基础信息

- 后端服务地址：`http://127.0.0.1:8000`
- 在线文档：`/docs`
- OpenAPI：`/openapi.json`

---

## 1. 全局状态（首页头部）

### 对应原功能

- 任务状态
- 累计运行次数
- 最近一次运行目录

### 对应接口

- `GET /api/system/status`
- `GET /api/oil/runs?limit=20`

### 关键字段

- `global_busy`：是否有任务运行中
- `run_count`：累计运行数
- `latest_run_id`：最近 run

---

## 2. Tab1 运行（油价主任务）

### 2.1 启动训练

- 接口：`POST /api/oil/runs`
- 请求类型：`multipart/form-data`

字段：

- `zip_file`（必传，zip）
- `top_n`
- `epochs`
- `forecast_steps`
- `cutoff_date`
- `enable_early_stopping`
- `auto_bond_after_oil`（油价结束后自动触发绿债）

返回：

- `run_id`
- `output_dir`
- `pid`

### 2.2 任务状态/停止

- `GET /api/oil/runs/{run_id}`
- `GET /api/oil/runs/{run_id}/log?lines=400`
- `POST /api/oil/runs/{run_id}/stop`

---

## 3. Tab2 训练监控

### 3.1 监控来源解析（对应 Streamlit 监控来源单选）

- 接口：`GET /api/oil/monitor/resolve`

参数：

- `mode=running|active_by_log|selected|latest|manual`
- `selected_run_id`（当 mode=selected）
- `manual_dir`（当 mode=manual）

返回：

- `monitor_dir`
- `running_dir`
- `active_by_log_dir`
- `latest_dir`

### 3.2 训练图表与状态数据

- 接口：`GET /api/oil/runs/{run_id}/training-dashboard`

返回：

- `loss_series`（train/val loss）
- `price_series`（实际 vs 预测价格）
- `return_series`（实际 vs 预测收益）
- `run_log_tail`
- `is_log_active`
- `is_recently_started`

---

## 4. Tab3 结果预览

### 4.1 总览与关键文件状态

- `GET /api/oil/runs/{run_id}/overview`

### 4.2 通用 CSV 预览

- `GET /api/oil/runs/{run_id}/csv-preview?name=prediction_results.csv&rows=50`

说明：

- `name` 必须是当前 run 目录下的 CSV 文件名。

### 4.3 结果统计聚合（建议结果页主要读这个）

- `GET /api/oil/runs/{run_id}/analytics`

包含：

- `next_day_forecast`（下一天预测卡片）
- `future_forecast`（未来 H 天）
- `driver_top20`（因子分析）
- `risk`（风险区间与信号统计）
- `backtest_metrics`、`backtest_tail50`（回测）
- `bank_report_ai` 或 `bank_report_draft`（银行报告）

### 4.4 AI 报告与 AI 问答

- 生成企业银行报告：
  - `POST /api/oil/runs/{run_id}/ai-report?force=false`
- AI 专家问答：
  - `POST /api/ai/chat?mode=oil|new_energy&prompt=...&run_id=...`

---

## 5. Tab3 子模块：新能源整合预测

### 5.1 启动新能源预测

- 接口：`POST /api/oil/runs/{run_id}/new-energy`
- 请求类型：`multipart/form-data`

字段：

- `ne_zip_file`（必传，zip）
- `series`
- `conf_level`
- `scale_oil_return`
- `make_viz`
- `rebuild_returns`

### 5.2 查询最近结果

- 接口：`GET /api/oil/runs/{run_id}/new-energy/latest`

返回：

- `latest_dir`
- `log_tail`
- `images`
- `csv_preview`

---

## 6. Tab3 子模块：绿债预测

### 6.1 启动绿债预测

- 接口：`POST /api/oil/runs/{run_id}/bond`
- 请求类型：`multipart/form-data`
- 可选字段：`bond_zip_file`

说明：

- 若未上传 `bond_zip_file`，后端会尝试默认数据源。

### 6.2 查询最近绿债结果

- 接口：`GET /api/oil/runs/{run_id}/bond/latest`

返回：

- `bond_output_dir`
- `csv_preview`
- `images`

---

## 7. Tab4 下载/导出

- 列表：`GET /api/oil/runs/{run_id}/files`
- 下载单文件：`GET /api/oil/runs/{run_id}/download?name=xxx`
- 导出整包：`GET /api/oil/runs/{run_id}/export.zip`

---

## 8. 前端最小调用顺序（推荐）

1. 页面初始化：
   - `GET /api/system/status`
   - `GET /api/oil/runs?limit=20`
2. 启动任务：
   - `POST /api/oil/runs`
3. 训练中轮询：
   - `GET /api/oil/runs/{run_id}/training-dashboard`
   - `GET /api/oil/runs/{run_id}/log`
4. 结果页展示：
   - `GET /api/oil/runs/{run_id}/overview`
   - `GET /api/oil/runs/{run_id}/analytics`
   - `GET /api/oil/runs/{run_id}/csv-preview`
5. 下载导出：
   - `GET /api/oil/runs/{run_id}/files`
   - `GET /api/oil/runs/{run_id}/download`
   - `GET /api/oil/runs/{run_id}/export.zip`

---

## 9. 备注

- 当前对齐的是“业务能力”，不是 Streamlit UI 视觉样式。
- 若你下一步切 React/Vue，建议优先以 `analytics + training-dashboard + csv-preview` 三个接口为核心渲染数据源。
