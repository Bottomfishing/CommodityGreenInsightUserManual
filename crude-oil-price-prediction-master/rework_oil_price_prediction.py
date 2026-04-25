
"""
多变量油价预测主函数（按时间序列最佳实践重构）
整合 raw_data 与能源基本面数据；GRU 多尺度编码，预测远期对数收益并还原价格，
配合方向感知损失与涨跌辅助头，改善方向一致性。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor

import tensorflow as tf
import json
import os
import random
import argparse
import ast
import threading
import time
from pathlib import Path
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    LSTM,
    GRU,
    Dense,
    Dropout,
    Input,
    Concatenate,
    Conv1D,
    GaussianNoise,
    Add,
    Layer,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import Callback, CSVLogger, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.losses import Huber

from scipy.stats import spearmanr, zscore, kurtosis as scipy_kurtosis
from scipy.stats.mstats import winsorize

# 尝试导入 LightGBM，如果没有则用 RandomForest
try:
    import lightgbm as lgb
    USE_LIGHTGBM = True
except ImportError:
    USE_LIGHTGBM = False

try:
    import optuna
except Exception:
    optuna = None

os.environ["PYTHONHASHSEED"] = "42"
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)
os.environ["TF_DETERMINISTIC_OPS"] = "1"
os.environ["TF_CUDNN_DETERMINISTIC"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 默认参数（按截图建议） ====================
# 多尺度窗口：短/中/长（与 GRU 三支路一致）；序列长度取长窗口
WINDOW_SHORT = 5
WINDOW_MID = 20
WINDOW_LONG = 60
LOOKBACK_L = WINDOW_LONG  # 与最长窗口一致，供 CLI/报告兼容
HORIZON_H = 1    # 预测未来第 H 天（例如 20）
MISSING_RATE_THRESHOLD = 0.3  # 缺失率阈值
COLLINEARITY_THRESHOLD = 0.95  # 共线性阈值
WALK_FORWARD_FOLDS = 5  # Walk-forward 折数
INITIAL_TOP_N = 30  # 初始选择 Top N
FINAL_FEATURE_N = 20  # 最终特征数（15-25范围）
MIN_SELECTED_FEATURES = 5  # walk-forward 选择过少时的最小保底特征数

# ==================== 特征选择：随机森林 Top-N（替代共线性+Walk-forward） ====================
USE_RF_FEATURE_SELECTION = True
RF_TOP_N_DEFAULT = 35        # 默认保留 Top-N 特征（提升以缓解欠拟合，可在运行时输入覆盖）
RF_N_ESTIMATORS = 100        # 树的数量（与 huaqibeizz 版本保持一致）
RF_RANDOM_STATE = 42
# 随机森林重要性“拟合用的数据范围”
# - 'train': 只用训练集拟合（更严格、避免信息泄露）
# - 'all'  : 用处理后的整段数据拟合（更像 huaqibeizz 的 data_final 做法，会有信息泄露风险）
RF_FIT_SCOPE = 'train'

# 显式按日期划分 Train / Val / Test（可根据需要调整）
TRAIN_END_DATE = '2020-12-31'
VAL_END_DATE = '2022-12-31'  # (TRAIN_END_DATE, VAL_END_DATE] 为验证集，其余为测试集
# 预测目标：远期对数收益 log(P_{t+H}/P_t)，避免直接回归裸价（随机游走）
TARGET_COL = 'WTI_Fwd_LogReturn_H'
# RF 强制保留的趋势/时序类特征（存在则必入，避免 RF 砍掉长程依赖）
MANDATORY_RF_FEATURES = [
    'WTI_Futures',  # 原价列：评估与价格还原必需；未进 Top-N 也会强制留在表中
    'WTI_Futures_Return',
    'WTI_Futures_Change',
    'WTI_Futures_Momentum_3d',
    'WTI_Futures_Momentum_5d',
    'WTI_Futures_Momentum_20d',
    'WTI_Futures_RollRet_5',
    'WTI_Futures_RollRet_20',
    'WTI_Futures_RollRet_60',
    'Volatility_5d',
    'Volatility_20d',
    'DXY_Return',
    'RSI_14',
    'MACD',
]
# 方向感知损失中 Huber 与方向项的权重（略提高分类/方向相对回归的权重）
DIRECTION_LOSS_LAMBDA = 0.48
# 分类头默认权重降低：先把回归(收益)做稳，再用 Optuna/CLI 把分类拉起来
MULTITASK_CLS_WEIGHT = 0.20
USE_CNN_FRONT = True  # 浅层 Conv1D 局部编码后再接 GRU（仅长窗；与 USE_TCN_STACK 二选一优先 TCN）
USE_TCN_STACK = True  # 因果膨胀卷积 TCN 栈（长窗支路优先于 USE_CNN_FRONT）
USE_ATTENTION_POOL_LONG = True  # 长窗末层 GRU 输出序列 + 时间注意力池化
USE_EXPLICIT_BASE_LOG_PRICE = True  # 显式输入 log(P_t)（缩放），与随机游走水平对齐
USE_RESIDUAL_TARGET = True  # 回归头拟合「相对 0 远期收益」的缩放残差，预测时再叠回 scaler 零点

# ===== 标签分解：VMD（Variational Mode Decomposition）=====
# 将收益标签 y(t) 分解成 K 个模态分量，再由模型分别预测各分量，最后求和得到总收益。
# 注意：VMD 这里对 train/val/test 各自独立分解，避免跨段信息泄露（但会牺牲“同一套模态基”的一致性）。
USE_VMD_LABEL = True
VMD_K = 4
VMD_ALPHA = 2000.0
VMD_TAU = 0.0
VMD_DC = 0
VMD_INIT = 1
VMD_TOL = 1e-7

# ===== 正则与训练期序列增强（缓解 Train↓Val↑ 过拟合）=====
DROPOUT_GRU_STACK = 0.30
RECURRENT_DROPOUT_GRU = 0.20
GAUSSIAN_NOISE_INPUT = 0.05  # MinMax 后特征约 [0,1]；仅训练阶段生效
# 训练集：除原始窗外再拼接多份「加高斯噪声」的副本，等效大幅扩增样本量
TRAIN_SEQ_AUG_COPIES = 4
TRAIN_SEQ_AUG_NOISE_STD = 0.09
TRAIN_SEQ_AUG_SEED = 42
# 正式训练（非 Optuna trial）在 val_loss 上早停：更快截断过拟合
FORMAL_EARLY_STOPPING_PATIENCE = 10

LIVE_LOSS_JSON = "training_loss_live.json"


class LiveLossJsonCallback(Callback):
    """每个 epoch 结束将 train/val 总 loss 写入 JSON，供简易 Web 轮询刷新。"""

    def __init__(self, json_path: str):
        super().__init__()
        self.json_path = json_path
        self.epochs = []
        self.train_loss = []
        self.val_loss = []

    def on_train_begin(self, logs=None):
        self.epochs.clear()
        self.train_loss.clear()
        self.val_loss.clear()
        self._flush(
            {
                "epochs": [],
                "train_loss": [],
                "val_loss": [],
                "status": "training",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        self.epochs.append(int(epoch) + 1)
        tl, vl = logs.get("loss"), logs.get("val_loss")
        self.train_loss.append(None if tl is None else float(tl))
        self.val_loss.append(None if vl is None else float(vl))
        self._flush(
            {
                "epochs": self.epochs.copy(),
                "train_loss": self.train_loss.copy(),
                "val_loss": self.val_loss.copy(),
                "status": "training",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    def on_train_end(self, logs=None):
        payload = {
            "epochs": self.epochs.copy(),
            "train_loss": self.train_loss.copy(),
            "val_loss": self.val_loss.copy(),
            "status": "done",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._flush(payload)

    def _flush(self, payload: dict) -> None:
        path = self.json_path
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, path)
        except OSError:
            pass


class OptunaPruningCallback(Callback):
    """将 Keras val_loss 报告给 Optuna，用于 MedianPruner 等剪枝。"""

    def __init__(self, trial, monitor: str = "val_loss"):
        super().__init__()
        self.trial = trial
        self.monitor = monitor

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        value = logs.get(self.monitor)
        if value is None:
            return
        self.trial.report(float(value), step=int(epoch))
        if self.trial.should_prune():
            raise optuna.TrialPruned()


def _val_metrics_gru(model, data_dict, scaler_y):
    """
    验证集：回归 MAE（缩放空间）、分类头准确率、回归头方向准确率（还原到远期对数收益后再比符号）。
    """
    Xv = [
        np.asarray(data_dict["X_val_5"], dtype=np.float32),
        np.asarray(data_dict["X_val_20"], dtype=np.float32),
        np.asarray(data_dict["X_val_60"], dtype=np.float32),
    ]
    if data_dict.get("base_val") is not None:
        Xv.append(np.asarray(data_dict["base_val"], dtype=np.float32))
    reg_pred, cls_pred = model.predict(Xv, verbose=0)
    reg_pred = np.asarray(reg_pred)
    cls_prob = np.asarray(cls_pred).ravel()
    yreg = np.asarray(data_dict["y_val_reg"], dtype=np.float32)
    ycls = np.asarray(data_dict["y_val_cls"], dtype=np.float32).ravel()
    # MAE：以“总收益”（分量求和）为准
    yt_sum = np.sum(yreg, axis=1) if yreg.ndim == 2 else yreg.ravel()
    yp_sum = np.sum(reg_pred, axis=1) if reg_pred.ndim == 2 else reg_pred.ravel()
    mae = float(np.mean(np.abs(yp_sum - yt_sum)))
    cls_acc = float(np.mean((cls_prob > 0.5).astype(float) == ycls))
    z0 = data_dict.get("zero_scaled_return")
    if data_dict.get("use_vmd_label") and data_dict.get("scaler_y_vmd") is not None:
        sc = data_dict["scaler_y_vmd"]
        t_comp = sc.inverse_transform(yreg) if yreg.ndim == 2 else sc.inverse_transform(yreg.reshape(-1, 1))
        p_comp = sc.inverse_transform(reg_pred) if reg_pred.ndim == 2 else sc.inverse_transform(reg_pred.reshape(-1, 1))
        true_raw = np.sum(t_comp, axis=1)
        pred_raw = np.sum(p_comp, axis=1)
    else:
        y1 = yt_sum
        p1 = yp_sum
        if z0 is not None:
            y1 = y1 + float(z0)
            p1 = p1 + float(z0)
        true_raw = scaler_y.inverse_transform(y1.reshape(-1, 1)).ravel()
        pred_raw = scaler_y.inverse_transform(p1.reshape(-1, 1)).ravel()
    thr = 1e-6
    true_d = np.where(true_raw > thr, 1, np.where(true_raw < -thr, -1, 0))
    pred_d = np.where(pred_raw > thr, 1, np.where(pred_raw < -thr, -1, 0))
    mask = true_d != 0
    if not np.any(mask):
        dir_acc = float("nan")
    else:
        dir_acc = float(np.mean(true_d[mask] == pred_d[mask]))
    return mae, cls_acc, dir_acc


def _optuna_composite_loss(mae, cls_acc, dir_acc, y_val_reg, w_cls: float, w_dir: float):
    """
    最小化：回归误差（归一化） + 对分类/方向未达标部分的惩罚。
    cls/dir 约 0.5 为随机；提升 cls_acc、dir_acc 会减小 (1-acc) 项。
    """
    scale = float(np.std(np.asarray(y_val_reg, dtype=np.float32).ravel()) + 1e-8)
    mae_norm = float(mae) / scale
    ca = float(cls_acc) if cls_acc is not None and not (isinstance(cls_acc, float) and np.isnan(cls_acc)) else 0.5
    da = float(dir_acc) if dir_acc is not None and not (isinstance(dir_acc, float) and np.isnan(dir_acc)) else 0.5
    return mae_norm + w_cls * (1.0 - ca) + w_dir * (1.0 - da)


def _optuna_sample_trial_params(trial):
    """Optuna trial → build_gru_model / train_model 参数字典。"""
    unit_choices = [16, 24, 32, 48, 64, 96, 128]

    def sample_units(prefix, n_layers):
        vals = []
        for i in range(int(n_layers)):
            vals.append(trial.suggest_categorical(f"{prefix}_u{i+1}", unit_choices))
        return tuple(vals)

    nl5 = trial.suggest_int("num_layers_5", 1, 3)
    nl20 = trial.suggest_int("num_layers_20", 1, 3)
    nl60 = trial.suggest_int("num_layers_60", 1, 3)
    return {
        "units_5": sample_units("b5", nl5),
        "units_20": sample_units("b20", nl20),
        "units_60": sample_units("b60", nl60),
        "dense_units": (
            trial.suggest_int("dense1", 64, 256, step=32),
            trial.suggest_int("dense2", 32, 128, step=16),
        ),
        "dropout": trial.suggest_float("dropout", 0.10, 0.50),
        "learning_rate": trial.suggest_float("learning_rate", 1e-4, 5e-3, log=True),
        "recurrent_dropout": trial.suggest_float("recurrent_dropout", 0.0, 0.30),
        "input_noise_std": trial.suggest_float("input_noise_std", 0.0, 0.15),
        "use_cnn_front": trial.suggest_categorical("use_cnn_front", [True, False]),
        "use_tcn_stack": trial.suggest_categorical("use_tcn_stack", [True, False]),
        "use_attention_pool_long": trial.suggest_categorical("use_attention_pool_long", [True, False]),
        "cls_weight": trial.suggest_float("cls_weight", 0.25, 1.15),
        "direction_lambda": trial.suggest_float("direction_lambda", 0.15, 0.85),
        "huber_delta": trial.suggest_float("huber_delta", 0.3, 2.0),
        "aug_copies": trial.suggest_int("aug_copies", 0, 6),
        "aug_noise_std": trial.suggest_float("aug_noise_std", 0.02, 0.16),
        "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64]),
    }


def _optuna_sample_fe_params(trial):
    """特征工程侧：随机森林 Top-N / 树棵数 / Winsorize 分位 / RF 拟合数据范围。"""
    return {
        "rf_top_n": trial.suggest_int("rf_top_n", 18, 48),
        "rf_n_estimators": trial.suggest_int("rf_n_estimators", 75, 350, step=25),
        "winsor_lower": trial.suggest_float("winsor_lower", 0.0, 0.04),
        "winsor_upper": trial.suggest_float("winsor_upper", 0.96, 0.999),
        "rf_fit_scope": trial.suggest_categorical("rf_fit_scope", ["train", "all"]),
    }


def _optuna_best_params_from_trial(bt):
    """从 study.best_trial 还原与 load_gru_params_from_csv 一致的参数字典（含可选特征工程键）。"""
    p = bt.params
    d = {
        "units_5": tuple(p[f"b5_u{i+1}"] for i in range(p["num_layers_5"])),
        "units_20": tuple(p[f"b20_u{i+1}"] for i in range(p["num_layers_20"])),
        "units_60": tuple(p[f"b60_u{i+1}"] for i in range(p["num_layers_60"])),
        "dense_units": (p["dense1"], p["dense2"]),
        "dropout": p["dropout"],
        "learning_rate": p["learning_rate"],
        "recurrent_dropout": p["recurrent_dropout"],
        "input_noise_std": p["input_noise_std"],
        "use_cnn_front": p["use_cnn_front"],
        "use_tcn_stack": p["use_tcn_stack"],
        "use_attention_pool_long": p["use_attention_pool_long"],
        "cls_weight": p["cls_weight"],
        "direction_lambda": p["direction_lambda"],
        "huber_delta": p["huber_delta"],
        "aug_copies": p["aug_copies"],
        "aug_noise_std": p["aug_noise_std"],
        "batch_size": p["batch_size"],
        "aug_seed": int(RF_RANDOM_STATE),
    }
    if "rf_top_n" in p:
        d["rf_top_n"] = int(p["rf_top_n"])
        d["rf_n_estimators"] = int(p["rf_n_estimators"])
        d["winsor_lower"] = float(p["winsor_lower"])
        d["winsor_upper"] = float(p["winsor_upper"])
        d["rf_fit_scope"] = p["rf_fit_scope"]
    return d


_LOSS_MONITOR_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>训练 Loss 监控</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body { font-family: system-ui, sans-serif; margin: 16px; background: #111827; color: #e5e7eb; }
    h1 { font-size: 1.1rem; font-weight: 600; }
    #meta { font-size: 0.85rem; color: #9ca3af; margin-bottom: 12px; }
    .chart-wrap { background: #1f2937; border-radius: 8px; padding: 12px; max-width: 960px; }
  </style>
</head>
<body>
  <h1>Train / Val Loss（随训练更新）</h1>
  <div id="meta">轮询中…</div>
  <div class="chart-wrap"><canvas id="lossChart" height="100"></canvas></div>
  <script>
    const ctx = document.getElementById('lossChart');
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          { label: 'Train loss', data: [], borderColor: '#60a5fa', tension: 0.1, pointRadius: 2 },
          { label: 'Val loss', data: [], borderColor: '#f97316', tension: 0.1, pointRadius: 2 }
        ]
      },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: 'Epoch' }, ticks: { color: '#9ca3af' } },
          y: { title: { display: true, text: 'Loss' }, ticks: { color: '#9ca3af' } }
        },
        plugins: { legend: { labels: { color: '#e5e7eb' } } }
      }
    });
    async function poll() {
      try {
        const r = await fetch('/api/loss', { cache: 'no-store' });
        const j = await r.json();
        document.getElementById('meta').textContent =
          '状态: ' + (j.status || '-') + ' | 更新: ' + (j.updated_at || '-') +
          ' | Epochs: ' + (j.epochs ? j.epochs.length : 0);
        chart.data.labels = j.epochs || [];
        chart.data.datasets[0].data = j.train_loss || [];
        chart.data.datasets[1].data = j.val_loss || [];
        chart.update('none');
      } catch (e) {
        document.getElementById('meta').textContent = '请求失败: ' + e;
      }
    }
    setInterval(poll, 1000);
    poll();
  </script>
</body>
</html>
"""


