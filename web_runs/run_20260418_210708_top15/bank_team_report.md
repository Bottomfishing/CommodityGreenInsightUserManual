# 油价预测分析报告（企业银行团队版）

- 生成时间：2026-04-18 21:08:37
- 预测步长：H=1（天），窗口：LOOKBACK=30
- 特征选择：RandomForest Top-N=15

## 1. 预测效果（Test）
- MAE：19.1484
- RMSE：19.3776
- MAPE：26.45%
- R2：-15.2113
- 方向预测准确率（排除平盘）：0.4934

## 2. 主要驱动因子（示例 Top-10）
| feature               |   spearman_corr_with_return |   rf_importance |
|:----------------------|----------------------------:|----------------:|
| WTI_Futures_Lag2      |                  -0.167443  |     0.0682631   |
| WTI_Futures_Lag1      |                  -0.151081  |     0.104787    |
| WTI_Futures_MA_5      |                  -0.145036  |     0.0835619   |
| WTI_Futures           |                  -0.143415  |     0.344622    |
| WTI_Futures_MA_10     |                  -0.124335  |     0.0813501   |
| Inventory_Price_Ratio |                   0.121029  |     0.109005    |
| MACD                  |                  -0.109492  |     0.000376439 |
| WTI_Spot              |                  -0.0947917 |     0.00101942  |
| BB_Upper_20           |                  -0.0937476 |     0.0026505   |
| WTI_Futures_MA_20     |                  -0.0919618 |     0.0136203   |

- 图表：`top_drivers_spearman.png`、`top_drivers_rf_importance.png`

## 3. 风险区间与信号
- 风险区间：按 |预测收益| 分位数划分（LOW/MEDIUM/HIGH）
- 信号：LONG / SHORT / FLAT（阈值来自预测收益幅度）
- 图表：`direction_confusion_matrix.png`

## 4. 简单回测（信号驱动）
|   Strategy_TotalReturn |   BuyHold_TotalReturn |   Strategy_MaxDrawdown |   Strategy_WinRate |   Signal_Threshold |
|-----------------------:|----------------------:|-----------------------:|-------------------:|-------------------:|
|              0.0190709 |             -0.018714 |              -0.268932 |           0.475949 |           0.154583 |

- 图表：`backtest_nav_curve.png`

## 5. 风险提示（概要）
- 模型预测用于短期风险识别与情景提示，不构成投资建议。
- 当风险区间为 HIGH 且信号为 LONG/SHORT 时，建议结合库存/宏观/地缘事件进行人工复核。
- 建议与基准（随机游走/简单技术指标）并行监控，避免过拟合与结构性突变风险。

## 6. 输出文件清单
- `prediction_results.csv`：对齐后的预测/真实/收益
- `daily_predictions_vs_actual.csv`：每日预测 vs 真实（含误差）
- `driver_factor_analysis.csv`：驱动因子量化（相关性+RF重要性）
- `risk_signal_classification.csv`：风险区间+信号分类
- `backtest_results.csv`、`backtest_metrics.csv`：回测结果与指标
- 图：`gru_predictions.png`、`gru_returns.png`、`direction_prediction.png`、`top_drivers_*.png`、`direction_confusion_matrix.png`、`backtest_nav_curve.png`