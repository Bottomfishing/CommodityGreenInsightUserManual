# 油价预测分析报告（企业银行团队版）

- 生成时间：2026-04-20 12:32:47
- 预测步长：H=1（天），多尺度窗口：5/20/60 日
- 特征选择：RandomForest Top-N=35 + 强制趋势列

## 1. 预测效果（Test）
- MAE：1.3832
- RMSE：1.8354
- MAPE：1.91%
- R2：0.8342
- 方向预测准确率（排除平盘）：0.4985

## 2. 主要驱动因子（示例 Top-10）
| feature                  |   spearman_corr_with_return |   rf_importance |
|:-------------------------|----------------------------:|----------------:|
| WTI_Futures              |                  -0.162297  |       0.0306356 |
| RSI_14                   |                  -0.160175  |       0.0185902 |
| WTI_Futures_vs_MA_10     |                  -0.131041  |       0.0188426 |
| WTI_Futures_RollRet_5    |                  -0.102597  |       0.0160534 |
| WTI_Futures_Momentum_5d  |                  -0.102597  |       0.01422   |
| MACD                     |                  -0.0895387 |       0.0371241 |
| WTI_Spot                 |                  -0.0816238 |       0.026691  |
| OVX_Return               |                  -0.0747871 |       0.0239763 |
| WTI_Futures_Acceleration |                   0.0739671 |       0.0228253 |
| OVX_Change               |                  -0.068375  |       0.0215841 |

- 图表：`top_drivers_spearman.png`、`top_drivers_rf_importance.png`

## 3. 风险区间与信号
- 风险区间：按 |预测收益| 分位数划分（LOW/MEDIUM/HIGH）
- 信号：LONG / SHORT / FLAT（阈值来自预测收益幅度）
- 图表：`direction_confusion_matrix.png`

## 4. 简单回测（信号驱动）
|   Strategy_TotalReturn |   BuyHold_TotalReturn |   Strategy_MaxDrawdown |   Strategy_WinRate |   Signal_Threshold |
|-----------------------:|----------------------:|-----------------------:|-------------------:|-------------------:|
|               0.290355 |              0.119422 |              -0.194785 |           0.433333 |         0.00496823 |

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