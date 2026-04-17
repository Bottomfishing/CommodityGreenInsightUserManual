# 大宗绿测前端架构文档

> 油价预测与绿色金融平台 · Vue 3 前端项目

---

## 1. 概述

基于 Vue 3 + Vite 构建，对接后端 FastAPI 服务，实现油价预测（GRU）、新能源股票预测、绿债预测、AI 报告生成等核心功能。

- **后端 API 地址**：`http://127.0.0.1:8000`
- **本地代理**：`/api` → 后端（Vite 配置）
- **技术栈**：Vue 3 + Vite，Composition API

---

## 2. 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3（Composition API）|
| 构建 | Vite |
| 样式 | 原生 CSS（CSS Variables + backdrop-filter 毛玻璃） |
| 状态 | Pinia（`stores/app.js`） |
| 路由 | Vue Router（`router.js`） |
| HTTP | 原生 `fetch`（`api/index.js`） |
| 图标 | Emoji（无外部图标库） |

---

## 3. 目录结构

```
CommodityGreenInsight-Vue/
├── public/
│   ├── logo_zrld.png          # 项目 Logo 图标
│   └── 用户手册.pdf            # PDF 用户手册
│
├── src/
│   ├── api/
│   │   └── index.js           # API 接口封装（所有后端请求）
│   │
│   ├── components/             # 公共组件（预留）
│   │   └── .gitkeep
│   │
│   ├── stores/
│   │   └── app.js             # Pinia 全局状态（系统状态、运行列表等）
│   │
│   ├── styles/
│   │   └── global.css         # 全局样式
│   │
│   ├── views/                 # 4 个主页面 Tab 组件
│   │   ├── RunView.vue        # 运行页面（上传 zip、配置参数、启动训练）
│   │   ├── MonitorView.vue    # 训练监控（实时日志、指标曲线）
│   │   ├── ResultsView.vue    # 结果预览（预测图表、CSV 预览、AI 报告）
│   │   └── DownloadView.vue   # 下载/导出（文件列表、单个下载、打包下载）
│   │
│   ├── App.vue                # 根组件：侧边栏 + Tab 导航 + 弹窗
│   ├── main.js               # Vue 入口
│   └── router.js             # 路由配置（4 个路由，均为懒加载）
│
├── index.html
├── vite.config.js             # Vite 配置（含 /api 代理）
├── package.json
└── README.md
```

---

## 4. 核心模块说明

### 4.1 App.vue — 根组件

**职责**：侧边栏 + Tab 导航 + 全局弹窗，是整个应用的顶层容器。

**侧边栏**（展开/收起，可拖拽调整宽度 200~480px）：
- 品牌区：Logo + 项目名 + 收起按钮
- 状态卡片：任务状态 + 累计运行次数
- 历史运行选择下拉框
- 用户手册按钮（链接 PDF）
- AI 助手（`<details>` 可折叠聊天面板）
- 收起状态：极简模式，只显示 Logo + 状态点 + 按钮

**Tab 导航栏**（Sticky 定位）：
- 左：4 个 Tab 按钮（运行 / 训练监控 / 结果预览 / 下载导出）
- 右：状态指示圆点 + 三点菜单（主题切换、用户手册、登录、关于）

**弹窗**：关于弹窗、登录弹窗

**关键状态**：`sidebarCollapsed`、`sidebarWidth`、`topbarMenuOpen`、`aboutOpen`、`loginOpen`、`theme`

### 4.2 api/index.js — API 层

基于原生 `fetch` 封装，所有请求经过 `/api` 代理到后端。

**认证方式**：Bearer Token（`localStorage.token`），通过请求头 `Authorization: Bearer <token>` 携带。

**主要 API 分组**：