def _start_loss_monitor_web_server(output_dir_abs: str, json_name: str, port: int) -> bool:
    """在后台线程启动 Flask，提供 / 与 /api/loss。失败返回 False。"""
    try:
        from flask import Flask, Response
    except ImportError:
        print("[提示] 实时 Loss 网页需要安装 Flask: pip install flask")
        return False

    json_path = os.path.join(output_dir_abs, json_name)

    app = Flask(__name__)

    @app.route("/")
    def _index():
        return Response(_LOSS_MONITOR_PAGE, mimetype="text/html; charset=utf-8")

    @app.route("/api/loss")
    def _api_loss():
        try:
            if os.path.isfile(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    return Response(f.read(), mimetype="application/json; charset=utf-8")
        except OSError:
            pass
        body = json.dumps(
            {
                "epochs": [],
                "train_loss": [],
                "val_loss": [],
                "status": "waiting",
                "updated_at": None,
            },
            ensure_ascii=False,
        )
        return Response(body, mimetype="application/json; charset=utf-8")

    def _run():
        import logging

        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        app.run(host="127.0.0.1", port=int(port), threaded=True, use_reloader=False)

    t = threading.Thread(target=_run, name="loss-monitor", daemon=True)
    t.start()
    time.sleep(0.35)
    print(f"\n>>> Loss 实时监控: http://127.0.0.1:{int(port)}/  （JSON: {json_path}）\n")
    return True


def _save_loss_curve_png(history, save_path: str, show: bool) -> None:
    """训练结束后保存 train/val loss 静态图。"""
    if history is None or not getattr(history, "history", None):
        return
    h = history.history
    if "loss" not in h or "val_loss" not in h:
        return
    plt.figure(figsize=(10, 5))
    plt.plot(h["loss"], label="Train loss", color="#2563eb")
    plt.plot(h["val_loss"], label="Val loss", color="#ea580c")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Train / Val Loss")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()


def _dataframe_to_markdown_safe(df: pd.DataFrame, *, index: bool = False) -> str:
    """DataFrame 写入 Markdown：优先 to_markdown（需 tabulate），否则退回等宽文本块，避免整份报告生成失败。"""
    try:
        return str(df.to_markdown(index=index))
    except Exception:
        text = df.to_string(index=index)
        return "```\n" + text + "\n```"


class OilPriceDataLoader:
    def __init__(self, base_path='.'):
        self.base_path = base_path
        self.raw_data_path = f'{base_path}/raw_data'
        self.energy_data_path = f'{base_path}/能源基本面与下游产业'

    def load_wti_data(self):
        print("加载WTI价格数据...")
        wti_futures = pd.read_csv(f'{self.raw_data_path}/WTI_futuresprice.csv')
        wti_futures['Date'] = pd.to_datetime(wti_futures['Date'])
        wti_futures = wti_futures.rename(columns={'ClosePrice': 'WTI_Futures'})
        wti_futures = wti_futures[['Date', 'WTI_Futures']].set_index('Date')

        try:
            wti_spot = pd.read_excel(f'{self.raw_data_path}/WTI_spotprice.xls')
        except Exception:
            wti_spot = pd.DataFrame(index=wti_futures.index)
            wti_spot['WTI_Spot'] = np.nan

        if not wti_spot.empty and len(wti_spot.columns) > 0:
            if wti_spot.index.name is None and len(wti_spot.columns) >= 2:
                wti_spot.iloc[:, 0] = pd.to_datetime(wti_spot.iloc[:, 0])
                wti_spot = wti_spot.set_index(wti_spot.columns[0])
            price_col = [c for c in wti_spot.columns if 'price' in str(c).lower() or 'close' in str(c).lower()]
            col = price_col[0] if price_col else wti_spot.columns[-1]
            wti_spot = wti_spot[[col]].rename(columns={col: 'WTI_Spot'})
            wti_data = pd.merge(wti_futures, wti_spot, left_index=True, right_index=True, how='outer')
        else:
            wti_data = wti_futures.copy()
            wti_data['WTI_Spot'] = np.nan

        wti_data['Basis'] = wti_data['WTI_Futures'] - wti_data['WTI_Spot']
        return wti_data

    def _load_financial_csv(self, filepath):
        """统一加载金融类CSV（处理首列为日期、可能含表头行'Date'的情况）"""
        df = pd.read_csv(filepath)
        date_col = df.columns[0]
        df = df[df[date_col].astype(str).str.strip().str.lower() != 'date'].copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.rename(columns={date_col: 'Date'}).set_index('Date')
        return df

    def load_financial_data(self):
        print("加载金融数据...")
        financial_data = {}
        dxy = self._load_financial_csv(f'{self.raw_data_path}/DXY_Index.csv')
        close_col = next((c for c in dxy.columns if 'close' in c.lower()), dxy.columns[-1])
        financial_data['DXY'] = dxy[[close_col]].rename(columns={close_col: 'DXY'})
        sp500 = self._load_financial_csv(f'{self.raw_data_path}/SP500_Index.csv')
        close_col = next((c for c in sp500.columns if 'close' in c.lower()), sp500.columns[-1])
        financial_data['SP500'] = sp500[[close_col]].rename(columns={close_col: 'SP500'})
        us10y = self._load_financial_csv(f'{self.raw_data_path}/US10Y_Yield.csv')
        close_col = next((c for c in us10y.columns if 'close' in c.lower()), us10y.columns[-1])
        financial_data['US10Y'] = us10y[[close_col]].rename(columns={close_col: 'US10Y'})
        vix = self._load_financial_csv(f'{self.raw_data_path}/VIX_index.csv')
        close_col = next((c for c in vix.columns if 'close' in c.lower()), vix.columns[-1])
        financial_data['VIX'] = vix[[close_col]].rename(columns={close_col: 'VIX'})
        ovx = self._load_financial_csv(f'{self.raw_data_path}/OVX_index.csv')
        close_col = next((c for c in ovx.columns if 'close' in c.lower()), ovx.columns[-1])
        financial_data['OVX'] = ovx[[close_col]].rename(columns={close_col: 'OVX'})
        result = financial_data['DXY']
        for key in ['SP500', 'US10Y', 'VIX', 'OVX']:
            result = pd.merge(result, financial_data[key], left_index=True, right_index=True, how='outer')
        return result

    def load_supply_data(self):
        print("加载供给侧数据...")
        supply_data = {}
        stocks = pd.read_csv(f'{self.energy_data_path}/一、原油供需情况/美国商业原油库存.csv', skiprows=4)
        stocks.columns = ['Date', 'Stocks']
        stocks['Date'] = pd.to_datetime(stocks['Date'])
        stocks = stocks.set_index('Date').sort_index()
        supply_data['Stocks'] = stocks
        production = pd.read_csv(f'{self.energy_data_path}/一、原油供需情况/美国原油产量周度数据.csv', skiprows=4)
        production.columns = ['Date', 'Production']
        production['Date'] = pd.to_datetime(production['Date'])
        production = production.set_index('Date').sort_index()
        supply_data['Production'] = production
        try:
            rigs = pd.read_excel(f'{self.energy_data_path}/一、原油供需情况/活跃钻井机数量.xlsx')
            date_col = None
            if 'Date' in rigs.columns or '日期' in rigs.columns:
                date_col = 'Date' if 'Date' in rigs.columns else '日期'
            else:
                # 英文表头：日期可能在 Last Count、Date of Prior Count 等列
                for c in ['Last Count', 'Date of Prior Count', 'Date']:
                    if c in rigs.columns:
                        date_col = c
                        break
                if date_col is None:
                    # 找第一列能转为日期的
                    for c in rigs.columns:
                        ser = pd.to_datetime(rigs[c], errors='coerce')
                        if ser.notna().sum() > len(rigs) // 2:
                            date_col = c
                            break
            if date_col is None:
                date_col = rigs.columns[0]
            rigs[date_col] = pd.to_datetime(rigs[date_col], errors='coerce')
            rigs = rigs.dropna(subset=[date_col])
            numeric_cols = rigs.select_dtypes(include=[np.number]).columns
            value_col = 'Count' if 'Count' in numeric_cols else (numeric_cols[0] if len(numeric_cols) > 0 else None)
            if value_col is not None:
                # 同一日期可能多行（多地区），按日期聚合
                rigs_agg = rigs.groupby(rigs[date_col].dt.normalize())[value_col].sum()
                rigs_agg = rigs_agg.sort_index()
                supply_data['Rigs'] = rigs_agg.to_frame(name='Rigs')
                print("  已加载活跃钻井机数量 (Rigs)")
        except Exception as e:
            print(f"  活跃钻井机数量读取失败: {e}")
        result = supply_data['Stocks']
        for key in ['Production', 'Rigs']:
            if key in supply_data:
                result = pd.merge(result, supply_data[key], left_index=True, right_index=True, how='outer')
        return result

    def load_sentiment_data(self):
        try:
            oil_trends = pd.read_csv(f'{self.raw_data_path}/情绪指标/oil price.csv', skiprows=2)
            if '月份' in oil_trends.columns:
                oil_trends['Date'] = pd.to_datetime(oil_trends['月份'] + '-01')
            else:
                oil_trends['Date'] = pd.to_datetime(oil_trends.iloc[:, 0].astype(str) + '-01')
            oil_trends = oil_trends.set_index('Date')
            trend_col = oil_trends.columns[-1]
            oil_trends = oil_trends[[trend_col]].rename(columns={trend_col: 'Oil_Trends'})
            gas_trends = pd.read_csv(f'{self.raw_data_path}/情绪指标/gas price.csv', skiprows=2)
            if '月份' in gas_trends.columns:
                gas_trends['Date'] = pd.to_datetime(gas_trends['月份'] + '-01')
            else:
                gas_trends['Date'] = pd.to_datetime(gas_trends.iloc[:, 0].astype(str) + '-01')
            gas_trends = gas_trends.set_index('Date')
            trend_col = gas_trends.columns[-1]
            gas_trends = gas_trends[[trend_col]].rename(columns={trend_col: 'Gas_Trends'})
            return pd.merge(oil_trends, gas_trends, left_index=True, right_index=True, how='outer')
        except Exception:
            return pd.DataFrame()

    def load_geopolitical_events(self):
        """
        加载地缘大事件（三、地缘大事记.xlsx）。
        表头：事件类型、事件名称、开始日期、关键影响/备注。
        返回 DataFrame：索引为日期，列 GeoEvent（当日有事件=1，无=0），
        若“关键影响/备注”为数值则作为 GeoEvent_Impact，否则均为 1。
        """
        try:
            path = f'{self.energy_data_path}/三、地缘大事记.xlsx'
            raw = pd.read_excel(path, sheet_name=0)
            # 表头：事件类型、事件名称、开始日期、关键影响/备注
            date_col = None
            for c in raw.columns:
                c_str = str(c).strip()
                if c_str == '开始日期':
                    date_col = c
                    break
            if date_col is None:
                date_col = raw.columns[0]
            raw[date_col] = pd.to_datetime(raw[date_col], errors='coerce')
            raw = raw.dropna(subset=[date_col])
            dates = raw[date_col].dt.normalize()
            # 关键影响/备注：若为数值则用作影响程度
            impact_col = None
            for c in raw.columns:
                if str(c).strip() == '关键影响/备注':
                    if pd.api.types.is_numeric_dtype(raw[c]):
                        impact_col = c
                    else:
                        # 尝试转为数值（忽略非数字）
                        ser = pd.to_numeric(raw[c], errors='coerce')
                        if ser.notna().any():
                            raw[c + '_num'] = ser
                            impact_col = c + '_num'
                    break
            out = pd.DataFrame(index=pd.DatetimeIndex(dates.unique()).sort_values())
            out['GeoEvent'] = 1
            if impact_col is not None:
                agg = raw.groupby(dates)[impact_col].max()
                out['GeoEvent_Impact'] = agg.reindex(out.index).fillna(1.0).values
            else:
                out['GeoEvent_Impact'] = 1.0
            print("  已加载地缘大事件 (GeoEvent)，事件日数: {}".format(len(out)))
            return out
        except Exception as e:
            print("  地缘大事件读取失败: {}".format(e))
            return pd.DataFrame()

    def load_all_data(self):
        print("=" * 60)
        print("开始加载所有数据...")
        print("=" * 60)
        wti_data = self.load_wti_data()
        financial_data = self.load_financial_data()
        supply_data = self.load_supply_data()
        sentiment_data = self.load_sentiment_data()
        combined_data = wti_data.copy()
        combined_data = pd.merge(combined_data, financial_data, left_index=True, right_index=True, how='left')
        supply_daily = supply_data.resample('D').ffill()
        combined_data = pd.merge(combined_data, supply_daily, left_index=True, right_index=True, how='left')
        geo_events = self.load_geopolitical_events()
        if not geo_events.empty:
            combined_data = pd.merge(combined_data, geo_events, left_index=True, right_index=True, how='left')
            combined_data['GeoEvent'] = combined_data['GeoEvent'].fillna(0).astype(int)
            combined_data['GeoEvent_Impact'] = combined_data['GeoEvent_Impact'].fillna(0)
        if not sentiment_data.empty:
            sentiment_daily = sentiment_data.resample('D').ffill()
            combined_data = pd.merge(combined_data, sentiment_daily, left_index=True, right_index=True, how='left')
        combined_data = combined_data.sort_index()
        print(f"数据形状: {combined_data.shape}")
        return combined_data


import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ==================== 油价预测专用特征工程类 ====================
class FeatureEngineer:
    """油价预测专用特征工程类 - 严格因果性原则"""
    
    def __init__(self, lookback_windows=[5, 10, 20, 60]):
        """
        初始化
        Args:
            lookback_windows: 回看窗口列表，用于计算滚动特征
        """
        self.lookback_windows = lookback_windows
        
    def create_all_features(self, data, target_price_col='WTI_Futures'):
        """
        创建油价预测所有特征（严格因果）
        
        Args:
            data: 原始数据DataFrame
            target_price_col: 目标价格列名
            
        Returns:
            包含所有特征的DataFrame
        """
        print("开始油价预测特征工程...")
        print(f"输入数据形状: {data.shape}")
        
        # 复制数据避免修改原始数据
        df = data.copy()
        
        # 确保日期索引
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'Date' in df.columns:
                df = df.set_index('Date')
            else:
                raise ValueError("数据必须包含日期索引或'Date'列")
        
        # ==================== 1. 油价自身特征 ====================
        if target_price_col in df.columns:
            print("添加油价自身特征...")
            df = self._add_price_features(df, target_price_col)
        
        # ==================== 2. 金融市场特征 ====================
        print("添加金融市场特征...")
        df = self._add_financial_features(df)
        
        # ==================== 3. 基本面特征 ====================
        print("添加基本面特征...")
        df = self._add_fundamental_features(df)
        
        # ==================== 4. 技术指标特征 ====================
        print("添加技术指标特征...")
        df = self._add_technical_features(df, target_price_col)
        
        # ==================== 5. 波动率特征 ====================
        print("添加波动率特征...")
        df = self._add_volatility_features(df, target_price_col)
        
        # ==================== 6. 市场结构特征 ====================
        print("添加市场结构特征...")
        df = self._add_market_structure_features(df)
        
        # ==================== 7. 季节性特征 ====================
        print("添加季节性特征...")
        df = self._add_seasonal_features(df)
        
        # ==================== 8. 市场情绪特征 ====================
        print("添加市场情绪特征...")
        df = self._add_sentiment_features(df)
        
        # ==================== 8.5 地缘大事件影响特征 ====================
        print("添加地缘大事件影响特征...")
        df = self._add_geopolitical_features(df)
        
        # ==================== 9. 衍生关系特征 ====================
        print("添加衍生关系特征...")
        df = self._add_derived_features(df)
        
        # ==================== 10. 确保因果性 ====================
        print("确保特征因果性...")
        df = self._ensure_causality(df, target_price_col)
        
        print(f"特征工程完成，特征总数: {df.shape[1]}")
        return df
    
    def _add_price_features(self, df, price_col):
        """添加油价自身特征"""
        
        # 1.1 基础价格特征
        if price_col in df.columns:
            # 日收益率（对数）
            df[f'{price_col}_Return'] = np.log(df[price_col] / df[price_col].shift(1))
            
            # 价格变化（绝对）
            df[f'{price_col}_Change'] = df[price_col].diff()
            
            # 价格方向（涨跌）
            df[f'{price_col}_Direction'] = np.sign(df[f'{price_col}_Change'])
            
            # 价格相对水平（Z-score）
            for window in self.lookback_windows:
                mean_col = f'{price_col}_MA_{window}'
                std_col = f'{price_col}_Std_{window}'
                df[mean_col] = df[price_col].rolling(window=window).mean().shift(1)
                df[std_col] = df[price_col].rolling(window=window).std().shift(1)
                eps = 1e-8
                df[f'{price_col}_Z_{window}'] = ((df[price_col] - df[mean_col]) / (df[std_col] + eps)).shift(1)
        
        # 1.2 滞后特征
        if price_col in df.columns:
            for lag in [1, 2, 3, 5, 10, 20]:
                df[f'{price_col}_Lag{lag}'] = df[price_col].shift(lag)
        
        # 1.2b 短期累计收益（高信号特征，用于缓解欠拟合）
        if price_col in df.columns and f'{price_col}_Return' in df.columns:
            for d in [1, 3, 5, 20]:
                df[f'{price_col}_Momentum_{d}d'] = df[f'{price_col}_Return'].rolling(d).sum().shift(1)
            # 显式多尺度滚动累计收益（供 RF 强制保留与 GRU 趋势输入）
            for w in [5, 20, 60]:
                df[f'{price_col}_RollRet_{w}'] = df[f'{price_col}_Return'].rolling(w).sum().shift(1)
        
        # 1.2c 价格加速度（二阶变化）
        if price_col in df.columns and f'{price_col}_Change' in df.columns:
            df[f'{price_col}_Acceleration'] = df[f'{price_col}_Change'].diff().shift(1)
        
        # 1.3 滚动分位数特征
        if price_col in df.columns:
            for window in [20, 60, 120]:
                df[f'{price_col}_Percentile_{window}'] = df[price_col].rolling(window).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == window else np.nan
                ).shift(1)
        
        return df
    
    def _add_financial_features(self, df):
        """添加金融市场特征"""
        
        # 2.1 美元指数特征
        if 'DXY' in df.columns:
            # 美元指数变化
            df['DXY_Return'] = np.log(df['DXY'] / df['DXY'].shift(1))
            df['DXY_Change'] = df['DXY'].diff()
            
            # 美元指数动量
            for window in [5, 10, 20]:
                df[f'DXY_Momentum_{window}'] = df['DXY_Return'].rolling(window).sum().shift(1)
            
            # 美元指数相对水平
            df['DXY_Percentile_60'] = df['DXY'].rolling(60).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == 60 else np.nan
            ).shift(1)
        
        # 2.2 股票市场特征
        if 'SP500' in df.columns:
            # 标普500收益率
            df['SP500_Return'] = np.log(df['SP500'] / df['SP500'].shift(1))
            
            # 股市波动率（VIX）
            if 'VIX' in df.columns:
                df['VIX_Level'] = df['VIX']
                df['VIX_Change'] = df['VIX'].diff()
                df['VIX_Return'] = np.log(df['VIX'] / df['VIX'].shift(1))
                
                # VIX期限结构（如果有不同期限VIX）
                # 这里简化处理
                for window in [5, 10, 20]:
                    df[f'VIX_MA_{window}'] = df['VIX'].rolling(window).mean().shift(1)
        
        # 2.3 利率特征
        if 'US10Y' in df.columns:
            # 10年期美债收益率
            df['US10Y_Change'] = df['US10Y'].diff()
            df['US10Y_Return'] = np.log(df['US10Y'] / df['US10Y'].shift(1))
            
            # 实际利率（如果有通胀数据）
            # 这里简化，假设有通胀预期列
            if 'Inflation_Exp' in df.columns:
                df['Real_Rate'] = df['US10Y'] - df['Inflation_Exp']
                df['Real_Rate_Change'] = df['Real_Rate'].diff()
        
        # 2.4 原油波动率指数
        if 'OVX' in df.columns:
            df['OVX_Level'] = df['OVX']
            df['OVX_Change'] = df['OVX'].diff()
            df['OVX_Return'] = np.log(df['OVX'] / df['OVX'].shift(1))
            
            # OVIX与VIX的比值（原油相对波动率）
            if 'VIX' in df.columns:
                df['OVX_VIX_Ratio'] = (df['OVX'] / df['VIX']).shift(1)
                df['OVX_VIX_Spread'] = (df['OVX'] - df['VIX']).shift(1)
        
        return df
    
    def _add_fundamental_features(self, df):
        """添加基本面特征"""
        
        # 3.1 库存特征
        if 'Stocks' in df.columns:
            # 库存变化
            df['Stocks_Change'] = df['Stocks'].diff()
            df['Stocks_PctChange'] = df['Stocks'].pct_change()
            
            # 库存相对水平（Z-score）
            for window in [20, 60]:
                mean_col = f'Stocks_MA_{window}'
                std_col = f'Stocks_Std_{window}'
                df[mean_col] = df['Stocks'].rolling(window).mean().shift(1)
                df[std_col] = df['Stocks'].rolling(window).std().shift(1)
                eps = 1e-8
                df[f'Stocks_Z_{window}'] = ((df['Stocks'] - df[mean_col]) / (df[std_col] + eps)).shift(1)
            
            # 库存分位数
            df['Stocks_Percentile_60'] = df['Stocks'].rolling(60).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == 60 else np.nan
            ).shift(1)
        
        # 3.2 产量特征
        if 'Production' in df.columns:
            # 产量变化
            df['Production_Change'] = df['Production'].diff()
            df['Production_PctChange'] = df['Production'].pct_change()
            
            # 产量趋势
            for window in [5, 10, 20]:
                df[f'Production_Trend_{window}'] = df['Production'].rolling(window).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == window else np.nan
                ).shift(1)
        
        # 3.3 钻井平台数特征（如果有）
        if 'Rigs' in df.columns:
            df['Rigs_Change'] = df['Rigs'].diff()
            df['Rigs_PctChange'] = df['Rigs'].pct_change()
            
            # 钻井变化领先指标
            df['Rigs_Momentum_4w'] = df['Rigs'].diff(28).shift(1)  # 4周变化
        
        # 3.4 供需平衡特征（如果有需求数据）
        if all(col in df.columns for col in ['Production', 'Demand']):
            df['Supply_Demand_Balance'] = (df['Production'] - df['Demand']).shift(1)
            df['Supply_Demand_Ratio'] = (df['Production'] / df['Demand']).shift(1)
        
        return df
    
    def _add_technical_features(self, df, price_col):
        """添加技术指标特征"""
        
        if price_col not in df.columns:
            return df
        
        # 4.1 移动平均线特征
        ma_windows = [5, 10, 20, 50, 100, 200]
        for window in ma_windows:
            ma_col = f'{price_col}_MA_{window}'
            df[ma_col] = df[price_col].rolling(window).mean().shift(1)
            
            # 价格相对于移动平均的位置
            df[f'{price_col}_vs_MA_{window}'] = (df[price_col] / df[ma_col] - 1).shift(1)
        
        # 4.2 移动平均交叉特征
        if all(f'{price_col}_MA_{w}' in df.columns for w in [5, 20]):
            df[f'{price_col}_MA5_MA20_Cross'] = (
                (df[f'{price_col}_MA_5'] > df[f'{price_col}_MA_20']).astype(int) -
                (df[f'{price_col}_MA_5'] <= df[f'{price_col}_MA_20']).astype(int)
            ).shift(1)
        
        # 4.3 RSI相对强弱指标
        for period in [14, 28]:
            delta = df[price_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs)).shift(1)
        
        # 4.4 MACD指标
        exp1 = df[price_col].ewm(span=12, adjust=False).mean()
        exp2 = df[price_col].ewm(span=26, adjust=False).mean()
        df['MACD'] = (exp1 - exp2).shift(1)
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean().shift(1)
        df['MACD_Histogram'] = (df['MACD'] - df['MACD_Signal']).shift(1)
        
        # 4.5 布林带
        for window in [20, 50]:
            ma = df[price_col].rolling(window).mean()
            std = df[price_col].rolling(window).std()
            df[f'BB_Upper_{window}'] = (ma + 2 * std).shift(1)
            df[f'BB_Lower_{window}'] = (ma - 2 * std).shift(1)
            df[f'BB_Width_{window}'] = ((df[f'BB_Upper_{window}'] - df[f'BB_Lower_{window}']) / ma).shift(1)
            eps = 1e-8
            df[f'BB_Position_{window}'] = ((df[price_col] - ma) / (2 * std + eps)).shift(1)
        
        # 4.6 ATR真实波动幅度
        # 假设有高、低、收盘价
        high_col = 'High' if 'High' in df.columns else price_col
        low_col = 'Low' if 'Low' in df.columns else price_col
        
        tr1 = df[high_col] - df[low_col]
        tr2 = abs(df[high_col] - df[price_col].shift(1))
        tr3 = abs(df[low_col] - df[price_col].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR_14'] = tr.rolling(14).mean().shift(1)
        
        return df
    
    def _add_volatility_features(self, df, price_col):
        """添加波动率特征"""
        
        if price_col not in df.columns:
            return df
        
        # 5.1 历史波动率
        returns = np.log(df[price_col] / df[price_col].shift(1))
        
        for window in [5, 10, 20, 60]:
            # 日波动率
            df[f'Volatility_{window}d'] = returns.rolling(window).std().shift(1)
            
            # 年化波动率
            df[f'Volatility_Annualized_{window}d'] = returns.rolling(window).std() * np.sqrt(252)
            df[f'Volatility_Annualized_{window}d'] = df[f'Volatility_Annualized_{window}d'].shift(1)
            
            # 波动率变化
            if window >= 10:
                df[f'Volatility_Change_{window}d'] = df[f'Volatility_{window}d'].diff().shift(1)
        
        # 5.2 波动率锥（分位数）
        if 'Volatility_20d' in df.columns:
            for window in [20, 60, 120]:
                df[f'Volatility_Percentile_{window}'] = df['Volatility_20d'].rolling(window).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == window else np.nan
                ).shift(1)
        
        # 5.3 波动率偏度与峰度（用 apply+scipy 兼容各版本，避免 rolling.kurtosis 不兼容）
        for window in [20, 60]:
            df[f'Volatility_Skew_{window}'] = returns.rolling(window).skew().shift(1)
            df[f'Volatility_Kurtosis_{window}'] = returns.rolling(window).apply(
                lambda x: scipy_kurtosis(x, nan_policy='omit') if len(x) == window else np.nan
            ).shift(1)
        
        # 5.4 已实现波动率与隐含波动率比较（如果有OVX）
        if 'OVX' in df.columns and 'Volatility_Annualized_20d' in df.columns:
            df['Volatility_Risk_Premium'] = (df['OVX'] - df['Volatility_Annualized_20d']).shift(1)
        
        return df
    
    def _add_market_structure_features(self, df):
        """添加市场结构特征"""
        
        # 6.1 期现结构特征
        if all(col in df.columns for col in ['WTI_Futures', 'WTI_Spot']):
            # 基差（期货-现货）
            df['Basis'] = df['WTI_Futures'] - df['WTI_Spot']
            df['Basis_Change'] = df['Basis'].diff()
            df['Basis_Pct'] = df['Basis'] / df['WTI_Spot']
            
            # 基差方向（Contango/Backwardation）
            df['Market_Structure'] = np.where(df['Basis'] > 0, 1, -1)  # 1:Contango, -1:Backwardation
        
        # 6.2 期限结构特征（仅当存在 CL1/CL2 等多合约数据时）
        if all(col in df.columns for col in ['CL1', 'CL2']):
            df['Term_Spread_1_2'] = (df['CL1'] - df['CL2']).shift(1)
            df['Term_Spread_Pct'] = (df['CL1'] - df['CL2']) / df['CL2']
            df['Term_Spread_Pct'] = df['Term_Spread_Pct'].shift(1)
        
        # 6.3 跨市场价差（如果有Brent）
        if all(col in df.columns for col in ['WTI_Futures', 'Brent']):
            df['WTI_Brent_Spread'] = (df['WTI_Futures'] - df['Brent']).shift(1)
            df['WTI_Brent_Ratio'] = (df['WTI_Futures'] / df['Brent']).shift(1)
        
        # 6.4 裂解价差（如果有成品油价格）
        if all(col in df.columns for col in ['WTI_Futures', 'Gasoline', 'Heating_Oil']):
            df['Crack_Spread_Gasoline'] = (df['Gasoline'] - df['WTI_Futures']).shift(1)
            df['Crack_Spread_Heating'] = (df['Heating_Oil'] - df['WTI_Futures']).shift(1)
        
        return df
    
    def _add_seasonal_features(self, df):
        """添加季节性特征"""
        
        # 7.1 时间特征
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['Week'] = df.index.isocalendar().week
        df['DayOfWeek'] = df.index.dayofweek  # 0=Monday, 6=Sunday
        df['DayOfMonth'] = df.index.day
        df['DayOfYear'] = df.index.dayofyear
        
        # 7.2 季节性哑变量
        df['Is_Month_Start'] = df.index.is_month_start.astype(int)
        df['Is_Month_End'] = df.index.is_month_end.astype(int)
        df['Is_Quarter_Start'] = df.index.is_quarter_start.astype(int)
        df['Is_Quarter_End'] = df.index.is_quarter_end.astype(int)
        df['Is_Year_Start'] = df.index.is_year_start.astype(int)
        df['Is_Year_End'] = df.index.is_year_end.astype(int)
        
        # 7.3 月份效应（原油消费旺季/淡季）
        # 夏季驾驶季节（5-9月）
        df['Summer_Driving_Season'] = df['Month'].isin([5, 6, 7, 8, 9]).astype(int)
        
        # 冬季取暖季节（11-3月）
        df['Winter_Heating_Season'] = df['Month'].isin([11, 12, 1, 2, 3]).astype(int)
        
        # 炼厂维护季节（春季3-4月，秋季9-10月）
        df['Refinery_Maintenance'] = df['Month'].isin([3, 4, 9, 10]).astype(int)
        
        # 7.4 节假日效应（美国主要假期前后）
        # 这里简化处理，实际需要完整的节假日日历
        holiday_months = [1, 7, 12]  # 1月元旦，7月独立日，12月圣诞节
        df['Holiday_Effect'] = df['Month'].isin(holiday_months).astype(int)
        
        # 7.5 星期效应
        df['Is_Monday'] = (df['DayOfWeek'] == 0).astype(int)
        df['Is_Friday'] = (df['DayOfWeek'] == 4).astype(int)
        
        return df
    
    def _add_sentiment_features(self, df):
        """添加市场情绪特征"""
        
        # 8.1 Google Trends情绪指标
        if 'Oil_Trends' in df.columns:
            df['Oil_Search_Trend'] = df['Oil_Trends']
            df['Oil_Search_Change'] = df['Oil_Trends'].diff()
            df['Oil_Search_Momentum'] = df['Oil_Trends'].pct_change(7)  # 周度变化
        
        if 'Gas_Trends' in df.columns:
            df['Gas_Search_Trend'] = df['Gas_Trends']
            df['Gas_Search_Change'] = df['Gas_Trends'].diff()
            
            # 油/气搜索比（相对关注度）
            if 'Oil_Trends' in df.columns:
                df['Oil_Gas_Search_Ratio'] = (df['Oil_Trends'] / df['Gas_Trends']).shift(1)
        
        # 8.2 新闻情绪（如果有新闻数据）
        # 这里简化处理，实际可能需要NLP处理新闻文本
        if 'News_Sentiment' in df.columns:
            df['News_Sentiment_Score'] = df['News_Sentiment']
            df['News_Sentiment_Change'] = df['News_Sentiment'].diff()
            df['News_Sentiment_Momentum'] = df['News_Sentiment'].rolling(5).mean().shift(1)
        
        # 8.3 社交媒体情绪（如果有Twitter数据）
        # 这里简化处理
        if 'Twitter_Sentiment' in df.columns:
            df['Social_Media_Sentiment'] = df['Twitter_Sentiment']
            df['Social_Media_Volatility'] = df['Twitter_Sentiment'].rolling(5).std().shift(1)
        
        return df
    
    def _add_geopolitical_features(self, df):
        """
        添加地缘大事件影响特征（严格因果：仅使用 t-1 及之前信息）。
        - 当日/近N日是否发生事件
        - 距上次事件天数
        - 近N日内最大影响程度（若数据有影响程度列）
        """
        if 'GeoEvent' not in df.columns:
            return df
        # 因果：只用前一日的“是否事件日”
        ev = df['GeoEvent'].shift(1).fillna(0)
        # 当日是否为事件日（滞后 1 期，预测时已知）
        df['GeoEvent_OnDate'] = ev.astype(int)
        # 过去 5/10/20 个交易日内是否发生过事件
        for w in [5, 10, 20]:
            df[f'GeoEvent_Within_{w}d'] = (ev.rolling(window=w, min_periods=1).max().astype(int))
        # 距上次事件的天数（在“事件日”为 0，之后递增，直到下一次事件）
        grp = (ev == 1).cumsum()
        df['GeoEvent_DaysSinceLast'] = grp.groupby(grp).cumcount().astype(float)
        # 若有影响程度，过去 N 日内最大影响（因果：用 shift 后的滚动）
        if 'GeoEvent_Impact' in df.columns:
            imp = df['GeoEvent_Impact'].shift(1).fillna(0)
            for w in [5, 10, 20]:
                df[f'GeoEvent_Impact_Within_{w}d'] = imp.rolling(window=w, min_periods=1).max()
        return df
    
    def _add_derived_features(self, df):
        """添加衍生关系特征"""
        
        # 9.1 油股相关性特征
        if all(col in df.columns for col in ['WTI_Futures_Return', 'SP500_Return']):
            for window in [20, 60]:
                # 滚动相关性
                df[f'Oil_Stock_Correlation_{window}'] = df['WTI_Futures_Return'].rolling(window).corr(
                    df['SP500_Return']
                ).shift(1)
        
        # 9.2 油价与美元相关性
        if all(col in df.columns for col in ['WTI_Futures_Return', 'DXY_Return']):
            for window in [20, 60]:
                df[f'Oil_Dollar_Correlation_{window}'] = df['WTI_Futures_Return'].rolling(window).corr(
                    df['DXY_Return']
                ).shift(1)
        
        # 9.3 油价与利率相关性
        if all(col in df.columns for col in ['WTI_Futures_Return', 'US10Y_Change']):
            for window in [20, 60]:
                df[f'Oil_Rate_Correlation_{window}'] = df['WTI_Futures_Return'].rolling(window).corr(
                    df['US10Y_Change']
                ).shift(1)
        
        # 9.4 库存与价格关系
        if all(col in df.columns for col in ['WTI_Futures', 'Stocks']):
            # 库存价格比
            df['Inventory_Price_Ratio'] = (df['Stocks'] / df['WTI_Futures']).shift(1)
            
            # 库存变化与价格变化相关性
            for window in [20, 60]:
                df[f'Stock_Price_Correlation_{window}'] = df['WTI_Futures_Change'].rolling(window).corr(
                    df['Stocks_Change']
                ).shift(1)
        
        # 9.5 动量一致性特征
        if 'WTI_Futures_Return' in df.columns:
            # 多时间框架动量一致性
            for short, long in [(5, 20), (10, 30), (20, 60)]:
                short_momentum = df['WTI_Futures_Return'].rolling(short).sum()
                long_momentum = df['WTI_Futures_Return'].rolling(long).sum()
                df[f'Momentum_Consistency_{short}_{long}'] = (
                    np.sign(short_momentum) * np.sign(long_momentum)
                ).shift(1)
        
        # 9.6 市场状态特征
        if 'WTI_Futures_Return' in df.columns and 'Volatility_20d' in df.columns:
            # 定义市场状态
            returns_20d = df['WTI_Futures_Return'].rolling(20).sum()
            volatility_level = df['Volatility_20d']
            
            # 高波动上涨
            df['Market_HighVol_Up'] = (
                (returns_20d > returns_20d.rolling(60).mean()) & 
                (volatility_level > volatility_level.rolling(60).mean())
            ).astype(int).shift(1)
            
            # 低波动下跌
            df['Market_LowVol_Down'] = (
                (returns_20d < returns_20d.rolling(60).mean()) & 
                (volatility_level < volatility_level.rolling(60).mean())
            ).astype(int).shift(1)
        
        return df
    
    def _ensure_causality(self, df, target_price_col):
        """
        确保所有特征的因果性（不使用未来信息）。
        注意：各特征方法中已在创建时正确应用了 shift(1)，此处不再重复 shift，
        否则会造成双重滞后（shift(2)），严重削弱预测能力导致欠拟合。
        仅对少数未 shift 的原始级特征（如 VIX_Level、OVX_Level 等）做滞后处理。
        """
        # 仅在创建时未 shift 的列需要在此处 shift（多为"Level"类原始指标）
        cols_need_shift = [
            'VIX_Level', 'OVX_Level', 'Basis', 'Market_Structure',
            'Oil_Search_Trend', 'Gas_Search_Trend', 'Oil_Search_Change', 'Gas_Search_Change'
        ]
        cols_to_shift = [c for c in cols_need_shift if c in df.columns]
        if cols_to_shift:
            print(f"对 {len(cols_to_shift)} 个未滞后特征应用 shift(1): {cols_to_shift[:5]}...")
            for col in cols_to_shift:
                df[col] = df[col].shift(1)
        else:
            print("因果性检查: 各特征已在创建时正确滞后，无需额外 shift")
        return df
    
    def get_feature_categories(self, df):
        """获取特征分类统计"""
        
        categories = {
            '价格特征': [col for col in df.columns if 'WTI_Futures' in col and 'Return' not in col],
            '收益率特征': [col for col in df.columns if 'Return' in col],
            '技术指标': [col for col in df.columns if any(x in col for x in ['RSI', 'MACD', 'BB', 'ATR', 'MA_'])],
            '波动率特征': [col for col in df.columns if 'Volatility' in col],
            '金融市场': [col for col in df.columns if any(x in col for x in ['DXY', 'SP500', 'VIX', 'US10Y', 'OVX'])],
            '基本面': [col for col in df.columns if any(x in col for x in ['Stock', 'Production', 'Demand', 'Rig'])],
            '市场结构': [col for col in df.columns if any(x in col for x in ['Basis', 'Spread', 'Structure', 'Crack'])],
            '季节性': [col for col in df.columns if any(x in col for x in ['Month', 'Quarter', 'Week', 'Day', 'Season'])],
            '情绪特征': [col for col in df.columns if any(x in col for x in ['Trend', 'Sentiment', 'Search'])],
            '地缘大事件': [col for col in df.columns if 'GeoEvent' in col],
            '衍生关系': [col for col in df.columns if any(x in col for x in ['Correlation', 'Consistency', 'Ratio'])],
        }
        
        # 打印统计信息
        print("\n特征分类统计:")
        for category, features in categories.items():
            if features:  # 只显示有特征的类型
                print(f"  {category}: {len(features)}个特征")
        
        return categories


