"""
实盘单步预测脚本（使用已训练权重）
================================

用途：
- 读取最近 N 天期价（默认读取 ClosePrice）
- 载入 optuna_best_params_full.json 的参数
- 按训练模型结构构建网络并加载 gru_sequence_weights.weights.h5
- 预测下一天收益与价格

说明：
- 该脚本做“轻量实盘推理”，只依赖价格序列本身（n_features=1）。
- 若训练时使用了多源特征/训练集 scaler，想做到完全一致推理，
  需要在训练阶段额外保存“特征列清单 + scaler 参数”并在此复现。
"""

from __future__ import annotations

import argparse
import json
import os
from types import SimpleNamespace

import numpy as np
import pandas as pd

try:
    from tensorflow.keras.losses import Huber
    from tensorflow.keras.optimizers import Adam
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "需要安装 TensorFlow 2：pip install tensorflow\n"
        f"导入失败: {e}"
    ) from e

from wti_gru_sequence import (
    apply_vmd_on_target,
    build_sequence_model,
    build_sequence_model_multi,
)


DEFAULT_INPUT_CSV = "live_wti_15d.csv"
DEFAULT_PARAMS_JSON = "optuna_best_params_full.json"
DEFAULT_WEIGHTS = "gru_sequence_weights.weights.h5"


def _load_runtime_params(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"参数 JSON 顶层必须是对象: {path}")
    if isinstance(data.get("params"), dict):
        return dict(data["params"])
    if isinstance(data.get("best_params"), dict):
        return dict(data["best_params"])
    return dict(data)


def _load_price_series(csv_path: str, price_col: str) -> np.ndarray:
    if not os.path.isfile(csv_path):
        raise SystemExit(f"输入文件不存在: {csv_path}")
    df = pd.read_csv(csv_path)
    if price_col not in df.columns:
        aliases = ["ClosePrice", "close", "Close", "CLOSE", "收盘", "WTI_Futures"]
        hit = next((c for c in aliases if c in df.columns), None)
        if hit is None:
            raise ValueError(f"价格列 {price_col!r} 不存在，实际列：{list(df.columns)}")
        df = df.rename(columns={hit: price_col})
        print(f"[列名兼容] 自动使用价格列: {hit} -> {price_col}")
    s = pd.to_numeric(df[price_col], errors="coerce").dropna().astype(float)
    if len(s) < 5:
        raise ValueError("有效价格点太少，至少需要 5 行。")
    return s.values.reshape(-1, 1)


def _price_to_return_like_live(prices: np.ndarray, return_type: str) -> np.ndarray:
    p = np.asarray(prices, dtype=np.float64).reshape(-1)
    eps = 1e-12
    if return_type == "log":
        r = np.log((p + eps) / (np.roll(p, 1) + eps))
    else:
        r = (p / (np.roll(p, 1) + eps)) - 1.0
    r[0] = 0.0
    return r.reshape(-1, 1)


def estimate_true_label_confidence(
    denoised_return: float,
    noise_imf: np.ndarray,
) -> float:
    """
    用 IMF8（高频噪声）估计“真实标签相对去噪标签”的置信度，范围 (0,1]。
    噪声越大、信号越弱，置信度越低。
    """
    noise = np.asarray(noise_imf, dtype=np.float64).reshape(-1)
    noise_std = float(np.std(noise)) if len(noise) > 0 else 0.0
    signal_abs = float(abs(denoised_return))
    snr_like = signal_abs / (noise_std + 1e-12)
    conf = 1.0 - np.exp(-max(0.0, snr_like))
    return float(np.clip(conf, 0.0, 1.0))


