# 大宗绿测前端对接映射表

本文档用于将 `streamlit_app_0325.py` 的页面功能映射到 `backend_api.py` 的 REST API，便于前后端分离联调。
当前版本已加入 MySQL 用户系统，业务接口默认需要登录鉴权。

## 基础信息

- 后端服务地址：`http://127.0.0.1:8000`
- 在线文档：`/docs`
- OpenAPI：`/openapi.json`
- 登录页：`/login`

---

## 0. 鉴权与用户体系（新增）

### 0.1 用户相关接口

- 注册：`POST /api/auth/register`
- 登录：`POST /api/auth/login`
- 当前用户：`GET /api/auth/me`
- 简易登录页：`GET /login`

### 0.2 Token 使用方式

- 登录成功后会返回 `token`
- 后续所有业务接口请求头需携带：
  - `Authorization: Bearer <token>`

### 0.3 用户数据隔离规则

- 每个 `run_id` 会绑定到创建该任务的用户
- 用户只能看到/操作自己的训练历史
- 访问他人 `run_id` 会返回 `403`

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
- `mysql_enabled`：MySQL 是否启用
- `mysql_url_configured`：是否配置 `MYSQL_URL`

---

## 2. Tab1 运行（油价主任务）

### 2.1 启动训练

- 接口：`POST /api/oil/runs`
- 请求类型：`multipart/form-data`
- 鉴权：需要 `Authorization` 头

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

说明：

- 以上接口均需要鉴权，且仅可操作本人 `run_id`

---

## 3. Tab2 训练监控

### 3.1 监控来源解析（对应 Streamlit 监控来源单选）

- 接口：`GET /api/oil/monitor/resolve`
- 鉴权：需要

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
- 鉴权：需要

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
- 鉴权：需要

### 4.2 通用 CSV 预览

- `GET /api/oil/runs/{run_id}/csv-preview?name=prediction_results.csv&rows=50`
- 鉴权：需要

说明：

- `name` 必须是当前 run 目录下的 CSV 文件名。

### 4.3 结果统计聚合（建议结果页主要读这个）

- `GET /api/oil/runs/{run_id}/analytics`
- 鉴权：需要

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

说明：

- 两者均需要鉴权。
- 当 `mode=oil` 且传 `run_id` 时，会校验该 `run_id` 归属当前用户。

---

## 5. Tab3 子模块：新能源整合预测

### 5.1 启动新能源预测

- 接口：`POST /api/oil/runs/{run_id}/new-energy`
- 请求类型：`multipart/form-data`
- 鉴权：需要

字段：

- `ne_zip_file`（必传，zip）
- `series`
- `conf_level`
- `scale_oil_return`
- `make_viz`
- `rebuild_returns`

### 5.2 查询最近结果

- 接口：`GET /api/oil/runs/{run_id}/new-energy/latest`
- 鉴权：需要

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
- 鉴权：需要

说明：

- 若未上传 `bond_zip_file`，后端会尝试默认数据源。

### 6.2 查询最近绿债结果

- 接口：`GET /api/oil/runs/{run_id}/bond/latest`
- 鉴权：需要

返回：

- `bond_output_dir`
- `csv_preview`
- `images`

---

## 7. Tab4 下载/导出

- 列表：`GET /api/oil/runs/{run_id}/files`
- 下载单文件：`GET /api/oil/runs/{run_id}/download?name=xxx`
- 导出整包：`GET /api/oil/runs/{run_id}/export.zip`

说明：

- 以上接口均需要鉴权，且受 `run_id` 归属限制。

---

## 8. 前端最小调用顺序（推荐）

1. 登录阶段：
   - `POST /api/auth/login`
   - 前端保存 `token`（建议内存 + `sessionStorage`）
2. 页面初始化：
   - `GET /api/system/status`
   - `GET /api/oil/runs?limit=20`
3. 启动任务：
   - `POST /api/oil/runs`
4. 训练中轮询：
   - `GET /api/oil/runs/{run_id}/training-dashboard`
   - `GET /api/oil/runs/{run_id}/log`
5. 结果页展示：
   - `GET /api/oil/runs/{run_id}/overview`
   - `GET /api/oil/runs/{run_id}/analytics`
   - `GET /api/oil/runs/{run_id}/csv-preview`
6. 下载导出：
   - `GET /api/oil/runs/{run_id}/files`
   - `GET /api/oil/runs/{run_id}/download`
   - `GET /api/oil/runs/{run_id}/export.zip`

---

## 9. 备注

- 当前对齐的是“业务能力”，不是 Streamlit UI 视觉样式。
- 若你下一步切 React/Vue，建议优先以 `analytics + training-dashboard + csv-preview` 三个接口为核心渲染数据源。
- 由于启用了用户系统，建议前端统一封装请求拦截器自动注入 `Authorization` 头。

---

## 10. 前端请求封装示例（Axios）

```ts
import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```