# 真实数据读取与训练入口：见文件末尾 `if __name__ == '__main__'` → main()
# （OilPriceDataLoader.load_all_data → FeatureEngineer.create_all_features）


class DataPreprocessor:
    """数据预处理：按时间序列最佳实践"""

    def handle_missing_values(self, data):
        data = data.copy()

        # 1. 价格类 → ffill
        price_like_cols = [
            c for c in data.columns
            if any(k in c.lower() for k in
                   ['wti', 'dxy', 'sp500', 'vix', 'ovx', 'us10y'])
        ]
        data[price_like_cols] = data[price_like_cols].ffill()

        # 2. 供给类 → ffill
        supply_cols = [
            c for c in data.columns
            if any(k in c.lower() for k in ['stock', 'production', 'rig'])
        ]
        data[supply_cols] = data[supply_cols].ffill()

        # 3. 情绪类 → ffill
        sentiment_cols = [
            c for c in data.columns
            if 'trend' in c.lower()
        ]
        data[sentiment_cols] = data[sentiment_cols].ffill()

        # 4. 宏观慢变量 → ffill（不要插值）
        macro_cols = [
            c for c in data.columns
            if 'macro' in c.lower()
        ]
        data[macro_cols] = data[macro_cols].ffill()

        return data

    def remove_outliers_zscore(self, data, threshold=2.5):
        """
        使用 Z-score 删除异常值（只基于数值列）
        - threshold: |z| 大于该阈值的样本会被视为异常行并删除
        - 建议：只在 Train 段上调用，避免用到未来信息
        """
        numeric = data.select_dtypes(include=[np.number])
        if numeric.empty:
            return data
        z_scores = np.abs(zscore(numeric))
        # 对每一行，所有数值列的 |z| 都小于阈值才保留
        mask = (z_scores < threshold).all(axis=1)
        return data[mask].copy()

    def winsorize_outliers(self, data, lower=0.01, upper=0.99):
        """
        使用分位数截断（Winsorize）替代删行，保留更多样本缓解欠拟合。
        将超出 [lower, upper] 分位数的值截断到边界，而非删除整行。
        """
        data = data.copy()
        numeric = data.select_dtypes(include=[np.number])
        if numeric.empty:
            return data
        for col in numeric.columns:
            try:
                data[col] = winsorize(data[col].values, limits=(lower, 1 - upper))
            except Exception:
                pass
        return data

    def select_features(self, data, target_col='WTI_Futures', method='rf',
                        correlation_threshold=0.4, n_top_lasso=20, n_top_rf=20,
                        force_include=None):
        """
        特征选择：按与目标变量的相关性/重要性选择特征。
        重要：target_col 必须与模型预测目标一致（如远期对数收益 WTI_Fwd_LogReturn_H），
        否则会选出与当前价格相关但与未来收益无关的特征，导致欠拟合。
        
        method:
            'all'         - 使用全部数值特征
            'correlation' - 按 Spearman 相关性过滤
            'lasso'       - 按 Lasso 系数选 Top-N
            'rf'          - 按随机森林重要性选 Top-N
        """
        exclude_cols = [target_col, 'WTI_Spot', 'Basis']
        feature_cols = [
            c for c in data.columns
            if c not in exclude_cols and data[c].dtype in [np.float64, np.int64]
        ]
        if len(feature_cols) == 0:
            return data[[target_col]].copy(), []

        X = data[feature_cols].fillna(0).values
        y = data[target_col].values

        if method == 'correlation':
            correlations = data[feature_cols + [target_col]].corr(method='spearman')[target_col]
            feature_cols = [c for c in feature_cols if abs(correlations[c]) >= correlation_threshold]
            print(f"  相关性过滤: 保留 {len(feature_cols)} 个特征 (|ρ|>={correlation_threshold})")
        elif method == 'lasso':
            from sklearn.linear_model import LassoCV
            model = LassoCV(cv=5, random_state=42).fit(X, y)
            imp = np.abs(model.coef_)
            top_idx = np.argsort(imp)[::-1][:min(n_top_lasso, len(feature_cols))]
            selected = [feature_cols[i] for i in top_idx if imp[i] > 1e-6]
            feature_cols = selected if len(selected) > 0 else [
                feature_cols[i] for i in top_idx[:n_top_lasso]
            ]
            print(f"  Lasso 特征选择: 保留 {len(feature_cols)} 个特征")
        elif method == 'rf':
            model = RandomForestRegressor(n_estimators=RF_N_ESTIMATORS, random_state=RF_RANDOM_STATE).fit(X, y)
            imp = model.feature_importances_
            top_idx = np.argsort(imp)[::-1][:min(n_top_rf, len(feature_cols))]
            feature_cols = [feature_cols[i] for i in top_idx]
            if force_include:
                for col in force_include:
                    if col in data.columns and col not in feature_cols and col not in exclude_cols:
                        feature_cols = [col] + [c for c in feature_cols if c != col]
                print(f"  随机森林特征选择: 保留 {len(feature_cols)} 个特征 (含强制保留 {force_include})")
            else:
                print(f"  随机森林特征选择: 保留 {len(feature_cols)} 个特征")

        if method == 'all':
            print(f"  使用全部特征: 共 {len(feature_cols)} 个")
        if len(feature_cols) == 0:
            feature_cols = [
                c for c in data.columns
                if c not in exclude_cols and data[c].dtype in [np.float64, np.int64]
            ]
        print("  选中特征名称:")
        for i, name in enumerate(feature_cols, 1):
            print(f"    {i:2d}. {name}")
        return data[feature_cols + [target_col]].copy(), feature_cols

    def split_time_series(self, data, train_ratio=0.7, val_ratio=0.15):
        """按时间切分：Train 70%, Val 15%, Test 15%"""
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        data_train = data.iloc[:train_end].copy()
        data_val = data.iloc[train_end:val_end].copy()
        data_test = data.iloc[val_end:].copy()
        return data_train, data_val, data_test

    def split_time_series_by_date(self, data, train_end_date, val_end_date):
        """按日期切分：<=train_end 为 Train，(train_end, val_end] 为 Val，其余为 Test"""
        data = data.sort_index()
        mask_train = data.index <= train_end_date
        mask_val = (data.index > train_end_date) & (data.index <= val_end_date)
        mask_test = data.index > val_end_date
        data_train = data.loc[mask_train].copy()
        data_val = data.loc[mask_val].copy()
        data_test = data.loc[mask_test].copy()
        print(f"按日期切分: Train_end={train_end_date}, Val_end={val_end_date}")
        return data_train, data_val, data_test
    
    def basic_filtering(self, data_train, data_val, data_test, target_col='WTI_Return'):
        """Step 3: 基础过滤（只在训练集上计算统计量）"""
        print("\n=== Step 3: 基础过滤 ===")
        exclude_cols = [target_col, 'WTI_Futures', 'WTI_Spot', 'Basis']
        # 使用 np.number 识别所有数值型特征，避免漏掉 float32/int32 等类型
        feature_cols = [c for c in data_train.columns if c not in exclude_cols and 
                       np.issubdtype(data_train[c].dtype, np.number)]
        
        # 3.1 缺失率过滤
        missing_rates = data_train[feature_cols].isnull().sum() / len(data_train)
        valid_cols = [c for c in feature_cols if missing_rates[c] <= MISSING_RATE_THRESHOLD]
        print(f"  缺失率过滤: {len(feature_cols)} -> {len(valid_cols)} (阈值={MISSING_RATE_THRESHOLD})")
        
        # 3.2 近常数过滤
        near_constant_cols = []
        for col in valid_cols:
            value_counts = data_train[col].value_counts()
            if len(value_counts) > 0:
                max_ratio = value_counts.iloc[0] / len(data_train)
                if max_ratio > 0.99:  # 99% 都是同一个值
                    near_constant_cols.append(col)
        valid_cols = [c for c in valid_cols if c not in near_constant_cols]
        print(f"  近常数过滤: 删除 {len(near_constant_cols)} 个特征")
        
        # 3.3 共线性去重（Spearman 相关性）
        to_remove = set()
        corr_matrix = data_train[valid_cols].corr(method='spearman')
        for i, col1 in enumerate(valid_cols):
            if col1 in to_remove:
                continue
            for j, col2 in enumerate(valid_cols[i+1:], start=i+1):
                if col2 in to_remove:
                    continue
                if abs(corr_matrix.loc[col1, col2]) > COLLINEARITY_THRESHOLD:
                    # 优先保留更原始的驱动因子
                    if any(x in col1.lower() for x in ['dxy', 'stocks', 'production', 'us10y', 'return']):
                        to_remove.add(col2)
                    elif any(x in col2.lower() for x in ['dxy', 'stocks', 'production', 'us10y', 'return']):
                        to_remove.add(col1)
                    else:
                        # 如果都是衍生特征，保留相关性更高的那个
                        corr1 = abs(data_train[[col1, target_col]].corr(method='spearman').loc[col1, target_col])
                        corr2 = abs(data_train[[col2, target_col]].corr(method='spearman').loc[col2, target_col])
                        if corr1 >= corr2:
                            to_remove.add(col2)
                        else:
                            to_remove.add(col1)
        
        final_cols = [c for c in valid_cols if c not in to_remove]
        print(f"  共线性去重: {len(valid_cols)} -> {len(final_cols)} (删除 {len(to_remove)} 个)")
        
        # 应用到所有数据集（保留 WTI_Futures 用于价格还原）
        all_cols = final_cols + [target_col]
        if 'WTI_Futures' in data_train.columns:
            all_cols.append('WTI_Futures')
        return (data_train[all_cols].copy(), 
                data_val[all_cols].copy(), 
                data_test[all_cols].copy(),
                final_cols)

    def rf_feature_selection_top_n(self, data_train, data_val, data_test, target_col,
                                   top_n=20, exclude_cols=None,
                                   n_estimators=300, random_state=42,
                                   keep_also_cols=None,
                                   fit_data=None):
        """
        随机森林特征重要性选择 Top-N（只在 Train 上训练，再同步到 Val/Test）
        - 用途：替代“共线性去重 + walk-forward”
        - 注意：会 drop 掉 Train 中 target 或特征为 NaN 的行来 fit 模型
        """
        print(f"\n=== Step 3: 随机森林特征选择 Top-{top_n} ===")
        if exclude_cols is None:
            exclude_cols = []
        if keep_also_cols is None:
            keep_also_cols = []

        fit_df = fit_data if fit_data is not None else data_train

        # 仅保留数值型特征，并排除目标/价格等列（以 fit_df 的列为准）
        # 与 huaqibeizz 版本保持一致：只用 float64 / int64 两类
        feature_cols = [
            c for c in fit_df.columns
            if c not in set(exclude_cols + [target_col])
            and fit_df[c].dtype in [np.float64, np.int64]
        ]
        if len(feature_cols) == 0:
            raise ValueError("随机森林特征选择：未找到可用的数值型特征列。")

        # 训练数据：与 huaqibeizz 一致，特征用 fillna(0)，不额外 drop 行
        X_train = fit_df[feature_cols].fillna(0).values
        y_train = fit_df[target_col].values

        # 训练随机森林
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=1
        )
        model.fit(X_train, y_train)

        importances = np.array(model.feature_importances_)
        top_n = min(int(top_n), len(feature_cols))
        top_idx = np.argsort(importances)[::-1][:top_n]
        selected_features = [feature_cols[i] for i in top_idx]
        # 强制追加趋势/时序关键列（RF 排序之外，保障长程依赖）
        for col in keep_also_cols:
            if col in feature_cols and col not in selected_features:
                selected_features.append(col)

        print(f"  选中特征数: {len(selected_features)}")
        print("  Top 特征:")
        for i, name in enumerate(selected_features[:min(30, len(selected_features))], 1):
            print(f"    {i:2d}. {name}")

        # 同步到各数据集（保留目标列，并可额外保留一些列用于后续建模，例如未来价格）
        keep_cols = selected_features + [target_col]
        for col in keep_also_cols:
            if col in data_train.columns and col not in keep_cols:
                keep_cols.append(col)

        return (
            data_train[keep_cols].copy(),
            data_val[keep_cols].copy(),
            data_test[keep_cols].copy(),
            selected_features
        )
    
    def permutation_importance(self, model, X_val, y_val, feature_names, metric='mae'):
        """计算 Permutation Importance"""
        if metric == 'mae':
            baseline_error = mean_absolute_error(y_val, model.predict(X_val))
        else:
            baseline_error = mean_squared_error(y_val, model.predict(X_val))
        
        importances = []
        X_val_shuffled = X_val.copy()
        
        for i, col_name in enumerate(feature_names):
            # 打乱第 i 列
            np.random.shuffle(X_val_shuffled[:, i])
            pred_shuffled = model.predict(X_val_shuffled)
            
            if metric == 'mae':
                error_shuffled = mean_absolute_error(y_val, pred_shuffled)
            else:
                error_shuffled = mean_squared_error(y_val, pred_shuffled)
            
            delta_error = error_shuffled - baseline_error
            importances.append(delta_error)
            
            # 恢复
            X_val_shuffled[:, i] = X_val[:, i]
        
        return np.array(importances)
    
    def walk_forward_feature_selection(self, data_train, data_val, target_col='WTI_Return', 
                                       n_folds=WALK_FORWARD_FOLDS, top_n=INITIAL_TOP_N):
        """Step 4: Walk-forward 特征选择（使用 LightGBM/XGBoost）"""
        print(f"\n=== Step 4: Walk-forward 特征选择 ({n_folds} 折) ===")
        
        # 注意：WTI_Futures 在这里仅用于“对齐与评估”，不要把它当成模型输入特征
        feature_cols = [c for c in data_train.columns if c not in [target_col, 'WTI_Futures']]
        # 这里理论上在前面已经做过 ffill().dropna()，如果仍有 NaN，用 dropna() 而不是填 0
        df_train = data_train[feature_cols + [target_col]].dropna().copy()
        X_train = df_train[feature_cols].values
        y_train = df_train[target_col].values
        
        # 创建 walk-forward 折（注意使用清洗后的样本数，以免索引越界）
        n_train = len(X_train)
        fold_size = n_train // (n_folds + 1)
        all_importances = []
        
        for fold in range(n_folds):
            print(f"  处理第 {fold+1}/{n_folds} 折...")
            # 每折的训练和验证段
            train_start = 0
            train_end = (fold + 1) * fold_size
            val_start = train_end
            val_end = min(val_start + fold_size, n_train)
            
            if val_end <= val_start:
                continue
            
            X_fold_train = X_train[train_start:train_end]
            y_fold_train = y_train[train_start:train_end]
            X_fold_val = X_train[val_start:val_end]
            y_fold_val = y_train[val_start:val_end]
            
            # 每个 fold 都要重新 fit scaler
            scaler = MinMaxScaler()
            X_fold_train_scaled = scaler.fit_transform(X_fold_train)
            X_fold_val_scaled = scaler.transform(X_fold_val)
            
            # 训练模型
            if USE_LIGHTGBM:
                model = lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            
            model.fit(X_fold_train_scaled, y_fold_train)
            
            # 计算 Permutation Importance
            importances = self.permutation_importance(
                model, X_fold_val_scaled, y_fold_val, feature_cols, metric='mae'
            )
            all_importances.append(importances)
        
        # 聚合：计算 median 和 P(Δerror>0)
        all_importances = np.array(all_importances)
        median_importance = np.median(all_importances, axis=0)
        p_positive = np.mean(all_importances > 0, axis=0)
        
        # 选择条件：median(Δerror) > 0 且 P(Δerror>0) >= 0.7
        selected_mask = (median_importance > 0) & (p_positive >= 0.7)
        selected_indices = np.where(selected_mask)[0]

        # 如果选得过少（或为空），回退到“按 median_importance 排序的 Top-N”
        if len(selected_indices) < MIN_SELECTED_FEATURES:
            selected_indices = np.argsort(median_importance)[::-1][:top_n]
        else:
            # 按 median_importance 排序，取 top_n
            selected_indices = selected_indices[np.argsort(median_importance[selected_indices])[::-1][:top_n]]
        
        selected_features = [feature_cols[i] for i in selected_indices]
        print(f"  选中 {len(selected_features)} 个特征 (median>0 且 P(>0)>={0.7})")
        
        return selected_features
    
    def forward_selection(self, data_train, data_val, candidate_features, target_col='WTI_Return', 
                         max_features=25):
        """Step 5: 逐步前向选择（可选）"""
        print(f"\n=== Step 5: 逐步前向选择 (最多 {max_features} 个) ===")
        
        selected = []
        # 同样避免把 WTI_Futures 当特征（它只用于对齐/评估）
        remaining = [c for c in candidate_features if c != 'WTI_Futures']
        best_error = float('inf')
        
        # 前面已经做过缺失值处理，这里再次 dropna 兜底，避免用 0 人为造信号
        X_train_full = data_train[remaining + [target_col]].dropna().copy()
        X_val_full = data_val[remaining + [target_col]].dropna().copy()
        
        for step in range(min(max_features, len(remaining))):
            best_feature = None
            best_step_error = float('inf')
            
            for feature in remaining:
                # 尝试加入这个特征
                test_features = selected + [feature]
                X_train_subset = X_train_full[test_features].values
                y_train = X_train_full[target_col].values
                X_val_subset = X_val_full[test_features].values
                y_val = X_val_full[target_col].values
                
                # 重新 fit scaler
                scaler = MinMaxScaler()
                X_train_scaled = scaler.fit_transform(X_train_subset)
                X_val_scaled = scaler.transform(X_val_subset)
                
                # 训练模型
                if USE_LIGHTGBM:
                    model = lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
                else:
                    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
                
                model.fit(X_train_scaled, y_train)
                pred = model.predict(X_val_scaled)
                error = mean_absolute_error(y_val, pred)
                
                if error < best_step_error:
                    best_step_error = error
                    best_feature = feature
            
            # 如果误差不再下降，停止
            if best_step_error >= best_error:
                print(f"  误差不再下降，停止选择 (当前 {len(selected)} 个特征)")
                break
            
            selected.append(best_feature)
            remaining.remove(best_feature)
            best_error = best_step_error
            print(f"  步骤 {step+1}: 加入 {best_feature}, MAE={best_step_error:.4f}")
        
        return selected