def run_live_forecast(
    input_csv: str = DEFAULT_INPUT_CSV,
    params_json: str = DEFAULT_PARAMS_JSON,
    weights_path: str = DEFAULT_WEIGHTS,
) -> dict:

    if not os.path.isfile(params_json):
        raise SystemExit(f"参数文件不存在: {params_json}")
    if not os.path.isfile(weights_path):
        raise SystemExit(f"权重文件不存在: {weights_path}")

    params = _load_runtime_params(params_json)
    args = SimpleNamespace(**params)

    price_col = str(getattr(args, "price_col", "ClosePrice"))
    time_steps = int(getattr(args, "time_steps", 15))
    return_type = str(getattr(args, "return_type", "simple"))
    use_multi = bool(getattr(args, "use_direction_head", True))

    prices = _load_price_series(input_csv, price_col=price_col)
    if len(prices) < time_steps:
        raise SystemExit(
            f"输入价格长度不足：当前 {len(prices)}，需要至少 {time_steps} 行。"
        )

    # 1) 由价格转收益
    returns = _price_to_return_like_live(prices, return_type=return_type)

    # 2) 与训练一致的 VMD 拓扑：K=8，删除最高频 1 个 IMF（默认）
    vmd_k = int(getattr(args, "vmd_k", 8))
    vmd_drop = int(getattr(args, "vmd_drop_high_freq", 1))
    vmd_alpha = float(getattr(args, "vmd_alpha", 2000.0))
    vmd_tau = float(getattr(args, "vmd_tau", 0.0))
    vmd_dc = int(getattr(args, "vmd_dc", 0))
    vmd_init = int(getattr(args, "vmd_init", 1))
    vmd_tol = float(getattr(args, "vmd_tol", 1e-7))
    vmd_mode = str(getattr(args, "vmd_drop_mode", "freq"))

    denoised_returns, imfs = apply_vmd_on_target(
        returns,
        k=vmd_k,
        alpha=vmd_alpha,
        tau=vmd_tau,
        dc=vmd_dc,
        init=vmd_init,
        tol=vmd_tol,
        drop_high_freq=vmd_drop,
        drop_mode=vmd_mode,
        debug_print=False,
    )
    denoised_returns = np.asarray(denoised_returns, dtype=np.float64).reshape(-1, 1)

    if len(denoised_returns) < time_steps:
        raise SystemExit(
            f"VMD 后有效长度不足：当前 {len(denoised_returns)}，需要至少 {time_steps}。"
        )

    # 3) 轻量在线标准化（无训练 scaler 时的近似方案）
    window_ret = denoised_returns[-time_steps:].reshape(-1, 1)
    mu = float(np.mean(window_ret))
    sigma = float(np.std(window_ret))
    if not np.isfinite(sigma) or sigma < 1e-12:
        sigma = 1.0
    x_scaled = ((window_ret - mu) / sigma).reshape(1, time_steps, 1).astype(np.float64)

    if use_multi:
        model = build_sequence_model_multi(
            str(getattr(args, "cell", "gru")),
            int(getattr(args, "batch_size", 64)),
            time_steps,
            n_features=1,
            bidirectional=bool(getattr(args, "bidirectional", True)),
            stateful=False,
            units=int(getattr(args, "units", 64)),
            dropout=float(getattr(args, "dropout", 0.1)),
        )
        loss_fn = Huber() if str(getattr(args, "loss", "huber")) == "huber" else str(getattr(args, "loss", "mse"))
        model.compile(
            optimizer=Adam(learning_rate=float(getattr(args, "learning_rate", 1e-3))),
            loss={"return": loss_fn, "dir": "binary_crossentropy"},
        )
    else:
        model = build_sequence_model(
            str(getattr(args, "cell", "gru")),
            int(getattr(args, "batch_size", 64)),
            time_steps,
            n_features=1,
            bidirectional=bool(getattr(args, "bidirectional", True)),
            stateful=False,
            units=int(getattr(args, "units", 64)),
            dropout=float(getattr(args, "dropout", 0.1)),
        )
        loss_fn = Huber() if str(getattr(args, "loss", "huber")) == "huber" else str(getattr(args, "loss", "mse"))
        model.compile(
            optimizer=Adam(learning_rate=float(getattr(args, "learning_rate", 1e-3))),
            loss=loss_fn,
        )

    model.load_weights(weights_path)

    raw_pred = model.predict(x_scaled, batch_size=1, verbose=0)
    if use_multi:
        pred_scaled = float(np.asarray(raw_pred[0], dtype=np.float64).reshape(-1)[0])
        pred_prob_up = float(np.asarray(raw_pred[1], dtype=np.float64).reshape(-1)[0])
    else:
        pred_scaled = float(np.asarray(raw_pred, dtype=np.float64).reshape(-1)[0])
        pred_prob_up = float("nan")

    pred_return = pred_scaled * sigma + mu
    last_price = float(prices[-1, 0])
    if return_type == "log":
        pred_price = last_price * float(np.exp(pred_return))
    else:
        pred_price = last_price * (1.0 + pred_return)

    # 4) 用 IMF8（最高频段噪声）估计“真实标签相对去噪标签”的置信度
    # 若 K<8，则退化为最后一个 IMF 作为噪声近似。
    noise_idx = 7 if imfs.shape[0] >= 8 else (imfs.shape[0] - 1)
    noise_imf = imfs[noise_idx]
    pred_conf = estimate_true_label_confidence(pred_return, noise_imf)

    out = {
        "input_csv": input_csv,
        "weights": weights_path,
        "window_len": int(time_steps),
        "return_type": return_type,
        "vmd_k": int(vmd_k),
        "drop_high_freq": int(vmd_drop),
        "drop_mode": vmd_mode,
        "last_price": float(last_price),
        "pred_denoised_return": float(pred_return),
        "pred_price": float(pred_price),
        "true_vs_denoised_confidence": float(pred_conf),
        "pred_prob_up": float(pred_prob_up) if np.isfinite(pred_prob_up) else None,
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-csv", default=DEFAULT_INPUT_CSV)
    ap.add_argument("--params-json", default=DEFAULT_PARAMS_JSON)
    ap.add_argument("--weights", default=DEFAULT_WEIGHTS)
    ap.add_argument("--json", action="store_true", help="以 JSON 打印输出，便于后端解析")
    args = ap.parse_args()

    out = run_live_forecast(
        input_csv=args.input_csv,
        params_json=args.params_json,
        weights_path=args.weights,
    )

    if args.json:
        print(json.dumps(out, ensure_ascii=False))
        return

    print("\n=== Next-Day Forecast ===")
    print(f"input_csv={out['input_csv']}")
    print(f"weights={out['weights']}")
    print(f"window_len={out['window_len']}, return_type={out['return_type']}")
    print(f"vmd_k={out['vmd_k']}, drop_high_freq={out['drop_high_freq']}, drop_mode={out['drop_mode']}")
    print(f"last_price={out['last_price']:.6f}")
    print(f"pred_denoised_return={out['pred_denoised_return']:.8f}")
    print(f"pred_price={out['pred_price']:.6f}")
    print(f"true_vs_denoised_confidence={out['true_vs_denoised_confidence']:.6f}")
    if out["pred_prob_up"] is not None:
        print(f"pred_prob_up={out['pred_prob_up']:.6f}")


if __name__ == "__main__":
    main()