| 分组 | 接口 | 说明 |
|------|------|------|
| 认证 | `POST /auth/login` `POST /auth/register` `GET /auth/me` | 用户登录/注册/获取信息 |
| 系统 | `GET /system/status` | 全局状态（global_busy、current_run_id 等）|
| Run | `POST /oil/runs` `GET /oil/runs` `POST /oil/runs/{id}/stop` | 创建/查询/停止训练 Run |
| 监控 | `GET /oil/monitor/resolve` `GET /oil/runs/{id}/training-dashboard` `GET /oil/runs/{id}/log` | 监控数据、日志 |
| 结果 | `GET /oil/runs/{id}/overview` `GET /oil/runs/{id}/analytics` `GET /oil/runs/{id}/prediction-preview` | 预测结果、分析数据 |
| AI | `POST /ai/chat` | AI 助手对话 |
| 新能源 | `POST /oil/runs/{id}/new-energy` `GET /oil/runs/{id}/new-energy/latest` | 新能源股票预测 |
| 绿债 | `POST /oil/runs/{id}/bond` `GET /oil/runs/{id}/bond/latest` | 绿债预测 |
| 下载 | `GET /oil/runs/{id}/files` `GET /oil/runs/{id}/download?name=` `GET /oil/runs/{id}/export.zip` | 文件列表及下载 |

### 4.3 stores/app.js — 状态管理

Pinia store，管理全局状态，供所有视图共享。

**状态**：`systemStatus`、`runList`、`selectedRunId`、`theme`

**计算属性**：`isGlobalBusy`、`selectedRun`、`runCount`

**方法**：`toggleTheme`、`loadSystemStatus`、`loadRunList`、`selectRun`

### 4.4 router.js — 路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | → 重定向 `/run` | |
| `/run` | `RunView.vue` | 运行 |
| `/monitor/:runId?` | `MonitorView.vue` | 训练监控 |
| `/results/:runId?` | `ResultsView.vue` | 结果预览 |
| `/download/:runId?` | `DownloadView.vue` | 下载导出 |

均使用路由级懒加载（`() => import(...)`）。

---

## 5. Views — 四个 Tab 页面

### 5.1 RunView — 运行

- Hero 区域：大标题 + KPI 卡片（状态/目录/启动时间）
- 步骤指示器（上传数据 → 配置参数 → 训练监控 → 结果预览）
- 文件上传区（拖拽上传 zip 包）
- 参数配置表单（topN、epochs、预测步数、截断日期、早停开关、绿债自动触发）
- 启动/停止按钮

### 5.2 MonitorView — 训练监控

- 监控来源选择（running / active_by_log / selected / latest / manual）
- 实时日志滚动展示（`training_log.csv` 状态 + 训练日志）
- 指标曲线（matplotlib 生成的 PNG 图表轮播）
- 预测结果预览（`prediction_results.csv` 表格）

### 5.3 ResultsView — 结果预览

- 概览 KPI 卡片
- GRU 收益图表（`gru_returns.png`）
- 预测结果表格（`prediction_results.csv` 可翻页预览）
- 新能源预测区块（上传 zip → 查看图表）
- 绿债预测区块（上传 zip → 查看图表）
- AI 报告生成按钮 + 报告内容展示

### 5.4 DownloadView — 下载/导出

- 文件列表（图片 + CSV）
- 单文件下载
- 打包 zip 下载

---

## 6. 指南

### 6.1 启动开发服务器

```bash
cd CommodityGreenInsight-Vue
npm install
npm run dev
```

默认端口 `5174`，`/api` 代理到 `http://127.0.0.1:8000`。

### 6.2 新增视图页面

1. 在 `src/views/` 下创建 `.vue` 文件
2. 在 `router.js` 中注册路由
3. 在 `App.vue` 中用 `<router-view>` 或 `v-if` 引入

### 6.3 新增 API 接口

在 `src/api/index.js` 中按分组添加函数，使用 `request()` 基础方法，参考现有接口格式。

### 6.4 添加全局组件

在 `src/components/` 下创建 `.vue`，在 `App.vue` 中按需引入。