_huber_loss = Huber(delta=1.0)


def direction_aware_huber_loss_fn(y_true, y_pred):
    """复合损失：Huber + 软符号方向惩罚（优先对齐涨跌方向）。"""
    h = _huber_loss(y_true, y_pred)
    eps = tf.constant(1e-6, dtype=tf.keras.backend.dtype(y_pred))
    yt = y_true / (tf.abs(y_true) + eps)
    yp = y_pred / (tf.abs(y_pred) + eps)
    dir_pen = tf.reduce_mean(tf.nn.relu(-yt * yp))
    return h + tf.cast(DIRECTION_LOSS_LAMBDA, h.dtype) * dir_pen


def make_direction_aware_huber_loss(direction_lambda: float, huber_delta: float):
    huber = Huber(delta=float(huber_delta))

    def _loss(y_true, y_pred):
        h = huber(y_true, y_pred)
        eps = tf.constant(1e-6, dtype=tf.keras.backend.dtype(y_pred))
        yt = y_true / (tf.abs(y_true) + eps)
        yp = y_pred / (tf.abs(y_pred) + eps)
        dir_pen = tf.reduce_mean(tf.nn.relu(-yt * yp))
        return h + tf.cast(direction_lambda, h.dtype) * dir_pen

    return _loss


def make_direction_aware_huber_loss_sum(direction_lambda: float, huber_delta: float):
    """多维回归：先对最后一维求和，再按总和计算方向感知 Huber。"""
    huber = Huber(delta=float(huber_delta))

    def _loss(y_true, y_pred):
        yt = tf.reduce_sum(y_true, axis=-1, keepdims=True)
        yp = tf.reduce_sum(y_pred, axis=-1, keepdims=True)
        h = huber(yt, yp)
        eps = tf.constant(1e-6, dtype=tf.keras.backend.dtype(yp))
        yt_s = yt / (tf.abs(yt) + eps)
        yp_s = yp / (tf.abs(yp) + eps)
        dir_pen = tf.reduce_mean(tf.nn.relu(-yt_s * yp_s))
        return h + tf.cast(direction_lambda, h.dtype) * dir_pen

    return _loss


def vmd_decompose_1d(
    signal_1d: np.ndarray,
    K: int = 4,
    alpha: float = 2000.0,
    tau: float = 0.0,
    DC: int = 0,
    init: int = 1,
    tol: float = 1e-7,
    max_iter: int = 500,
) -> np.ndarray:
    """
    轻量 VMD（参考 vmdpy 思路，内置实现避免外部依赖）。
    返回 shape=(n, K) 的分量矩阵，每列一个模态；列求和≈原信号。
    """
    f = np.asarray(signal_1d, dtype=np.float64).ravel()
    n = len(f)
    if n < 8 or K <= 1:
        return np.tile(f.reshape(-1, 1), (1, max(1, int(K))))

    # 镜像延拓，减轻边界效应
    half = n // 2
    f_ext = np.concatenate([f[half:0:-1], f, f[-2:-half - 2:-1]], axis=0)
    T = len(f_ext)

    freqs = np.fft.fftfreq(T, d=1.0)
    f_hat = np.fft.fft(f_ext)

    u_hat = np.zeros((K, T), dtype=np.complex128)
    omega = np.zeros(K, dtype=np.float64)
    if init == 1:
        omega = np.linspace(0, 0.5, K, endpoint=False)
    elif init == 2:
        rng = np.random.default_rng(42)
        omega = np.sort(rng.random(K) * 0.5)
    else:
        omega[:] = 0.0

    lam = np.zeros(T, dtype=np.complex128)
    u_hat_prev = np.copy(u_hat)

    alpha_k = float(alpha) * np.ones(K, dtype=np.float64)

    # 只保留正频（解析信号）
    pos_mask = freqs >= 0
    f_hat_plus = np.zeros_like(f_hat)
    f_hat_plus[pos_mask] = f_hat[pos_mask]
    f_hat_plus[~pos_mask] = 0

    for _ in range(int(max_iter)):
        u_sum = np.sum(u_hat, axis=0)
        for k in range(K):
            u_sum_ex = u_sum - u_hat[k]
            rhs = f_hat_plus - u_sum_ex - lam / 2.0
            denom = 1.0 + alpha_k[k] * (freqs - omega[k]) ** 2
            u_hat[k] = rhs / denom

            if DC and k == 0:
                omega[k] = 0.0
            else:
                num = np.sum((freqs[pos_mask]) * (np.abs(u_hat[k][pos_mask]) ** 2))
                den = np.sum(np.abs(u_hat[k][pos_mask]) ** 2) + 1e-12
                omega[k] = float(num / den)

        u_sum = np.sum(u_hat, axis=0)
        lam = lam + tau * (u_sum - f_hat_plus)

        diff = np.linalg.norm(u_hat - u_hat_prev) / (np.linalg.norm(u_hat_prev) + 1e-12)
        u_hat_prev = np.copy(u_hat)
        if diff < float(tol):
            break

    u = np.fft.ifft(u_hat, axis=1).real  # (K, T)
    # 去掉镜像部分
    u = u[:, half:half + n]  # (K, n)
    return u.T  # (n, K)


def _stack_gru_branch(x, units_list, kwargs):
    n = len(units_list)
    out = x
    for i, u in enumerate(units_list):
        out = GRU(int(u), return_sequences=(i < n - 1), **kwargs)(out)
    return out


class TemporalAttentionPooling(Layer):
    """(batch, time, dim) → softmax 权重 → (batch, dim) 上下文向量。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._score = Dense(1, activation=None, use_bias=True)

    def call(self, inputs):
        s = self._score(inputs)
        w = tf.nn.softmax(s, axis=1)
        return tf.reduce_sum(inputs * w, axis=1)


def _stack_gru_branch_attention_pool(x, units_list, kwargs):
    """末层 GRU 保留时间维，再接 TemporalAttentionPooling。"""
    n = len(units_list)
    out = x
    for i, u in enumerate(units_list):
        ret_seq = i < n - 1 or True
        out = GRU(int(u), return_sequences=ret_seq, **kwargs)(out)
    return TemporalAttentionPooling()(out)


def _tcn_dilated_front(x, filters: int = 32, dilations=(1, 2, 4)):
    """因果膨胀卷积残差栈，输出通道 filters（再接 GRU）。"""
    h = Conv1D(filters, 1, padding="same")(x)
    for d in dilations:
        y = Conv1D(filters, 3, padding="causal", dilation_rate=int(d), activation="relu")(h)
        y = Conv1D(filters, 3, padding="causal", dilation_rate=int(d), activation="relu")(y)
        h = Add()([h, y])
    return h


def augment_train_sequences(
    X5: np.ndarray,
    X20: np.ndarray,
    X60: np.ndarray,
    y_reg: np.ndarray,
    y_cls: np.ndarray,
    n_extra_copies: int,
    noise_std: float,
    rng: np.random.Generator,
    clip01: bool = True,
    base_train=None,
):
    """
    训练序列大幅扩增：保留原始样本，再拼接 n_extra_copies 份对特征加高斯噪声的副本（标签不变）。
    特征已 MinMax 到约 [0,1]，默认 clip 回 [0,1]。
    若提供 base_train（显式 log 价缩放），按样本顺序与噪声副本同步复制。
    """
    if n_extra_copies <= 0:
        return X5, X20, X60, y_reg, y_cls, base_train
    xs5, xs20, xs60 = [np.asarray(X5, dtype=np.float32)], [np.asarray(X20, dtype=np.float32)], [np.asarray(X60, dtype=np.float32)]
    yr_list = [np.asarray(y_reg, dtype=np.float32)]
    yc_list = [np.asarray(y_cls, dtype=np.float32)]
    base_list = None
    if base_train is not None:
        base_list = [np.asarray(base_train, dtype=np.float32)]
    for _ in range(int(n_extra_copies)):
        n5 = rng.normal(0.0, noise_std, X5.shape).astype(np.float32)
        n20 = rng.normal(0.0, noise_std, X20.shape).astype(np.float32)
        n60 = rng.normal(0.0, noise_std, X60.shape).astype(np.float32)
        a5 = (X5.astype(np.float32) + n5)
        a20 = (X20.astype(np.float32) + n20)
        a60 = (X60.astype(np.float32) + n60)
        if clip01:
            a5 = np.clip(a5, 0.0, 1.0)
            a20 = np.clip(a20, 0.0, 1.0)
            a60 = np.clip(a60, 0.0, 1.0)
        xs5.append(a5)
        xs20.append(a20)
        xs60.append(a60)
        yr_list.append(np.asarray(y_reg, dtype=np.float32).copy())
        yc_list.append(np.asarray(y_cls, dtype=np.float32).copy())
        if base_list is not None:
            base_list.append(np.asarray(base_train, dtype=np.float32).copy())
    out_base = None if base_list is None else np.concatenate(base_list, axis=0)
    return (
        np.concatenate(xs5, axis=0),
        np.concatenate(xs20, axis=0),
        np.concatenate(xs60, axis=0),
        np.concatenate(yr_list, axis=0),
        np.concatenate(yc_list, axis=0),
        out_base,
    )


class OilPricePredictor:
    def __init__(
        self,
        timesteps=LOOKBACK_L,
        horizon=HORIZON_H,
        w_short=WINDOW_SHORT,
        w_mid=WINDOW_MID,
        w_long=WINDOW_LONG,
    ):
        self.timesteps = int(timesteps)
        self.horizon = horizon
        self.w_short = int(w_short)
        self.w_mid = int(w_mid)
        self.w_long = int(w_long)

    def create_target_forward_return(
        self, data, price_col='WTI_Futures', target_col=TARGET_COL
    ):
        """远期对数收益 log(P_{t+H}/P_t)，平稳目标，利于方向学习。"""
        if price_col not in data.columns:
            return data
        data = data.copy()
        p = data[price_col]
        data[target_col] = np.log(p.shift(-self.horizon) / p)
        return data

    def create_target_price(self, data, price_col='WTI_Futures', target_col=TARGET_COL):
        """兼容旧名：与 create_target_forward_return 一致。"""
        return self.create_target_forward_return(data, price_col=price_col, target_col=target_col)

    def _collect_base_log_prices(self, prices_np: np.ndarray) -> np.ndarray:
        """与 _create_sequences_multiscale 相同下标：样本 k 对应定价日 t 的 log(P_t)。"""
        n = len(prices_np)
        ws, wm, wl = self.w_short, self.w_mid, self.w_long
        out = []
        for i in range(wl, n - self.horizon + 1):
            p = float(prices_np[i - 1])
            out.append(np.log(max(p, 1e-8)))
        return np.asarray(out, dtype=np.float64)

    def prepare_data(
        self,
        data_train,
        data_val,
        data_test,
        feature_cols,
        target_col=TARGET_COL,
        use_explicit_base_log=None,
        use_residual_target=None,
        use_vmd_label=None,
        vmd_k: int = None,
    ):
        """多尺度窗口序列 + 回归/分类双标签（分类标签由未缩放远期收益符号生成）。
        可选：显式 log(P_t) 输入；回归目标为相对「0 远期收益」的缩放残差（USE_RESIDUAL_TARGET）。"""
        if use_explicit_base_log is None:
            use_explicit_base_log = USE_EXPLICIT_BASE_LOG_PRICE
        if use_residual_target is None:
            use_residual_target = USE_RESIDUAL_TARGET
        if use_vmd_label is None:
            use_vmd_label = USE_VMD_LABEL
        if vmd_k is None:
            vmd_k = int(VMD_K)
        use_vmd_label = bool(use_vmd_label)

        # VMD 标签分解时，关闭 residual target（残差偏移是针对“总收益缩放”的，分量缩放下意义不清）
        if use_vmd_label:
            use_residual_target = False

        needed_cols = list(dict.fromkeys(feature_cols + [target_col, 'WTI_Futures']))
        data_train = data_train[needed_cols].dropna().copy()
        data_val = data_val[needed_cols].dropna().copy()
        data_test = data_test[needed_cols].dropna().copy()

        X_train = data_train[feature_cols].values
        y_train_raw = data_train[target_col].values
        X_val = data_val[feature_cols].values
        y_val_raw = data_val[target_col].values
        X_test = data_test[feature_cols].values
        y_test_raw = data_test[target_col].values

        scaler_X = MinMaxScaler(feature_range=(0, 1))
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_val_scaled = scaler_X.transform(X_val)
        X_test_scaled = scaler_X.transform(X_test)
        scaler_y_vmd = None
        if use_vmd_label:
            ytr_comp = vmd_decompose_1d(
                y_train_raw,
                K=int(vmd_k),
                alpha=float(VMD_ALPHA),
                tau=float(VMD_TAU),
                DC=int(VMD_DC),
                init=int(VMD_INIT),
                tol=float(VMD_TOL),
            )
            yva_comp = vmd_decompose_1d(
                y_val_raw,
                K=int(vmd_k),
                alpha=float(VMD_ALPHA),
                tau=float(VMD_TAU),
                DC=int(VMD_DC),
                init=int(VMD_INIT),
                tol=float(VMD_TOL),
            )
            yte_comp = vmd_decompose_1d(
                y_test_raw,
                K=int(vmd_k),
                alpha=float(VMD_ALPHA),
                tau=float(VMD_TAU),
                DC=int(VMD_DC),
                init=int(VMD_INIT),
                tol=float(VMD_TOL),
            )
            scaler_y_vmd = MinMaxScaler(feature_range=(0, 1))
            y_train_scaled = scaler_y_vmd.fit_transform(ytr_comp)
            y_val_scaled = scaler_y_vmd.transform(yva_comp)
            y_test_scaled = scaler_y_vmd.transform(yte_comp)
        else:
            y_train_scaled = scaler_y.fit_transform(y_train_raw.reshape(-1, 1))
            y_val_scaled = scaler_y.transform(y_val_raw.reshape(-1, 1))
            y_test_scaled = scaler_y.transform(y_test_raw.reshape(-1, 1))

        zero_scaled = None
        if use_residual_target and (not use_vmd_label):
            zero_scaled = float(scaler_y.transform([[0.0]])[0, 0])
            y_train_scaled = y_train_scaled - zero_scaled
            y_val_scaled = y_val_scaled - zero_scaled
            y_test_scaled = y_test_scaled - zero_scaled

        wl = self.w_long
        (
            Xtr5,
            Xtr20,
            Xtr60,
            ytr_r,
            ytr_c,
        ) = self._create_sequences_multiscale(X_train_scaled, y_train_scaled, y_train_raw)
        Xva5, Xva20, Xva60, yva_r, yva_c = self._create_sequences_multiscale(
            X_val_scaled, y_val_scaled, y_val_raw
        )
        Xte5, Xte20, Xte60, yte_r, yte_c = self._create_sequences_multiscale(
            X_test_scaled, y_test_scaled, y_test_raw
        )

        price_train = data_train['WTI_Futures'].values
        price_val = data_val['WTI_Futures'].values
        price_test = data_test['WTI_Futures'].values
        test_index = data_test.index
        i_start = wl
        i_end = len(X_test_scaled) - self.horizon + 1
        indices = np.arange(i_start, i_end)
        base_idx = indices - 1
        target_idx = base_idx + self.horizon
        price_test_base = price_test[base_idx]
        price_test_target = price_test[target_idx]
        date_test_base = test_index[base_idx]
        date_test_target = test_index[target_idx]

        scaler_base_log = None
        base_train = base_val = base_test = None
        if use_explicit_base_log:
            scaler_base_log = MinMaxScaler(feature_range=(0, 1))
            bl_tr = self._collect_base_log_prices(price_train).reshape(-1, 1)
            base_train = scaler_base_log.fit_transform(bl_tr).astype(np.float32)
            base_val = scaler_base_log.transform(
                self._collect_base_log_prices(price_val).reshape(-1, 1)
            ).astype(np.float32)
            base_test = scaler_base_log.transform(
                self._collect_base_log_prices(price_test).reshape(-1, 1)
            ).astype(np.float32)

        out = {
            'X_train_5': Xtr5,
            'X_train_20': Xtr20,
            'X_train_60': Xtr60,
            'y_train_reg': ytr_r,
            'y_train_cls': ytr_c,
            'X_val_5': Xva5,
            'X_val_20': Xva20,
            'X_val_60': Xva60,
            'y_val_reg': yva_r,
            'y_val_cls': yva_c,
            'X_test_5': Xte5,
            'X_test_20': Xte20,
            'X_test_60': Xte60,
            'y_test_reg': yte_r,
            'y_test_cls': yte_c,
            'y_test': yte_r,
            'scaler_X': scaler_X,
            'scaler_y': scaler_y,
            'scaler_y_vmd': scaler_y_vmd,
            'price_test_base': price_test_base,
            'price_test_target': price_test_target,
            'date_test_base': date_test_base,
            'date_test_target': date_test_target,
            'feature_cols': feature_cols,
            'use_explicit_base_log': bool(use_explicit_base_log),
            'use_residual_target': bool(use_residual_target),
            'use_vmd_label': bool(use_vmd_label),
            'vmd_k': int(vmd_k),
            'zero_scaled_return': zero_scaled,
            'scaler_base_log': scaler_base_log,
            'base_train': base_train,
            'base_val': base_val,
            'base_test': base_test,
        }
        return out

    def _create_sequences_multiscale(self, X, y_scaled, y_raw_return):
        """多尺度窗口；标签对齐时刻 t=i-1 的远期收益。"""
        ws, wm, wl = self.w_short, self.w_mid, self.w_long
        X5, X20, X60, y_reg, y_cls = [], [], [], [], []
        for i in range(wl, len(X) - self.horizon + 1):
            X5.append(X[i - ws : i])
            X20.append(X[i - wm : i])
            X60.append(X[i - wl : i])
            if y_scaled.ndim == 2 and y_scaled.shape[1] > 1:
                y_reg.append(y_scaled[i - 1, :])
            else:
                y_reg.append(float(y_scaled[i - 1, 0]))
            yr = y_raw_return[i - 1]
            y_cls.append(1.0 if yr > 0.0 else 0.0)
        return (
            np.asarray(X5, dtype=np.float32),
            np.asarray(X20, dtype=np.float32),
            np.asarray(X60, dtype=np.float32),
            np.asarray(y_reg, dtype=np.float32),
            np.asarray(y_cls, dtype=np.float32),
        )

    def _create_sequences(self, X, y):
        """单窗口序列（遗留接口；多尺度请用 _create_sequences_multiscale）。"""
        X_seq, y_seq = [], []
        for i in range(self.timesteps, len(X) - self.horizon + 1):
            X_seq.append(X[i - self.timesteps : i])
            y_seq.append(y[i - 1, 0])
        return np.array(X_seq), np.array(y_seq)

    def build_lstm_model(self, input_shape, units=[256, 128, 64, 32], dropout=0.1, learning_rate=2e-3):
        """LSTM 模型：增大容量、降低 dropout 以缓解欠拟合"""
        model = Sequential()
        for i, unit in enumerate(units):
            return_sequences = (i < len(units) - 1)
            if i == 0:
                model.add(LSTM(units=unit, return_sequences=return_sequences, input_shape=input_shape))
            else:
                model.add(LSTM(units=unit, return_sequences=return_sequences))
            model.add(Dropout(dropout))
        model.add(Dense(32, activation='relu'))
        model.add(Dropout(dropout))
        model.add(Dense(1))
        model.compile(optimizer=Adam(learning_rate=learning_rate), loss=Huber(), metrics=['mae'])
        return model

    def build_gru_model(
        self,
        n_features,
        dropout=None,
        learning_rate=3e-3,
        recurrent_dropout=None,
        input_noise_std=None,
        units_5=None,
        units_20=None,
        units_60=None,
        dense_units=None,
        use_cnn_front=None,
        use_tcn_stack=None,
        use_attention_pool_long=None,
        use_explicit_base_log=None,
        reg_out_dim: int = 1,
        cls_weight=None,
        direction_lambda=None,
        huber_delta=None,
    ):
        """
        多尺度三支路（5/20/60）+ 长窗可选 TCN / 浅层 Conv1D + GRU（可选长窗序列注意力池化）；
        可选显式 log(P_t) 向量与三支路隐状态拼接；
        双输出：reg_head=远期收益（缩放空间，可为相对 0 收益的残差）、cls_head=涨/跌概率。
        """
        if dropout is None:
            dropout = DROPOUT_GRU_STACK
        if recurrent_dropout is None:
            recurrent_dropout = RECURRENT_DROPOUT_GRU
        if input_noise_std is None:
            input_noise_std = GAUSSIAN_NOISE_INPUT
        if units_5 is None:
            units_5 = (48,)
        if units_20 is None:
            units_20 = (96,)
        if units_60 is None:
            units_60 = (128,)
        if dense_units is None:
            dense_units = (128, 64)
        if use_cnn_front is None:
            use_cnn_front = USE_CNN_FRONT
        if use_tcn_stack is None:
            use_tcn_stack = USE_TCN_STACK
        if use_attention_pool_long is None:
            use_attention_pool_long = USE_ATTENTION_POOL_LONG
        if use_explicit_base_log is None:
            use_explicit_base_log = USE_EXPLICIT_BASE_LOG_PRICE
        if cls_weight is None:
            cls_weight = MULTITASK_CLS_WEIGHT
        if direction_lambda is None:
            direction_lambda = DIRECTION_LOSS_LAMBDA
        if huber_delta is None:
            huber_delta = 1.0

        kwargs = dict(
            activation='tanh',
            recurrent_activation='sigmoid',
            recurrent_dropout=float(recurrent_dropout),
            reset_after=True,
        )
        inp5 = Input(shape=(self.w_short, n_features), name='in5')
        inp20 = Input(shape=(self.w_mid, n_features), name='in20')
        inp60 = Input(shape=(self.w_long, n_features), name='in60')
        if float(input_noise_std) > 0:
            x5 = GaussianNoise(float(input_noise_std), name='noise5')(inp5)
            x20 = GaussianNoise(float(input_noise_std), name='noise20')(inp20)
            x60 = GaussianNoise(float(input_noise_std), name='noise60')(inp60)
        else:
            x5, x20, x60 = inp5, inp20, inp60
        if use_tcn_stack:
            c60 = _tcn_dilated_front(x60, filters=32, dilations=(1, 2, 4))
        elif use_cnn_front:
            c60 = Conv1D(32, 3, padding='same', activation='relu')(x60)
            c60 = Conv1D(32, 3, padding='same', activation='relu')(c60)
        else:
            c60 = x60
        if use_attention_pool_long:
            g60 = _stack_gru_branch_attention_pool(c60, units_60, kwargs)
        else:
            g60 = _stack_gru_branch(c60, units_60, kwargs)
        g5 = _stack_gru_branch(x5, units_5, kwargs)
        g20 = _stack_gru_branch(x20, units_20, kwargs)
        merge_inputs = [g5, g20, g60]
        model_inputs = [inp5, inp20, inp60]
        if use_explicit_base_log:
            inp_base = Input(shape=(1,), name='base_log_scaled')
            merge_inputs = merge_inputs + [inp_base]
            model_inputs = model_inputs + [inp_base]
        merged = Concatenate(name='merged')(merge_inputs)

        # 回归专属塔（容量由 dense_units 控制）
        d_reg = Dense(int(dense_units[0]), activation='relu', name='reg_dense1')(merged)
        d_reg = Dropout(float(dropout), name='reg_drop1')(d_reg)
        d_reg = Dense(int(dense_units[1]), activation='relu', name='reg_dense2')(d_reg)
        d_reg = Dropout(float(dropout), name='reg_drop2')(d_reg)
        reg_head = Dense(int(reg_out_dim), activation='linear', name='reg_head')(d_reg)

        # 分类专属塔（每层略宽，便于拟合涨跌边界）
        cls_w0 = int(dense_units[0]) + 32
        cls_w1 = int(dense_units[1]) + 32
        d_cls = Dense(cls_w0, activation='relu', name='cls_dense1')(merged)
        d_cls = Dropout(float(dropout), name='cls_drop1')(d_cls)
        d_cls = Dense(cls_w1, activation='relu', name='cls_dense2')(d_cls)
        d_cls = Dropout(float(dropout), name='cls_drop2')(d_cls)
        cls_head = Dense(1, activation='sigmoid', name='cls_head')(d_cls)
        model = Model(inputs=model_inputs, outputs=[reg_head, cls_head])
        if int(reg_out_dim) > 1:
            reg_loss = make_direction_aware_huber_loss_sum(float(direction_lambda), float(huber_delta))
        else:
            reg_loss = make_direction_aware_huber_loss(float(direction_lambda), float(huber_delta))
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss={
                'reg_head': reg_loss,
                'cls_head': 'binary_crossentropy',
            },
            loss_weights={'reg_head': 1.0, 'cls_head': float(cls_weight)},
            metrics={'reg_head': ['mae'], 'cls_head': ['accuracy']},
        )
        return model

    def train_model(
        self,
        model,
        data_dict,
        epochs=200,
        batch_size=32,
        verbose=1,
        log_path='training_log.csv',
        live_loss_json_path=None,
        aug_copies=None,
        aug_noise_std=None,
        aug_seed=None,
        trial=None,
        early_stopping_patience=None,
    ):
        """多输入 / 双输出训练：学习率衰减 + CSV 日志；可选每 epoch 写 JSON 供 Web 轮询。
        trial 非空时：静默训练、EarlyStopping、Optuna 剪枝，不写 CSV 日志（避免 trial 互相覆盖）。
        trial 为空（正式训练）时：同样启用 EarlyStopping（监控 val_loss，恢复最优权重）。"""
        copies = int(TRAIN_SEQ_AUG_COPIES if aug_copies is None else aug_copies)
        noise_std = float(TRAIN_SEQ_AUG_NOISE_STD if aug_noise_std is None else aug_noise_std)
        seed = int(TRAIN_SEQ_AUG_SEED if aug_seed is None else aug_seed)

        X5 = np.asarray(data_dict['X_train_5'], dtype=np.float32)
        X20 = np.asarray(data_dict['X_train_20'], dtype=np.float32)
        X60 = np.asarray(data_dict['X_train_60'], dtype=np.float32)
        yr0 = np.asarray(data_dict['y_train_reg'], dtype=np.float32)
        yc0 = np.asarray(data_dict['y_train_cls'], dtype=np.float32)
        n_orig = int(len(yr0))
        b0 = data_dict.get('base_train')
        if copies > 0:
            rng = np.random.default_rng(seed)
            X5, X20, X60, yr0, yc0, b0 = augment_train_sequences(
                X5,
                X20,
                X60,
                yr0,
                yc0,
                copies,
                noise_std,
                rng,
                clip01=True,
                base_train=b0,
            )
            if verbose:
                print(
                    f"  训练序列增强: {n_orig} -> {len(yr0)} 条 "
                    f"(+{copies} 份噪声副本, noise_std={noise_std})"
                )
        X_train = [X5, X20, X60]
        if b0 is not None:
            X_train.append(np.asarray(b0, dtype=np.float32))
        y_train = {'reg_head': yr0, 'cls_head': yc0}
        fit_shuffle = bool(copies > 0)
        X_val = [
            data_dict['X_val_5'],
            data_dict['X_val_20'],
            data_dict['X_val_60'],
        ]
        if data_dict.get('base_val') is not None:
            X_val.append(np.asarray(data_dict['base_val'], dtype=np.float32))
        y_val = {
            'reg_head': data_dict['y_val_reg'],
            'cls_head': data_dict['y_val_cls'],
        }
        callbacks = [
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=4,
                min_lr=1e-6,
                verbose=0 if trial is not None else 1,
            ),
        ]
        if log_path:
            callbacks.append(CSVLogger(log_path, append=False))
        if live_loss_json_path:
            callbacks.insert(0, LiveLossJsonCallback(live_loss_json_path))
        if trial is not None:
            callbacks.append(
                EarlyStopping(
                    monitor='val_loss',
                    patience=12,
                    restore_best_weights=True,
                    verbose=0,
                )
            )
            callbacks.append(OptunaPruningCallback(trial, monitor='val_loss'))
        else:
            esp = int(
                FORMAL_EARLY_STOPPING_PATIENCE
                if early_stopping_patience is None
                else early_stopping_patience
            )
            callbacks.append(
                EarlyStopping(
                    monitor='val_loss',
                    patience=max(1, esp),
                    restore_best_weights=True,
                    verbose=1,
                )
            )
        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=0 if trial is not None else verbose,
            shuffle=fit_shuffle,
        )
        return history

    def predict(self, model, X_list):
        """多输入预测；返回 (reg_scaled, cls_prob)。"""
        out = model.predict(X_list, verbose=0)
        if isinstance(out, (list, tuple)):
            return out[0], out[1]
        return out, None

    def predict_return_from_scaled(self, pred_target_scaled, data_dict):
        """把 reg_head 输出（缩放空间）还原成原始对数收益。支持 VMD(K 维) 或单维残差目标。"""
        arr = np.asarray(pred_target_scaled, dtype=np.float64)
        if data_dict.get("use_vmd_label") and data_dict.get("scaler_y_vmd") is not None:
            sc = data_dict["scaler_y_vmd"]
            comp = sc.inverse_transform(arr)  # (n, K)
            return np.sum(comp, axis=1)
        scy = data_dict["scaler_y"]
        z0 = data_dict.get("zero_scaled_return")
        a = arr.reshape(-1, 1)
        if z0 is not None:
            a = a + float(z0)
        return scy.inverse_transform(a).flatten()

    def predict_price(self, pred_target_scaled, scaler_y, zero_scaled_offset=None):
        """兼容旧接口：将归一化后的远期收益还原到原始对数收益尺度。"""
        arr = np.asarray(pred_target_scaled, dtype=np.float64).reshape(-1, 1)
        if zero_scaled_offset is not None:
            arr = arr + float(zero_scaled_offset)
        return scaler_y.inverse_transform(arr).flatten()

    def evaluate(self, y_true_price, y_pred_price, model_name='Model'):
        """评估（在价格上）"""
        mae = mean_absolute_error(y_true_price, y_pred_price)
        rmse = np.sqrt(mean_squared_error(y_true_price, y_pred_price))
        mape = mean_absolute_percentage_error(y_true_price, y_pred_price) * 100
        r2 = r2_score(y_true_price, y_pred_price)
        print(f"\n{model_name} 评估 (价格):")
        print(f"  MAE: {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAPE: {mape:.2f}%")
        print(f"  R2: {r2:.4f}")
        return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2}

    def evaluate_returns(self, y_true_ret, y_pred_ret, model_name='Model'):
        """在对数收益上评估（与价格 R2 互补）。"""
        mae = mean_absolute_error(y_true_ret, y_pred_ret)
        rmse = np.sqrt(mean_squared_error(y_true_ret, y_pred_ret))
        r2 = r2_score(y_true_ret, y_pred_ret)
        print(f"\n{model_name} 评估 (对数收益):")
        print(f"  MAE: {mae:.6f}")
        print(f"  RMSE: {rmse:.6f}")
        print(f"  R2: {r2:.4f}")
        return {'MAE': mae, 'RMSE': rmse, 'R2': r2}

    def plot_predictions(self, y_true, y_pred, model_name='Model', save_path=None, show=True):
        plt.figure(figsize=(15, 6))
        plt.plot(y_true, label='Actual', alpha=0.7)
        plt.plot(y_pred, label='Predicted', alpha=0.7)
        plt.title(f'{model_name} - 油价预测')
        plt.xlabel('时间')
        plt.ylabel('价格')
        plt.legend()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()

    def plot_returns(self, y_true_ret, y_pred_ret, model_name='Model', save_path=None, show=True):
        """画收益（return）对比曲线，便于检查模型学到的涨跌幅"""
        plt.figure(figsize=(15, 6))
        plt.plot(y_true_ret, label='Actual Return', alpha=0.7)
        plt.plot(y_pred_ret, label='Predicted Return', alpha=0.7)
        plt.title(f'{model_name} - 收益预测')
        plt.xlabel('样本序号')
        plt.ylabel('对数收益')
        plt.legend()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()


def _csv_cell_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return bool(v)


def _csv_optional_bool(row, key: str, default: bool) -> bool:
    if key not in row.index or pd.isna(row[key]):
        return default
    return _csv_cell_bool(row[key])


def _default_fe_params(top_n: int) -> dict:
    """与主线默认 RF（未显式传 n_estimators 时方法内默认 300）及 Winsorize 一致。"""
    return {
        "rf_top_n": int(top_n),
        "rf_n_estimators": 300,
        "winsor_lower": 0.01,
        "winsor_upper": 0.99,
        "rf_fit_scope": "train",
    }


def _apply_feature_pipeline(
    preprocessor,
    predictor,
    data_train,
    data_val,
    data_test,
    fe_params: dict,
    mandatory_ok,
    target_col: str,
    vmd_label: bool = None,
    vmd_k: int = None,
):
    """
    随机森林 Top-N 特征选择 + 仅在训练集 Winsorize（与 main Step 4 一致）→ prepare_data。
    rf_fit_scope='all' 时用 Train+Val+Test 拼接数据拟合 RF 重要性（与 RF_FIT_SCOPE='all' 思想一致，有信息泄露风险）。
    """
    scope = str(fe_params.get("rf_fit_scope", "train"))
    if scope == "all":
        fit_data = pd.concat([data_train, data_val, data_test], axis=0).sort_index()
    else:
        fit_data = data_train
    data_train_sel, data_val_sel, data_test_sel, feature_cols = preprocessor.rf_feature_selection_top_n(
        data_train,
        data_val,
        data_test,
        target_col=target_col,
        top_n=int(fe_params["rf_top_n"]),
        n_estimators=int(fe_params["rf_n_estimators"]),
        random_state=RF_RANDOM_STATE,
        keep_also_cols=mandatory_ok,
        fit_data=fit_data,
    )
    wl = float(fe_params.get("winsor_lower", 0.01))
    wu = float(fe_params.get("winsor_upper", 0.99))
    data_train_sel = preprocessor.winsorize_outliers(data_train_sel, lower=wl, upper=wu)
    data_train_sel = data_train_sel.dropna().copy()
    data_val_sel = data_val_sel.dropna().copy()
    data_test_sel = data_test_sel.dropna().copy()
    if vmd_label is None:
        vmd_label = USE_VMD_LABEL
    if vmd_k is None:
        vmd_k = VMD_K
    data_dict = predictor.prepare_data(
        data_train_sel,
        data_val_sel,
        data_test_sel,
        feature_cols,
        target_col=target_col,
        use_vmd_label=bool(vmd_label),
        vmd_k=int(vmd_k),
    )
    n_feat = int(data_dict["X_train_60"].shape[2])
    return data_dict, feature_cols, n_feat, data_train_sel, data_val_sel, data_test_sel


def _write_feature_export_csvs(
    out_path,
    data_train_sel,
    data_val_sel,
    data_test_sel,
    final_features,
    target_col: str,
):
    """all_features_data.csv + model_input_data.csv（与 main 原逻辑一致）。"""
    all_feature_cols = data_train_sel.columns.tolist()
    full_train = data_train_sel[all_feature_cols].copy()
    full_train["Split"] = "train"
    full_val = data_val_sel[all_feature_cols].copy()
    full_val["Split"] = "val"
    full_test = data_test_sel[all_feature_cols].copy()
    full_test["Split"] = "test"
    full_all = pd.concat([full_train, full_val, full_test]).sort_index()
    full_all.reset_index(inplace=True)
    full_all.rename(columns={"index": "Date"}, inplace=True)
    full_all.to_csv(out_path("all_features_data.csv"), index=False)
    print(
        f"\n已保存所有特征总表到 {out_path('all_features_data.csv')}，行数={len(full_all)}，列数={full_all.shape[1]}"
    )
    print(f"\n最终特征数: {len(final_features)}")
    cols_for_model = list(dict.fromkeys(final_features + [target_col, "WTI_Futures"]))
    data_train_filtered = data_train_sel
    data_val_filtered = data_val_sel
    data_test_filtered = data_test_sel
    model_train = data_train_filtered[cols_for_model].dropna().copy()
    model_train["Split"] = "train"
    model_val = data_val_filtered[cols_for_model].dropna().copy()
    model_val["Split"] = "val"
    model_test = data_test_filtered[cols_for_model].dropna().copy()
    model_test["Split"] = "test"
    model_all = pd.concat([model_train, model_val, model_test]).sort_index()
    model_all.reset_index(inplace=True)
    model_all.rename(columns={"index": "Date"}, inplace=True)
    model_all.to_csv(out_path("model_input_data.csv"), index=False)
    print(
        f"\n已保存模型输入总表到 {out_path('model_input_data.csv')}，行数={len(model_all)}，列数={model_all.shape[1]}"
    )


def load_gru_params_from_csv(csv_path: str) -> dict:
    """读取 noise_optuna_best_params.csv 风格的一行超参（与 noise_binary_test 导出格式一致）。"""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"找不到参数文件: {path.resolve()}")
    df = pd.read_csv(path, nrows=1)
    if df.empty:
        raise ValueError(f"空 CSV: {path}")
    row = df.iloc[0]

    def tup(key: str):
        v = row[key]
        return ast.literal_eval(str(v).strip())

    out = {
        "units_5": tup("units_5"),
        "units_20": tup("units_20"),
        "units_60": tup("units_60"),
        "dense_units": tup("dense_units"),
        "dropout": float(row["dropout"]),
        "learning_rate": float(row["learning_rate"]),
        "recurrent_dropout": float(row["recurrent_dropout"]),
        "input_noise_std": float(row["input_noise_std"]),
        "use_cnn_front": _csv_cell_bool(row["use_cnn_front"]),
        "use_tcn_stack": _csv_optional_bool(row, "use_tcn_stack", USE_TCN_STACK),
        "use_attention_pool_long": _csv_optional_bool(row, "use_attention_pool_long", USE_ATTENTION_POOL_LONG),
        "cls_weight": float(row["cls_weight"]),
        "direction_lambda": float(row["direction_lambda"]),
        "huber_delta": float(row["huber_delta"]),
        "aug_copies": int(row["aug_copies"]),
        "aug_noise_std": float(row["aug_noise_std"]),
        "aug_seed": int(row["aug_seed"]),
        "batch_size": int(row["batch_size"]),
    }
    for fe_key in ("rf_top_n", "rf_n_estimators", "winsor_lower", "winsor_upper", "rf_fit_scope"):
        if fe_key in row.index and pd.notna(row[fe_key]):
            if fe_key == "rf_fit_scope":
                out[fe_key] = str(row[fe_key]).strip()
            elif fe_key in ("rf_top_n", "rf_n_estimators"):
                out[fe_key] = int(row[fe_key])
            else:
                out[fe_key] = float(row[fe_key])
    return out


def run_optuna_gru_study(
    predictor,
    preprocessor,
    data_train,
    data_val,
    data_test,
    mandatory_ok,
    out_csv_path: str,
    n_trials: int,
    optuna_epochs: int,
    optuna_timeout: int,
    w_cls: float,
    w_dir: float,
    seed: int,
    tune_fe: bool,
    target_col: str,
    data_dict=None,
    n_feat: int = None,
    vmd_label: bool = None,
    vmd_k: int = None,
):
    """
    Optuna 最小化 composite：val_mae/std + w_cls*(1-cls_acc) + w_dir*(1-dir_acc)。
    tune_fe=True：每个 trial 先搜 RF/Winsorize/拟合范围，再搜 GRU，再 prepare_data（较慢、更全面）。
    tune_fe=False：在固定 data_dict 上只搜 GRU（与旧版一致）。
    """
    if optuna is None:
        raise ImportError("未安装 optuna，请先 pip install optuna")
    if not tune_fe:
        if data_dict is None or n_feat is None:
            raise ValueError("tune_fe=False 时必须传入已构造的 data_dict 与 n_feat")

    def objective(trial):
        tf.keras.backend.clear_session()
        hp = _optuna_sample_trial_params(trial)
        if tune_fe:
            fe = _optuna_sample_fe_params(trial)
            dd, _, nf, _, _, _ = _apply_feature_pipeline(
                preprocessor,
                predictor,
                data_train,
                data_val,
                data_test,
                fe,
                mandatory_ok,
                target_col,
                vmd_label=vmd_label,
                vmd_k=vmd_k,
            )
        else:
            dd = data_dict
            nf = int(n_feat)
        reg_dim = int(dd.get("vmd_k", 1)) if dd.get("use_vmd_label") else 1
        model = predictor.build_gru_model(
            nf,
            dropout=hp["dropout"],
            learning_rate=hp["learning_rate"],
            recurrent_dropout=hp["recurrent_dropout"],
            input_noise_std=hp["input_noise_std"],
            units_5=hp["units_5"],
            units_20=hp["units_20"],
            units_60=hp["units_60"],
            dense_units=hp["dense_units"],
            use_cnn_front=hp["use_cnn_front"],
            use_tcn_stack=hp["use_tcn_stack"],
            use_attention_pool_long=hp["use_attention_pool_long"],
            use_explicit_base_log=bool(dd["use_explicit_base_log"]),
            reg_out_dim=reg_dim,
            cls_weight=hp["cls_weight"],
            direction_lambda=hp["direction_lambda"],
            huber_delta=hp["huber_delta"],
        )
        predictor.train_model(
            model,
            dd,
            epochs=int(optuna_epochs),
            batch_size=int(hp["batch_size"]),
            aug_copies=int(hp["aug_copies"]),
            aug_noise_std=float(hp["aug_noise_std"]),
            aug_seed=int(RF_RANDOM_STATE),
            log_path=None,
            live_loss_json_path=None,
            trial=trial,
        )
        y_val_reg = dd["y_val_reg"]
        mae, cls_acc, dir_acc = _val_metrics_gru(model, dd, dd["scaler_y"])
        loss = _optuna_composite_loss(mae, cls_acc, dir_acc, y_val_reg, w_cls, w_dir)
        trial.set_user_attr("val_reg_mae", mae)
        trial.set_user_attr("val_cls_acc", cls_acc)
        trial.set_user_attr("val_dir_acc", dir_acc)
        return loss

    sampler = optuna.samplers.TPESampler(seed=int(seed))
    pruner = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10)
    study = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        pruner=pruner,
        study_name="rework_gru_multitask_fe" if tune_fe else "rework_gru_multitask",
    )
    print(
        f"\n开始 Optuna：trials={n_trials}, 每 trial(epochs)={optuna_epochs}, "
        f"tune_fe={tune_fe}, "
        f"composite = mae_norm + {w_cls:.3f}*(1-cls_acc) + {w_dir:.3f}*(1-dir_acc)"
    )
    study.optimize(
        objective,
        n_trials=int(n_trials),
        timeout=None if int(optuna_timeout) <= 0 else int(optuna_timeout),
        show_progress_bar=False,
    )
    bt = study.best_trial
    best = _optuna_best_params_from_trial(bt)
    row = {
        "best_composite": bt.value,
        "val_reg_mae": bt.user_attrs.get("val_reg_mae"),
        "val_cls_acc": bt.user_attrs.get("val_cls_acc"),
        "val_dir_acc": bt.user_attrs.get("val_dir_acc"),
        **best,
    }
    pd.DataFrame([row]).to_csv(out_csv_path, index=False, encoding="utf-8-sig")
    print(
        f"Optuna 结束：最优 composite={bt.value:.6f}, trial={bt.number}, "
        f"val_cls_acc={row.get('val_cls_acc')}, val_dir_acc={row.get('val_dir_acc')}, "
        f"已保存 {out_csv_path}"
    )
    return best


def main(base_path='.', top_n=RF_TOP_N_DEFAULT, output_dir='.', no_plots=False,
         cutoff_date=None, forecast_steps=0, epochs: int = 200, monitor_port: int = 0,
         params_csv=None, optuna_trials: int = 0, optuna_epochs: int = 80,
         optuna_timeout: int = 0,          optuna_weight_cls: float = 0.45,
         optuna_weight_dir: float = 0.35, optuna_seed: int = 42, optuna_tune_fe: bool = True,
         early_stopping_patience=None,
         vmd_label=None,
         vmd_k=None):
    print("=" * 80)
    print("多变量油价预测系统（按时间序列最佳实践）")
    print("=" * 80)

    output_dir = output_dir or '.'
    os.makedirs(output_dir, exist_ok=True)
    show_plots = not no_plots
    print(f"结果文件将写入: {os.path.abspath(output_dir)}")

    def out_path(filename: str) -> str:
        return os.path.join(output_dir, filename)
    
    # Step 0: 加载数据
    loader = OilPriceDataLoader(base_path=base_path)
    data = loader.load_all_data()
    
    # Step 1: 特征工程（严格因果）
    feature_engineer = FeatureEngineer()
    data_features = feature_engineer.create_all_features(data, target_price_col='WTI_Futures')

    # Step 1.5: 创建远期对数收益目标（必须在特征选择之前，RF 按与未来收益相关性选特征）
    predictor = OilPricePredictor(timesteps=WINDOW_LONG, horizon=HORIZON_H)
    data_features = predictor.create_target_forward_return(
        data_features, price_col='WTI_Futures', target_col=TARGET_COL
    )

    # Step 2: 在整段数据上做缺失值处理
    preprocessor = DataPreprocessor()
    data_clean = preprocessor.handle_missing_values(data_features)

    # Step 3: 先切分数据
    data_train, data_val, data_test = preprocessor.split_time_series_by_date(
        data_clean, TRAIN_END_DATE, VAL_END_DATE
    )

    print(f"\n数据切分: Train={len(data_train)}, Val={len(data_val)}, Test={len(data_test)}")

    # Step 4: 特征选择（RF）+ Winsorize + 序列；Optuna 同步搜特征工程时先跳过本段
    try:
        n = int(top_n)
    except Exception:
        n = int(RF_TOP_N_DEFAULT)

    mandatory_ok = [c for c in MANDATORY_RF_FEATURES if c in data_train.columns]

    params_early = None
    if params_csv and int(optuna_trials) == 0:
        params_early = load_gru_params_from_csv(params_csv)
        print(f"已从 CSV 预读参数: {Path(params_csv).resolve()}")

    skip_fe_for_optuna = int(optuna_trials) > 0 and optuna_tune_fe
    use_fe_from_csv = params_early is not None and "rf_top_n" in params_early and int(optuna_trials) == 0

    # 统一 VMD 开关（CLI > 常量）
    if vmd_label is None:
        vmd_label = USE_VMD_LABEL
    if vmd_k is None:
        vmd_k = VMD_K
    vmd_label = bool(vmd_label)

    if skip_fe_for_optuna:
        data_dict = None
        n_feat = None
        final_features = None
        feature_cols = None
        data_train_sel = None
        data_val_sel = None
        data_test_sel = None
    elif use_fe_from_csv:
        data_dict, feature_cols, n_feat, data_train_sel, data_val_sel, data_test_sel = _apply_feature_pipeline(
            preprocessor, predictor, data_train, data_val, data_test,
            params_early, mandatory_ok, TARGET_COL,
            vmd_label=vmd_label,
            vmd_k=vmd_k,
        )
        final_features = feature_cols
        print(
            f"\n[CSV 特征工程] rf_top_n={params_early['rf_top_n']}, "
            f"rf_n_estimators={params_early.get('rf_n_estimators')}, "
            f"winsor=({params_early.get('winsor_lower')},{params_early.get('winsor_upper')}), "
            f"rf_fit_scope={params_early.get('rf_fit_scope', 'train')}"
        )
        print(f"\n数据清洗后: Train={len(data_train_sel)}, Val={len(data_val_sel)}, Test={len(data_test_sel)}")
    else:
        data_train_sel, data_val_sel, data_test_sel, feature_cols = \
            preprocessor.rf_feature_selection_top_n(
                data_train,
                data_val,
                data_test,
                target_col=TARGET_COL,
                top_n=int(n),
                keep_also_cols=mandatory_ok,
            )

        # Step 4.1: 只在 Train 上计算 winsorize
        data_train_sel = preprocessor.winsorize_outliers(data_train_sel, lower=0.01, upper=0.99)

        # Step 4.2: dropna
        data_train_sel = data_train_sel.dropna().copy()
        data_val_sel = data_val_sel.dropna().copy()
        data_test_sel = data_test_sel.dropna().copy()
        print(f"\n数据清洗后: Train={len(data_train_sel)}, Val={len(data_val_sel)}, Test={len(data_test_sel)}")
        final_features = feature_cols

    if not skip_fe_for_optuna:
        _write_feature_export_csvs(
            out_path, data_train_sel, data_val_sel, data_test_sel, final_features, TARGET_COL
        )
        if not use_fe_from_csv:
            data_dict = predictor.prepare_data(
                data_train_sel, data_val_sel, data_test_sel,
                final_features,
                target_col=TARGET_COL,
                use_vmd_label=vmd_label,
                vmd_k=int(vmd_k),
            )
            n_feat = int(data_dict["X_train_60"].shape[2])

    # Step 9: 训练模型（目前只保留 GRU，LSTM 暂时注释掉）
    # print("\n训练LSTM...")
    # lstm_model = predictor.build_lstm_model(input_shape, learning_rate=1e-3)
    # predictor.train_model(
    #     lstm_model, data_dict['X_train'], data_dict['y_train'],
    #     data_dict['X_val'], data_dict['y_val']
    # )

    print("\n训练GRU（多尺度 + 方向感知损失 + 涨跌辅助头）...")
    use_base_log_flag = (
        USE_EXPLICIT_BASE_LOG_PRICE
        if data_dict is None
        else bool(data_dict.get("use_explicit_base_log"))
    )
    use_residual_flag = (
        USE_RESIDUAL_TARGET
        if data_dict is None
        else bool(data_dict.get("use_residual_target"))
    )
    print(
        f"  结构开关: TCN长窗={USE_TCN_STACK}, CNN长窗={USE_CNN_FRONT}, 长窗注意力池={USE_ATTENTION_POOL_LONG}, "
        f"显式log(P_t)={use_base_log_flag}, 残差目标(相对0收益)={use_residual_flag}, "
        f"VMD标签={USE_VMD_LABEL} (K={VMD_K})"
    )
    csvp = None
    if int(optuna_trials) > 0:
        if params_csv:
            print("[提示] 已启用 Optuna（--optuna-trials>0），将忽略 --params-csv。")
        csvp = run_optuna_gru_study(
            predictor,
            preprocessor,
            data_train,
            data_val,
            data_test,
            mandatory_ok,
            out_path("rework_optuna_best_params.csv"),
            int(optuna_trials),
            int(optuna_epochs),
            int(optuna_timeout),
            float(optuna_weight_cls),
            float(optuna_weight_dir),
            int(optuna_seed),
            bool(optuna_tune_fe),
            TARGET_COL,
            data_dict=data_dict,
            n_feat=n_feat,
            vmd_label=vmd_label,
            vmd_k=vmd_k,
        )
        if skip_fe_for_optuna:
            fe_d = {k: csvp[k] for k in ("rf_top_n", "rf_n_estimators", "winsor_lower", "winsor_upper", "rf_fit_scope") if k in csvp}
            data_dict, final_features, n_feat, data_train_sel, data_val_sel, data_test_sel = _apply_feature_pipeline(
                preprocessor, predictor, data_train, data_val, data_test,
                fe_d, mandatory_ok, TARGET_COL,
                vmd_label=vmd_label,
                vmd_k=vmd_k,
            )
            # 与主线一致：后续驱动因子分析等处使用 feature_cols；skip_fe 分支此前未赋值会保持为 None
            feature_cols = final_features
            _write_feature_export_csvs(
                out_path, data_train_sel, data_val_sel, data_test_sel, final_features, TARGET_COL
            )
    elif params_early is not None:
        csvp = params_early
        print("使用预读 CSV 中的超参（含 GRU；若含 rf_top_n 则已用于特征工程）。")
    elif params_csv:
        csvp = load_gru_params_from_csv(params_csv)
        print(f"已从 CSV 加载 GRU 超参: {Path(params_csv).resolve()}")

    _dbe = bool(data_dict.get("use_explicit_base_log", USE_EXPLICIT_BASE_LOG_PRICE))
    _reg_dim = int(data_dict.get("vmd_k", 1)) if data_dict.get("use_vmd_label") else 1
    if csvp:
        gru_model = predictor.build_gru_model(
            n_feat,
            dropout=csvp["dropout"],
            learning_rate=csvp["learning_rate"],
            recurrent_dropout=csvp["recurrent_dropout"],
            input_noise_std=csvp["input_noise_std"],
            units_5=csvp["units_5"],
            units_20=csvp["units_20"],
            units_60=csvp["units_60"],
            dense_units=csvp["dense_units"],
            use_cnn_front=csvp["use_cnn_front"],
            use_tcn_stack=csvp.get("use_tcn_stack", USE_TCN_STACK),
            use_attention_pool_long=csvp.get("use_attention_pool_long", USE_ATTENTION_POOL_LONG),
            use_explicit_base_log=_dbe,
            reg_out_dim=_reg_dim,
            cls_weight=csvp["cls_weight"],
            direction_lambda=csvp["direction_lambda"],
            huber_delta=csvp["huber_delta"],
        )
    else:
        gru_model = predictor.build_gru_model(
            n_feat,
            dropout=DROPOUT_GRU_STACK,
            learning_rate=3e-3,
            recurrent_dropout=RECURRENT_DROPOUT_GRU,
            input_noise_std=GAUSSIAN_NOISE_INPUT,
            use_tcn_stack=USE_TCN_STACK,
            use_attention_pool_long=USE_ATTENTION_POOL_LONG,
            use_explicit_base_log=_dbe,
            reg_out_dim=_reg_dim,
        )
    loss_json_abs = os.path.abspath(out_path(LIVE_LOSS_JSON))
    print(f"Train/Val loss 将逐 epoch 写入: {loss_json_abs}")
    mp = int(monitor_port or 0)
    if mp > 0:
        _start_loss_monitor_web_server(os.path.abspath(output_dir), LIVE_LOSS_JSON, mp)
    if csvp:
        history = predictor.train_model(
            gru_model,
            data_dict,
            epochs=int(max(1, int(epochs or 200))),
            batch_size=int(csvp["batch_size"]),
            aug_copies=int(csvp["aug_copies"]),
            aug_noise_std=float(csvp["aug_noise_std"]),
            aug_seed=int(csvp["aug_seed"]),
            log_path=out_path('training_log.csv'),
            live_loss_json_path=loss_json_abs,
            early_stopping_patience=early_stopping_patience,
        )
    else:
        history = predictor.train_model(
            gru_model,
            data_dict,
            epochs=int(max(1, int(epochs or 200))),
            batch_size=32,
            log_path=out_path('training_log.csv'),
            live_loss_json_path=loss_json_abs,
            early_stopping_patience=early_stopping_patience,
        )
    _save_loss_curve_png(history, out_path('loss_curve_train_val.png'), show_plots)

    # Step 10: 预测和评估（回归头：远期收益 → 还原价格）
    X_test_list = [
        data_dict['X_test_5'],
        data_dict['X_test_20'],
        data_dict['X_test_60'],
    ]
    if data_dict.get('base_test') is not None:
        X_test_list.append(data_dict['base_test'])
    reg_scaled, cls_prob = predictor.predict(gru_model, X_test_list)
    gru_pred_scaled = np.asarray(reg_scaled)

    # 使用 prepare_data 中已经对齐好的价格
    test_base_prices = data_dict['price_test_base']
    test_target_prices = data_dict['price_test_target']
    test_base_dates = data_dict['date_test_base']
    test_target_dates = data_dict['date_test_target']

    # 确保长度匹配
    min_len = min(
        len(gru_pred_scaled),
        len(test_base_prices),
        len(test_target_prices),
        len(data_dict['y_test_reg']),
    )
    gru_pred_scaled = gru_pred_scaled[:min_len]
    test_base_prices = test_base_prices[:min_len]
    test_target_prices = test_target_prices[:min_len]
    test_base_dates = test_base_dates[:min_len]
    test_target_dates = test_target_dates[:min_len]

    # 还原为「远期对数收益」尺度，再还原价格：P̂_{t+h} = P_t * exp(r̂)
    gru_pred_return = predictor.predict_return_from_scaled(gru_pred_scaled, data_dict)
    gru_pred_price = test_base_prices * np.exp(gru_pred_return)

    y_test_return = np.log(test_target_prices / test_base_prices)
    if cls_prob is not None:
        pc = (np.asarray(cls_prob).flatten()[:min_len] > 0.5).astype(float)
        ta = data_dict['y_test_cls'][:min_len]
        cls_acc = float(np.mean(pc == ta)) if len(ta) else float("nan")
        print(f"\n涨跌辅助头准确率（阈值 0.5）: {cls_acc:.4f}")

    # Baseline：随机游走（未来价格=当前价格 => return=0）
    baseline_pred_price = test_base_prices.copy()
    baseline_pred_return = np.log(baseline_pred_price / test_base_prices)  # 全 0

    # 评估（在价格上）
    y_test_price = test_target_prices
    # predictor.evaluate(y_test_price, lstm_pred_price, 'LSTM')
    metrics = predictor.evaluate(y_test_price, gru_pred_price, 'GRU')
    ret_metrics = predictor.evaluate_returns(y_test_return, gru_pred_return, 'GRU')

    baseline_rw_ret = np.zeros_like(y_test_return)
    r2_ret_rw = r2_score(y_test_return, baseline_rw_ret)
    print(f"\nBaseline(远期对数收益=0，随机游走) 在对数收益上的 R2: {r2_ret_rw:.4f}")

    # 更强 baseline：AR(1) / 历史均值（都在收益空间对比）
    try:
        p_tr = np.asarray(data_train_sel["WTI_Futures"].values, dtype=np.float64)
        r_tr = np.diff(np.log(np.clip(p_tr, 1e-8, None)))
        mu_tr = float(np.mean(r_tr)) if len(r_tr) else 0.0
        if len(r_tr) >= 3:
            x = r_tr[:-1]
            y = r_tr[1:]
            den = float(np.dot(x, x)) + 1e-12
            phi = float(np.dot(x, y) / den)
        else:
            phi = 0.0
    except Exception:
        mu_tr, phi = 0.0, 0.0
    r_lag = np.concatenate([[0.0], y_test_return[:-1]])
    ar1_pred = phi * r_lag
    mean_pred = np.full_like(y_test_return, mu_tr, dtype=np.float64)
    r2_ret_ar1 = r2_score(y_test_return, ar1_pred)
    r2_ret_mean = r2_score(y_test_return, mean_pred)
    print(f"\nBaseline(AR(1) on returns) R2_ret: {r2_ret_ar1:.4f}  (phi={phi:.3f})")
    print(f"Baseline(收益均值) R2_ret: {r2_ret_mean:.4f}  (mu={mu_tr:.6f})")

    roc_auc_test = None
    if cls_prob is not None:
        try:
            ta = data_dict['y_test_cls'][:min_len]
            cp = np.asarray(cls_prob).flatten()[:min_len]
            if len(np.unique(ta)) >= 2:
                roc_auc_test = float(roc_auc_score(ta, cp))
                print(f"\n涨跌辅助头 ROC-AUC（测试集）: {roc_auc_test:.4f}")
        except Exception:
            pass

    # Direction Accuracy
    threshold = 1e-6
    true_direction = np.where(y_test_return > threshold, 1, np.where(y_test_return < -threshold, -1, 0))
    pred_direction = np.where(gru_pred_return > threshold, 1, np.where(gru_pred_return < -threshold, -1, 0))
    mask = true_direction != 0
    direction_accuracy = np.mean(true_direction[mask] == pred_direction[mask])
    print(f"\n方向预测准确率: {direction_accuracy:.4f}")

    # Direction Plot
    plt.figure(figsize=(12, 4))
    plt.plot(true_direction, label='True Direction')
    plt.plot(pred_direction, label='Pred Direction', alpha=0.7)
    plt.legend()
    plt.title("Direction Prediction")
    plt.xlabel("Sample")
    plt.ylabel("Direction")
    plt.savefig(out_path("direction_prediction.png"), dpi=300, bbox_inches='tight')
    if show_plots:
        plt.show()
    else:
        plt.close()

    # Baseline 对比与 R2 校验
    baseline_r2 = r2_score(y_test_price, baseline_pred_price)
    print(f"\nBaseline(随机游走 P_t) R2: {baseline_r2:.4f}")
    delta_r2_price = float(metrics["R2"] - baseline_r2)
    ret_r2 = float(ret_metrics.get("R2", float("nan")))
    if (delta_r2_price > 0.01) and (ret_r2 > 0.02) and (direction_accuracy > 0.53):
        print(f"  [达标] ΔR2_price={delta_r2_price:.4f}, R2_ret={ret_r2:.4f}, DirAcc={direction_accuracy:.4f}")
    else:
        print(f"  [未达标] ΔR2_price={delta_r2_price:.4f}, R2_ret={ret_r2:.4f}, DirAcc={direction_accuracy:.4f}")

    # 绘图（只画 GRU）
    # predictor.plot_predictions(y_test_price, lstm_pred_price, 'LSTM', 'lstm_predictions.png')
    predictor.plot_predictions(y_test_price, gru_pred_price, 'GRU', out_path('gru_predictions.png'), show=show_plots)
    # 同时画收益曲线对比
    predictor.plot_returns(y_test_return, gru_pred_return, 'GRU', out_path('gru_returns.png'), show=show_plots)
    # predictor.plot_returns(y_test_return, baseline_pred_return, 'Baseline(RW=0)', 'baseline_returns.png')

    # 保存结果
    result_df = pd.DataFrame({
        'Date_base': test_base_dates,
        'Date_target': test_target_dates,
        'BasePrice_P_t': test_base_prices,
        'Actual_P_t_plus_H': y_test_price,
        # 'LSTM_Pred_P_t_plus_H': lstm_pred_price,
        'GRU_Pred_P_t_plus_H': gru_pred_price,
        'Actual_Return': y_test_return,
        'GRU_Pred_Return': gru_pred_return,
    })
    result_df.to_csv(out_path('prediction_results.csv'), index=False)
    # ===== 生成 oil_pred.csv（给 bond 用）=====
    oil_pred_df = result_df[[
        "Date_target",
        "GRU_Pred_P_t_plus_H"
    ]].copy()

    oil_pred_df.columns = ["Date", "Oil_Pred"]

    oil_pred_df.to_csv(
        out_path("oil_pred.csv"),
        index=False
    )

    print("✅ oil_pred.csv 已生成")

    print(f"\n已保存对齐后的预测结果到 {out_path('prediction_results.csv')}，样本数={len(result_df)}")

    # 额外：按“每日目标日期”汇总的精简表（真实值 vs 预测值）
    daily_summary_df = result_df[['Date_target', 'Actual_P_t_plus_H', 'GRU_Pred_P_t_plus_H']].copy()
    daily_summary_df.rename(columns={
        'Date_target': 'Date',
        'Actual_P_t_plus_H': 'Actual',
        'GRU_Pred_P_t_plus_H': 'Pred',
    }, inplace=True)
    # 尽量把日期转成 datetime 便于排序/查看（转不了就保留原样）
    daily_summary_df['Date'] = pd.to_datetime(daily_summary_df['Date'], errors='ignore')
    daily_summary_df.sort_values('Date', inplace=True, kind='stable')
    daily_summary_df.reset_index(drop=True, inplace=True)
    daily_summary_df['Error'] = daily_summary_df['Pred'] - daily_summary_df['Actual']
    daily_summary_df['AbsError'] = daily_summary_df['Error'].abs()
    daily_summary_df.to_csv(out_path('daily_predictions_vs_actual.csv'), index=False, encoding='utf-8-sig')
    print("\n每日预测 vs 真实值（最后 15 行）：")
    print(daily_summary_df.tail(15).to_string(index=False))
    print(f"\n已保存每日汇总表到 {out_path('daily_predictions_vs_actual.csv')}")

    # ======================================================================
    # 补充输出：因子分析 / 风险区间(信号分类) / 回测 / 面向企业银行团队的报告
    # ======================================================================
    print("\n=== 附加分析：驱动因子 / 风险信号 / 回测 / 报告 ===")

    # 1) 驱动因子量化：Spearman 相关性（对数收益） + RF 重要性（对未来价格目标）
    try:
        # RF 重要性（用训练集拟合，避免信息泄露）
        df_rf_train = data_train_sel[feature_cols + [TARGET_COL]].dropna().copy()
        X_rf = df_rf_train[feature_cols].values
        y_rf = df_rf_train[TARGET_COL].values
        rf = RandomForestRegressor(
            n_estimators=RF_N_ESTIMATORS,
            random_state=RF_RANDOM_STATE,
            n_jobs=-1
        )
        rf.fit(X_rf, y_rf)
        rf_importance = pd.Series(rf.feature_importances_, index=feature_cols, name="rf_importance")

        # 相关性：用 test 段对齐到 y_test_return 的样本序列
        # 从 data_dict 里拿到对齐的特征序列索引（date_test_base），用 data_test_sel 对齐取值
        test_feature_df = data_test_sel.copy()
        if isinstance(test_feature_df.index, pd.DatetimeIndex):
            aligned_idx = pd.to_datetime(test_base_dates, errors='coerce')
            aligned_idx = pd.DatetimeIndex(aligned_idx)
            X_test_feat = test_feature_df.reindex(aligned_idx)[feature_cols]
        else:
            X_test_feat = test_feature_df[feature_cols].iloc[:min_len]

        # y_test_return 与 X_test_feat 行对齐
        X_test_feat = X_test_feat.iloc[:min_len].copy()
        corr_rows = []
        for col in feature_cols:
            x = X_test_feat[col].values
            # dropna 对齐
            m = np.isfinite(x) & np.isfinite(y_test_return)
            if m.sum() < 10:
                corr_rows.append((col, np.nan, np.nan))
            else:
                r, p = spearmanr(x[m], y_test_return[m])
                corr_rows.append((col, float(r), float(p)))
        corr_df = pd.DataFrame(corr_rows, columns=["feature", "spearman_corr_with_return", "spearman_pvalue"])
        corr_df["abs_spearman_corr"] = corr_df["spearman_corr_with_return"].abs()
        corr_df = corr_df.set_index("feature").join(rf_importance, how="left").reset_index()
        corr_df.sort_values(["abs_spearman_corr", "rf_importance"], ascending=[False, False], inplace=True)
        corr_df.to_csv(out_path("driver_factor_analysis.csv"), index=False, encoding="utf-8-sig")
        print(f"已保存驱动因子分析表到 {out_path('driver_factor_analysis.csv')}")

        # 可视化：Top 驱动因子（相关性）与 RF 重要性
        top_k = min(20, len(corr_df))
        top_corr = corr_df.head(top_k).iloc[::-1]
        plt.figure(figsize=(10, 7))
        plt.barh(top_corr["feature"], top_corr["abs_spearman_corr"], color="#4C78A8")
        plt.title(f"Top-{top_k} 驱动因子（|Spearman| vs 实际收益）")
        plt.xlabel("|Spearman correlation|")
        plt.tight_layout()
        plt.savefig(out_path("top_drivers_spearman.png"), dpi=300, bbox_inches="tight")
        if show_plots:
            plt.show()
        else:
            plt.close()

        top_rf = corr_df.sort_values("rf_importance", ascending=False).head(top_k).iloc[::-1]
        plt.figure(figsize=(10, 7))
        plt.barh(top_rf["feature"], top_rf["rf_importance"], color="#F58518")
        plt.title(f"Top-{top_k} 驱动因子（RF importance vs 远期收益目标）")
        plt.xlabel("RF feature importance")
        plt.tight_layout()
        plt.savefig(out_path("top_drivers_rf_importance.png"), dpi=300, bbox_inches="tight")
        if show_plots:
            plt.show()
        else:
            plt.close()
    except Exception as e:
        print(f"[警告] 驱动因子分析失败：{e}")

    # 2) 风险区间 / 信号分类 + 准确性验证
    try:
        # 风险区间：按 |预测收益| 的分位数划分（低/中/高）
        abs_pred = np.abs(gru_pred_return)
        q50, q80 = np.quantile(abs_pred, [0.5, 0.8])
        risk_level = np.where(abs_pred >= q80, "HIGH",
                      np.where(abs_pred >= q50, "MEDIUM", "LOW"))

        # 信号分类：多/空/观望（阈值用 q50 的一半，避免太稀疏）
        sig_th = max(1e-6, float(q50) * 0.5)
        signal = np.where(gru_pred_return > sig_th, "LONG",
                  np.where(gru_pred_return < -sig_th, "SHORT", "FLAT"))

        # 真实方向（涨/跌/平）
        true_dir = np.where(y_test_return > threshold, "UP",
                    np.where(y_test_return < -threshold, "DOWN", "FLAT"))
        pred_dir = np.where(gru_pred_return > threshold, "UP",
                    np.where(gru_pred_return < -threshold, "DOWN", "FLAT"))

        risk_df = pd.DataFrame({
            "Date_target": test_target_dates[:min_len],
            "Actual_Return": y_test_return[:min_len],
            "Pred_Return": gru_pred_return[:min_len],
            "RiskLevel": risk_level[:min_len],
            "Signal": signal[:min_len],
            "TrueDirection": true_dir[:min_len],
            "PredDirection": pred_dir[:min_len],
        })
        risk_df.to_csv(out_path("risk_signal_classification.csv"), index=False, encoding="utf-8-sig")
        print(f"已保存风险与信号分类表到 {out_path('risk_signal_classification.csv')}")

        # 混淆矩阵（方向）
        labels = ["UP", "FLAT", "DOWN"]
        cm = pd.crosstab(
            pd.Categorical(risk_df["TrueDirection"], categories=labels, ordered=True),
            pd.Categorical(risk_df["PredDirection"], categories=labels, ordered=True),
            rownames=["True"], colnames=["Pred"], dropna=False
        )
        cm.to_csv(out_path("direction_confusion_matrix.csv"), encoding="utf-8-sig")
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title("Direction Confusion Matrix")
        plt.tight_layout()
        plt.savefig(out_path("direction_confusion_matrix.png"), dpi=300, bbox_inches="tight")
        if show_plots:
            plt.show()
        else:
            plt.close()
    except Exception as e:
        print(f"[警告] 风险区间/信号分类失败：{e}")

    # 3) 简单回测：按信号做多/做空/空仓，计算策略净值曲线与指标
    try:
        # position: LONG=+1, SHORT=-1, FLAT=0
        pos = np.where(signal == "LONG", 1, np.where(signal == "SHORT", -1, 0)).astype(float)
        strat_ret = pos * y_test_return[:min_len]
        buyhold_ret = y_test_return[:min_len]

        strat_nav = np.exp(np.cumsum(strat_ret))
        bh_nav = np.exp(np.cumsum(buyhold_ret))

        backtest_df = pd.DataFrame({
            "Date_target": test_target_dates[:min_len],
            "Actual_Return": buyhold_ret,
            "Position": pos,
            "Strategy_Return": strat_ret,
            "Strategy_NAV": strat_nav,
            "BuyHold_NAV": bh_nav,
        })
        backtest_df.to_csv(out_path("backtest_results.csv"), index=False, encoding="utf-8-sig")

        # 指标（不做年化频率假设，输出总收益/最大回撤/胜率）
        def max_drawdown(nav: np.ndarray) -> float:
            peak = np.maximum.accumulate(nav)
            dd = nav / peak - 1.0
            return float(dd.min())

        total_return = float(strat_nav[-1] - 1.0)
        bh_total_return = float(bh_nav[-1] - 1.0)
        mdd = max_drawdown(strat_nav)
        win_rate = float((strat_ret > 0).mean())

        backtest_metrics = pd.DataFrame([{
            "Strategy_TotalReturn": total_return,
            "BuyHold_TotalReturn": bh_total_return,
            "Strategy_MaxDrawdown": mdd,
            "Strategy_WinRate": win_rate,
            "Signal_Threshold": sig_th,
        }])
        backtest_metrics.to_csv(out_path("backtest_metrics.csv"), index=False, encoding="utf-8-sig")

        plt.figure(figsize=(12, 5))
        plt.plot(strat_nav, label="Strategy NAV")
        plt.plot(bh_nav, label="Buy&Hold NAV", alpha=0.7)
        plt.title("Backtest NAV Curve (Strategy vs Buy&Hold)")
        plt.xlabel("Sample")
        plt.ylabel("NAV")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_path("backtest_nav_curve.png"), dpi=300, bbox_inches="tight")
        if show_plots:
            plt.show()
        else:
            plt.close()

        print(f"回测完成：Strategy 总收益={total_return:.2%}，最大回撤={mdd:.2%}，胜率={win_rate:.2%}")
    except Exception as e:
        print(f"[警告] 回测失败：{e}")

    # 4) 报告（Markdown）：面向企业银行团队的风险提示概要
    try:
        report_lines = []
        report_lines.append("# 油价预测分析报告（企业银行团队版）")
        report_lines.append("")
        report_lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(
            f"- 预测步长：H={HORIZON_H}（天），多尺度窗口：{WINDOW_SHORT}/{WINDOW_MID}/{WINDOW_LONG} 日"
        )
        report_lines.append(f"- 特征选择：RandomForest Top-N={int(n)} + 强制趋势列")
        report_lines.append("")
        report_lines.append("## 1. 预测效果（Test）")
        report_lines.append(f"- MAE：{metrics['MAE']:.4f}")
        report_lines.append(f"- RMSE：{metrics['RMSE']:.4f}")
        report_lines.append(f"- MAPE：{metrics['MAPE']:.2f}%")
        report_lines.append(f"- R2：{metrics['R2']:.4f}")
        report_lines.append(f"- ΔR2（相对随机游走价格）：{delta_r2_price:.4f}")
        report_lines.append(f"- 方向预测准确率（排除平盘）：{direction_accuracy:.4f}")
        report_lines.append(f"- 对数收益 R2（模型）：{ret_r2:.4f}")
        report_lines.append(f"- 对数收益 R2（零收益基准）：{r2_ret_rw:.4f}")
        report_lines.append(f"- 对数收益 R2（AR(1) 基准）：{r2_ret_ar1:.4f}")
        report_lines.append(f"- 对数收益 R2（均值基准）：{r2_ret_mean:.4f}")
        if roc_auc_test is not None:
            report_lines.append(f"- 涨跌辅助头 ROC-AUC：{roc_auc_test:.4f}")
        report_lines.append("")
        report_lines.append("## 2. 主要驱动因子（示例 Top-10）")
        driver_csv = out_path("driver_factor_analysis.csv")
        if Path(driver_csv).exists():
            df_driver = pd.read_csv(driver_csv)
            top10 = df_driver.head(10)[["feature", "spearman_corr_with_return", "rf_importance"]]
            report_lines.append(_dataframe_to_markdown_safe(top10, index=False))
            report_lines.append("")
            report_lines.append("- 图表：`top_drivers_spearman.png`、`top_drivers_rf_importance.png`")
        else:
            report_lines.append("- （未生成驱动因子表）")
        report_lines.append("")
        report_lines.append("## 3. 风险区间与信号")
        report_lines.append("- 风险区间：按 |预测收益| 分位数划分（LOW/MEDIUM/HIGH）")
        report_lines.append("- 信号：LONG / SHORT / FLAT（阈值来自预测收益幅度）")
        report_lines.append("- 图表：`direction_confusion_matrix.png`")
        report_lines.append("")
        report_lines.append("## 4. 简单回测（信号驱动）")
        bm = out_path("backtest_metrics.csv")
        if Path(bm).exists():
            df_bt = pd.read_csv(bm)
            report_lines.append(_dataframe_to_markdown_safe(df_bt, index=False))
            report_lines.append("")
            report_lines.append("- 图表：`backtest_nav_curve.png`")
        else:
            report_lines.append("- （未生成回测指标）")
        report_lines.append("")
        report_lines.append("## 5. 风险提示（概要）")
        report_lines.append("- 模型预测用于短期风险识别与情景提示，不构成投资建议。")
        report_lines.append("- 当风险区间为 HIGH 且信号为 LONG/SHORT 时，建议结合库存/宏观/地缘事件进行人工复核。")
        report_lines.append("- 建议与基准（随机游走/简单技术指标）并行监控，避免过拟合与结构性突变风险。")
        report_lines.append("")
        report_lines.append("## 6. 输出文件清单")
        report_lines.append("- `prediction_results.csv`：对齐后的预测/真实/收益")
        report_lines.append("- `daily_predictions_vs_actual.csv`：每日预测 vs 真实（含误差）")
        report_lines.append("- `driver_factor_analysis.csv`：驱动因子量化（相关性+RF重要性）")
        report_lines.append("- `risk_signal_classification.csv`：风险区间+信号分类")
        report_lines.append("- `backtest_results.csv`、`backtest_metrics.csv`：回测结果与指标")
        report_lines.append("- 图：`gru_predictions.png`、`gru_returns.png`、`direction_prediction.png`、`top_drivers_*.png`、`direction_confusion_matrix.png`、`backtest_nav_curve.png`")

        report_path = out_path("bank_team_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"已保存报告到 {report_path}")
    except Exception as e:
        print(f"[警告] 报告生成失败：{e}")

    # lstm_model.save('lstm_model.h5')
    try:
        gru_model.save(out_path('gru_model.h5'))
    except Exception as exc:
        print(f"[警告] 保存 gru_model.h5 失败，将尝试仅保存权重: {exc}")
        gru_model.save_weights(out_path('gru_model.weights.h5'))

    print("\n完成！")

    # ----------------------------------------------------------------------
    # 实盘预测：基于“截止日期”用最后窗口递推预测未来 N 天（horizon=1 时最合理）
    # 输出：future_forecast.csv + future_forecast.png
    # ----------------------------------------------------------------------
    try:
        forecast_steps = int(forecast_steps or 0)
    except Exception:
        forecast_steps = 0

    if forecast_steps > 0:
        if predictor.horizon != 1:
            print(f"\n[提示] 当前 horizon={predictor.horizon}，递推多步预测最合理的是 horizon=1。将仍按逐日递推预测 {forecast_steps} 天。")

        print(f"\n=== 实盘预测：递推预测未来 {forecast_steps} 天 ===")

        # 截止日期：默认用数据最后一天；若提供 cutoff_date，则只使用 <= cutoff 的历史
        raw_hist = data.sort_index().copy()
        if cutoff_date:
            cutoff_ts = pd.to_datetime(cutoff_date, errors="coerce")
            if pd.isna(cutoff_ts):
                print(f"[警告] cutoff_date={cutoff_date} 无法解析，将使用最后日期。")
            else:
                raw_hist = raw_hist.loc[raw_hist.index <= cutoff_ts].copy()

        if len(raw_hist) < (predictor.timesteps + 5):
            print("[警告] 历史数据太短，无法进行实盘预测（不足以形成窗口）。")
        else:
            # 使用训练时的 scaler 与特征列
            scaler_X = data_dict.get("scaler_X")
            scaler_y = data_dict.get("scaler_y")
            selected_features = list(feature_cols)

            last_known = raw_hist.iloc[-1].copy()
            last_date = raw_hist.index[-1]

            future_rows = []
            raw_ext = raw_hist.copy()

            for step in range(1, forecast_steps + 1):
                next_date = pd.to_datetime(last_date) + pd.Timedelta(days=1)
                # 简化：未知外生变量用最后已知值延续
                new_row = last_known.copy()
                new_row.name = next_date
                raw_ext = pd.concat([raw_ext, new_row.to_frame().T], axis=0)

                # 重新做特征工程与清洗（只为获得最新一天的输入特征）
                feats = feature_engineer.create_all_features(raw_ext, target_price_col='WTI_Futures')
                feats = predictor.create_target_forward_return(
                    feats, price_col='WTI_Futures', target_col=TARGET_COL
                )
                feats_clean = preprocessor.handle_missing_values(feats)

                # 只取模型所需列，避免缺列
                missing = [c for c in selected_features if c not in feats_clean.columns]
                if missing:
                    print(f"[警告] 实盘预测缺少特征列：{missing[:5]}{'...' if len(missing) > 5 else ''}")
                    break

                # 取截止到 next_date 的最后 timesteps 行做输入窗口。
                # 注意：多步递推时，新增未来行在复杂滚动特征下容易出现局部 NaN，
                # 若直接 dropna() 会把新行丢掉，导致每一步都重复用同一段历史窗口。
                x_df = feats_clean[selected_features].copy()
                x_df = x_df.ffill().bfill()
                if x_df.tail(predictor.w_long).isna().any().any():
                    print("[警告] 实盘预测窗口仍存在 NaN，无法继续递推。")
                    break
                w5, w20, w60 = predictor.w_short, predictor.w_mid, predictor.w_long
                if len(x_df) < w60:
                    print("[警告] 实盘预测窗口不足（特征行数过少）。")
                    break

                x5 = scaler_X.transform(x_df.iloc[-w5:].values).astype(np.float32)
                x20 = scaler_X.transform(x_df.iloc[-w20:].values).astype(np.float32)
                x60 = scaler_X.transform(x_df.iloc[-w60:].values).astype(np.float32)
                X5 = x5.reshape(1, w5, len(selected_features))
                X20 = x20.reshape(1, w20, len(selected_features))
                X60 = x60.reshape(1, w60, len(selected_features))

                pred_in = [X5, X20, X60]
                if data_dict.get("use_explicit_base_log") and data_dict.get("scaler_base_log") is not None:
                    base_p_feat = float(raw_ext["WTI_Futures"].iloc[-2])
                    bl = np.log(max(base_p_feat, 1e-8))
                    bsc = data_dict["scaler_base_log"].transform([[bl]]).astype(np.float32)
                    pred_in.append(bsc)

                reg_scaled, _ = predictor.predict(gru_model, pred_in)
                pred_log_fwd = float(predictor.predict_return_from_scaled(np.asarray(reg_scaled), data_dict)[0])
                base_p = float(raw_ext['WTI_Futures'].iloc[-2])
                pred_price = float(base_p * np.exp(pred_log_fwd))

                # 用预测价格更新下一天的 WTI_Futures，形成递推
                raw_ext.loc[next_date, 'WTI_Futures'] = pred_price
                last_known = raw_ext.loc[next_date].copy()
                last_date = next_date

                # 预测收益（相对上一交易点）：log(P_t / P_{t-1})
                prev_price = float(raw_ext.loc[raw_ext.index[-2], 'WTI_Futures'])
                pred_ret = float(np.log(pred_price / prev_price)) if prev_price > 0 else np.nan

                future_rows.append({
                    "Date": next_date,
                    "Pred_Price": pred_price,
                    "Pred_Return": pred_ret,
                })

            if future_rows:
                future_df = pd.DataFrame(future_rows)
                future_df.to_csv(out_path("future_forecast.csv"), index=False, encoding="utf-8-sig")
                print(f"已保存未来预测到 {out_path('future_forecast.csv')}，行数={len(future_df)}")

                plt.figure(figsize=(12, 4))
                plt.plot(future_df["Date"], future_df["Pred_Price"], marker="o", label="Forecast Price")
                plt.title(f"Future Forecast ({forecast_steps} days)")
                plt.xlabel("Date")
                plt.ylabel("Price")
                plt.xticks(rotation=30)
                plt.tight_layout()
                plt.savefig(out_path("future_forecast.png"), dpi=300, bbox_inches="tight")
                if show_plots:
                    plt.show()
                else:
                    plt.close()
            else:
                print("[警告] 未生成任何未来预测结果。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Oil price prediction pipeline (GRU/LSTM)")
    parser.add_argument("--base-path", default=".", help="数据根目录（包含 raw_data/ 和 能源基本面与下游产业/）")
    parser.add_argument("--top-n", type=int, default=int(RF_TOP_N_DEFAULT), help="随机森林特征选择 Top-N")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出根目录；默认在下方自动创建独立子文件夹（见 --results-folder / --flat-output）",
    )
    parser.add_argument(
        "--results-folder",
        default=None,
        metavar="NAME",
        help="在 --output-dir 下使用的子文件夹名；省略则自动命名为 rework_result_YYYYMMDD_HHMMSS",
    )
    parser.add_argument(
        "--flat-output",
        action="store_true",
        help="不创建子文件夹，直接向 --output-dir 写入（与旧版扁平输出一致）",
    )
    parser.add_argument("--no-plots", action="store_true", help="不弹出图窗（适合 Web/服务器运行）")
    parser.add_argument("--cutoff-date", default=None, help="实盘预测的截止日期（YYYY-MM-DD）；默认使用数据最后一天")
    parser.add_argument("--forecast-steps", type=int, default=0, help="实盘预测：递推预测未来 N 天（0=不生成）")
    parser.add_argument("--epochs", type=int, default=200, help="训练轮数（epochs），默认 200")
    parser.add_argument("--vmd-label", action="store_true", help="对收益标签启用 VMD 分解（默认按常量 USE_VMD_LABEL）")
    parser.add_argument("--no-vmd-label", action="store_true", help="关闭 VMD 标签分解")
    parser.add_argument("--vmd-k", type=int, default=None, help=f"VMD 模态数 K，默认 {VMD_K}")
    parser.add_argument(
        "--early-stopping-patience",
        type=int,
        default=None,
        metavar="N",
        help=f"正式训练时 EarlyStopping 的 val_loss 耐心（epoch），默认 {FORMAL_EARLY_STOPPING_PATIENCE}；Optuna trial 内仍为 12",
    )
    parser.add_argument(
        "--monitor-port",
        type=int,
        default=0,
        metavar="PORT",
        help=">0 时在后台启动简易 Web（需 flask），浏览器查看实时 train/val loss；0 关闭",
    )
    parser.add_argument(
        "--params-csv",
        default=None,
        help="从 noise_optuna_best_params.csv 加载 GRU/增强/batch 超参（与 noise_binary_test 导出一致）",
    )
    parser.add_argument("--optuna-trials", type=int, default=0, help="Optuna 搜索次数；0=关闭（与 --params-csv 二选一）")
    parser.add_argument("--optuna-epochs", type=int, default=80, help="Optuna 每个 trial 的最大训练轮数")
    parser.add_argument("--optuna-timeout", type=int, default=0, help="Optuna 总秒数上限，0=不限")
    parser.add_argument(
        "--optuna-weight-cls",
        type=float,
        default=0.45,
        help="复合目标中 (1-val_cls_acc) 的权重，越大越重视分类头",
    )
    parser.add_argument(
        "--optuna-weight-dir",
        type=float,
        default=0.35,
        help="复合目标中 (1-val_dir_acc) 的权重，越大越重视回归头方向（验证集）",
    )
    parser.add_argument("--optuna-seed", type=int, default=42, help="Optuna 采样随机种子")
    parser.add_argument(
        "--optuna-no-fe",
        action="store_true",
        help="Optuna 只搜索 GRU/增强等，不搜索 RF Top-N、树棵数、Winsorize、RF 拟合范围（更快；先按 --top-n 跑完固定特征流水线）",
    )
    args = parser.parse_args()

    # CLI 覆盖 VMD 开关（优先级最高）
    vmd_label_flag = USE_VMD_LABEL
    if bool(args.vmd_label):
        vmd_label_flag = True
    if bool(args.no_vmd_label):
        vmd_label_flag = False
    vmd_k_cli = VMD_K if args.vmd_k is None else int(args.vmd_k)

    base_out = os.path.abspath(args.output_dir or ".")
    if args.flat_output:
        final_output_dir = base_out
        os.makedirs(final_output_dir, exist_ok=True)
    else:
        if args.results_folder and str(args.results_folder).strip():
            sub = str(args.results_folder).strip()
        else:
            sub = f"rework_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        final_output_dir = os.path.join(base_out, sub)
        os.makedirs(final_output_dir, exist_ok=True)

    # Web/服务器环境下建议关闭交互式绘图
    if args.no_plots:
        try:
            import matplotlib
            matplotlib.use("Agg")
        except Exception:
            pass

    main(
        base_path=args.base_path,
        top_n=args.top_n,
        output_dir=final_output_dir,
        no_plots=args.no_plots,
        cutoff_date=args.cutoff_date,
        forecast_steps=args.forecast_steps,
        epochs=int(max(1, int(args.epochs or 200))),
        monitor_port=int(args.monitor_port or 0),
        params_csv=args.params_csv,
        optuna_trials=int(args.optuna_trials or 0),
        optuna_epochs=int(max(1, int(args.optuna_epochs or 80))),
        optuna_timeout=int(args.optuna_timeout or 0),
        optuna_weight_cls=float(args.optuna_weight_cls),
        optuna_weight_dir=float(args.optuna_weight_dir),
        optuna_seed=int(args.optuna_seed),
        optuna_tune_fe=not bool(args.optuna_no_fe),
        early_stopping_patience=args.early_stopping_patience,
        vmd_label=vmd_label_flag,
        vmd_k=vmd_k_cli,
    )