
from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_OUT_DIR = _SCRIPT_DIR / "bond_integrated_output"

# 合并表必需列（列名需一致，或可 --data-csv 指向已整理好的宽表）
REQUIRED_COLS = [
    "date",
    "oil_price_pred",
    "treasury_10y",
    "fed_rate_exp",
    "ecb_rate_exp",
    "greenium",
    "esg_flow",
    "oil_volatility",
    "green_bond_yield",
]

BASE_REQUIRED_COLS = [
    "date",
    "treasury_10y",
    "fed_rate_exp",
    "ecb_rate_exp",
    "greenium",
    "esg_flow",
    "oil_volatility",
    "green_bond_yield",
]


def plot_prediction(y_true, y_pred, save_path=None):
    plt.figure(figsize=(12, 6))

    plt.plot(y_true, label="Actual", linewidth=2)
    plt.plot(y_pred, label="Predicted", linestyle="--")

    plt.title("Bond Prediction")
    plt.legend()
    plt.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    return plt

def _resolve_output_path(output_csv: str, out_dir: str) -> str:
    s = (output_csv or "").strip()
    if not s:
        raise ValueError("--output-csv 不能为空")
    if os.path.isabs(s):
        return os.path.abspath(s)
    if os.path.dirname(s):
        return os.path.abspath(s)
    return os.path.abspath(os.path.join(out_dir, s))

def _load_merged(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "date" not in df.columns:
        raise ValueError("合并表必须包含列 date")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    BASE_REQUIRED_COLS = [
        "date",
        "treasury_10y",
        "fed_rate_exp",
        "ecb_rate_exp",
        "greenium",
        "esg_flow",
        "oil_volatility",
        "green_bond_yield",
    ]

    available_cols = [c for c in BASE_REQUIRED_COLS if c in df.columns]
    missing_cols = [c for c in BASE_REQUIRED_COLS if c not in df.columns]

    print(f"[info] 可用特征: {available_cols}")
    print(f"[warning] 缺失特征: {missing_cols}")

    MIN_REQUIRED_FEATURES = 3

    if len(available_cols) < MIN_REQUIRED_FEATURES:
        raise ValueError(
            f"可用特征过少，仅 {len(available_cols)} 个：{available_cols}"
        )

    return df.sort_values("date").reset_index(drop=True)

def _add_paper_features(df: pd.DataFrame, chol_window: int = 60, ewma_span: int = 42) -> pd.DataFrame:
    """
    Kartal：EWMA 趋势/周期；Azhgaliyeva/Kilian：滚动递归 Cholesky（顺序 油→国债→美政策预期一阶差分）。
    Kanamura 类交互：油价×波动、绿债利差×波动。
    """
    out = df.copy()
    o = out["oil_price_pred"].astype(float)
    tr = out["treasury_10y"].astype(float)
    fe = out["fed_rate_exp"].astype(float)
    vol = out["oil_volatility"].astype(float)
    gi = out["greenium"].astype(float)
    out["oil_trend"] = o.ewm(span=int(ewma_span), adjust=False).mean()
    out["oil_cycle"] = o - out["oil_trend"]
    out["oil_vol_x_pred"] = o * vol
    out["greenium_x_vol"] = gi * vol
    d_o = o.diff()
    d_t = tr.diff()
    d_f = fe.diff()
    w = max(10, int(chol_window))
    eps = 1e-12
    e1 = d_o
    beta21 = d_t.rolling(w).cov(e1) / (e1.rolling(w).var() + eps)
    e2 = d_t - beta21 * e1
    beta31 = d_f.rolling(w).cov(e1) / (e1.rolling(w).var() + eps)
    beta32 = d_f.rolling(w).cov(e2) / (e2.rolling(w).var() + eps)
    e3 = d_f - beta31 * e1 - beta32 * e2
    out["shock_oil_recur"] = e1
    out["shock_tr_recur"] = e2
    out["shock_fed_recur"] = e3
    return out


def _stage2_gb_kwargs(
    *,
    n_estimators: int = 200,
    learning_rate: float = 0.05,
    max_depth: int = 2,
    min_samples_leaf: int = 15,
    subsample: float = 0.85,
    random_state: int = 42,
) -> dict:
    """第二阶段 GBDT：默认偏弱树+子采样，减轻 greenium/esg 特征加入后的过拟合。"""
    return {
        "n_estimators": n_estimators,
        "learning_rate": learning_rate,
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
        "subsample": subsample,
        "random_state": random_state,
    }


def _train_and_predict_stage12(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    stage1_features: list[str],
    stage2_features: list[str],
    target: str,
    ridge_alpha: float,
    gb_kw: dict | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    两阶段：Ridge(stage1) + （可选）GBDT(stage2 拟合训练残差)。
    返回 (y_test 真实值, y_final 预测, sigma=|测试集一阶残差|)。
    """
    y_train, y_test = train_df[target].astype(float), test_df[target].astype(float)
    y_train_arr = y_train.to_numpy() if hasattr(y_train, "to_numpy") else np.asarray(y_train)
    y_test_arr = y_test.to_numpy() if hasattr(y_test, "to_numpy") else np.asarray(y_test)

    # 兜底：如果 stage1 特征全不可用，用均值基线（便于 walk-forward）
    if len(stage1_features) == 0:
        base_pred = float(np.mean(y_train_arr))
        y_te_p1 = np.full(shape=(len(y_test_arr),), fill_value=base_pred, dtype=float)
        res_te = y_test_arr - y_te_p1
        sigma = np.abs(res_te)
        sigma = np.maximum(sigma, 1e-12)
        return y_test_arr.astype(float), y_te_p1.astype(float), sigma.astype(float)

    X1_train, X1_test = train_df[stage1_features], test_df[stage1_features]
    sc1 = StandardScaler()
    X1_tr = sc1.fit_transform(X1_train)
    X1_te = sc1.transform(X1_test)

    model1 = Ridge(alpha=float(ridge_alpha))
    model1.fit(X1_tr, y_train_arr)
    y_te_p1 = model1.predict(X1_te)
    res_tr = y_train_arr - model1.predict(X1_tr)
    res_te = y_test_arr - y_te_p1
    sigma = np.abs(res_te)
    sigma = np.maximum(sigma, 1e-12)

    # 仅线性方程：stage2_features 为空时跳过二阶段
    if len(stage2_features) == 0:
        return y_test_arr.astype(float), y_te_p1.astype(float), sigma.astype(float)

    # 二阶段：GBDT 拟合训练残差
    X2_train, X2_test = train_df[stage2_features], test_df[stage2_features]
    sc2 = StandardScaler()
    X2_tr = sc2.fit_transform(X2_train)
    X2_te = sc2.transform(X2_test)

    gkw = gb_kw if gb_kw is not None else _stage2_gb_kwargs()
    gb = GradientBoostingRegressor(**gkw)
    gb.fit(X2_tr, res_tr)
    pred_res_te = gb.predict(X2_te)
    y_final_te = y_te_p1 + pred_res_te
    return y_test_arr.astype(float), y_final_te.astype(float), sigma.astype(float)


def _walk_forward_eval(
    df: pd.DataFrame,
    stage1_features: list[str],
    stage2_features: list[str],
    target: str,
    ridge_alpha: float,
    min_train: int,
    step: int,
    gb_kw: dict | None = None,
) -> pd.DataFrame:
    """扩展训练窗 + 非重叠测试块；每折只在训练段 fit scaler/models。"""
    n = len(df)
    rows: list[dict] = []
    t = int(min_train)
    fold = 0
    while t + step <= n:
        train_df = df.iloc[:t].copy()
        test_df = df.iloc[t : t + step].copy()
        y_true, y_pred, _sigma = _train_and_predict_stage12(
            train_df,
            test_df,
            stage1_features,
            stage2_features,
            target,
            ridge_alpha,
            gb_kw=gb_kw,
        )
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        d_train_e = train_df["date"].iloc[-1]
        d_test_s, d_test_e = test_df["date"].iloc[0], test_df["date"].iloc[-1]
        rows.append(
            {
                "fold": fold,
                "n_train": len(train_df),
                "n_test": len(test_df),
                "train_end_date": d_train_e.strftime("%Y-%m-%d"),
                "test_start_date": d_test_s.strftime("%Y-%m-%d"),
                "test_end_date": d_test_e.strftime("%Y-%m-%d"),
                "RMSE": rmse,
                "MAE": mae,
                "R2": r2,
            }
        )
        fold += 1
        t += step
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="绿债线性方程预测，输出对齐 predict_new_energy_from_gru")
    ap.add_argument(
        "--build-data",
        action="store_true",
        help="运行前先从 bond_date 原始表生成 data.csv（见 bond_merge_from_bond_date.py）",
    )
    ap.add_argument(
        "--build-data-only",
        action="store_true",
        help="仅生成 data.csv 后退出，不训练",
    )
    ap.add_argument(
        "--extras-csv",
        default="",
        help="合并用：含 oil_price_pred、国债、政策预期、greenium、oil_volatility 等，列 date 对齐",
    )
    ap.add_argument(
        "--oil-pred-csv",
        default="",
        help="合并用：含 date, oil_price_pred（如 oil_pred.csv）",
    )
    ap.add_argument(
        "--fund-symbol",
        default="000042",
        help="build-data：Fund_NAV 中基金代码，默认 000042",
    )
    ap.add_argument(
        "--green-index-code",
        default="930951",
        help="build-data：BND_Tbdindexsh 中 Bndidxcd，默认 930951",
    )
    ap.add_argument(
        "--no-issuance-fill",
        action="store_true",
        help="build-data：不用发行规模填补缺失的 esg_flow",
    )
    ap.add_argument(
        "--greenium-col",
        default="green_premium_level",
        choices=("green_premium_level", "green_premium_dret"),
        help="build-data：green_premium_for_ml 中作为 greenium 的列",
    )
    ap.add_argument(
        "--esg-flow-agg",
        default="mean_return",
        choices=("mean_return", "sum_change"),
        help="build-data：esg_fund_flow_features 月内聚合方式",
    )
    ap.add_argument(
        "--data-csv",
        default="",
        help="合并特征 CSV（含 date 及全部特征列）；不填则尝试 bond_date/data.csv",
    )
    ap.add_argument(
        "--data-dir",
        default=str(_SCRIPT_DIR / "bond_date"),
        help="若未指定 --data-csv，则读取该目录下 data.csv",
    )
    ap.add_argument("--out-dir", default=str(_DEFAULT_OUT_DIR), help="默认 bond_integrated_output")
    ap.add_argument("--output-csv", default="bond_forecast_with_confidence.csv", help="主输出文件名或路径")
    ap.add_argument("--test-ratio", type=float, default=0.2, help="测试集占比（时间尾部）")
    ap.add_argument("--ridge-alpha", type=float, default=1.0)
    ap.add_argument("--conf-level", type=float, default=0.95, help="0.90 / 0.95 / 0.99")
    ap.add_argument(
        "--walk-forward",
        action="store_true",
        help="启用扩展窗 walk-forward 块验证（与单次 holdout 可同时输出）",
    )
    ap.add_argument(
        "--wf-min-train",
        type=int,
        default=80,
        help="walk-forward：首轮训练集最少样本数（日频约 80 个交易日）",
    )
    ap.add_argument(
        "--wf-step",
        type=int,
        default=20,
        help="walk-forward：每折测试块长度（日），随后训练窗扩展该长度",
    )
    ap.add_argument(
        "--wf-metrics-csv",
        default="bond_walk_forward_metrics.csv",
        help="walk-forward 每折指标保存名（仅 --walk-forward 时写入 out-dir；留空禁写）",
    )
    ap.add_argument(
        "--paper-synthesis",
        action="store_true",
        help="文献三合一近似：EWMA 分解、递归油价冲击、CR 交互项、分位数残差区间",
    )
    ap.add_argument(
        "--chol-window",
        type=int,
        default=60,
        help="递归冲击滚动窗长（日），需小于有效样本",
    )
    ap.add_argument(
        "--ewma-span",
        type=int,
        default=42,
        help="油价趋势 EWMA 跨度（日）",
    )
    ap.add_argument("--gb-max-depth", type=int, default=2, help="第二阶段 GBDT max_depth（默认略浅防过拟合）")
    ap.add_argument("--gb-min-samples-leaf", type=int, default=15, help="第二阶段 GBDT min_samples_leaf")
    ap.add_argument("--gb-subsample", type=float, default=0.85, help="第二阶段 GBDT 行子采样比例")
    ap.add_argument("--gb-n-estimators", type=int, default=200, help="第二阶段 GBDT 树棵数")
    ap.add_argument("--gb-learning-rate", type=float, default=0.05, help="第二阶段 GBDT 学习率")
    ap.add_argument(
        "--crisis-dummy-col",
        default="",
        help="可选：data.csv 中危机时期虚拟变量列名（存在时加入 crisis_dummy * oil_volatility 交互项）",
    )
    ap.add_argument("--no-viz", dest="make_viz", action="store_false")
    ap.set_defaults(make_viz=True)
    args = ap.parse_args()

    gb_kw = _stage2_gb_kwargs(
        max_depth=int(args.gb_max_depth),
        min_samples_leaf=int(args.gb_min_samples_leaf),
        subsample=float(args.gb_subsample),
        n_estimators=int(args.gb_n_estimators),
        learning_rate=float(args.gb_learning_rate),
    )

    if args.build_data or args.build_data_only:
        from bond_merge_from_bond_date import build_merged_dataframe

        gcode = str(args.green_index_code).strip() or None
        merged = build_merged_dataframe(
            args.data_dir,
            green_index_code=gcode,
            fund_symbol=str(args.fund_symbol).strip() or None,
            greenium_col=str(args.greenium_col),
            esg_flow_agg=str(args.esg_flow_agg),
            extras_csv=args.extras_csv.strip() or None,
            oil_pred_csv=args.oil_pred_csv.strip() or None,
            use_issuance_in_esg=not args.no_issuance_fill,
        )
        build_path = os.path.join(os.path.abspath(args.data_dir), "data.csv")
        merged.to_csv(build_path, index=False, encoding="utf-8-sig")
        print(f"[build-data] 已写入 {build_path}，行数 {len(merged)}")
        if args.build_data_only:
            return

    conf_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    if float(args.conf_level) not in conf_map:
        raise ValueError("conf-level 仅支持 0.90 / 0.95 / 0.99")
    z_alpha = conf_map[float(args.conf_level)]

    if args.data_csv:
        data_path = os.path.abspath(args.data_csv)
    else:
        data_path = os.path.join(args.data_dir, "data.csv")
    if not os.path.isfile(data_path):
        raise FileNotFoundError(
            f"找不到合并表: {data_path}\n"
            "可先运行：python predict_bond_from_gru_XYD.py --build-data-only\n"
            "或准备 data.csv，列包含：date, oil_price_pred, treasury_10y, "
            "fed_rate_exp, ecb_rate_exp, greenium, esg_flow, oil_volatility, green_bond_yield"
        )

    df = _load_merged(data_path)

    CORE_FEATURES = ["treasury_10y", "green_bond_yield"]

    missing_core = [c for c in CORE_FEATURES if c not in df.columns]

    if missing_core:
        print(f"[warning] 缺少核心特征: {missing_core}，预测可靠性可能下降")
    else:
        print("[info] 核心特征完整")

    # ===== 核心变量强校验（目标变量必须存在）=====
    if "green_bond_yield" not in df.columns:
        raise ValueError(
            f"缺少目标变量 green_bond_yield，当前列：{list(df.columns)}"
        )

    # ===== 关键解释变量（可缺，但提示）=====
    if "treasury_10y" not in df.columns:
        print("[warning] 缺少 treasury_10y，模型解释性下降")

    if args.oil_pred_csv:
        oil_df = pd.read_csv(args.oil_pred_csv)

        # 日期对齐
        if "Date_target" not in oil_df.columns:
            raise ValueError(f"oil_pred.csv 缺少 Date_target，实际列: {oil_df.columns}")

        oil_df["date"] = pd.to_datetime(oil_df["Date_target"], errors="coerce")
        # 列名统一
        oil_df = oil_df.rename(columns={
            "Oil_GRU_z_used": "oil_price_pred"
        })

        # 合并（以 bond 数据为主）
        df = pd.merge_asof(
            df.sort_values("date"),
            oil_df.sort_values("date"),
            on="date",
            direction="backward",
            tolerance=pd.Timedelta("7D")
        )

        print(f"[info] 已合并 oil_pred.csv，行数: {len(oil_df)}")

        missing_ratio = df["oil_price_pred"].isna().mean()
        print(f"[debug] oil_price_pred 缺失比例: {missing_ratio:.2%}")

        if missing_ratio > 0.5:
            raise ValueError("oil_pred.csv 与 bond 数据日期对不上，超过50%缺失")

    df = df.ffill()

    CORE_FEATURES = ["treasury_10y", "green_bond_yield"]

    drop_cols = [c for c in CORE_FEATURES if c in df.columns]

    if len(drop_cols) == 0:
        raise ValueError("缺少核心特征，无法建模")

    print(f"[info] 用于缺失值过滤的核心列: {drop_cols}")

    df = df.dropna(subset=drop_cols)

    # Stage1 特征（必须 shift）
    df["oil_price_pred"] = df["oil_price_pred"].shift(1)
    df["treasury_10y"] = df["treasury_10y"].shift(1)
    df["fed_rate_exp"] = df["fed_rate_exp"].shift(1)
    df["ecb_rate_exp"] = df["ecb_rate_exp"].shift(1)
    df["oil_volatility"] = df["oil_volatility"].shift(1)

    # 滞后：利差与资金流通常对收益率有滞后影响
    df["greenium_lag1"] = df["greenium"].shift(1)
    df["esg_flow_lag1"] = df["esg_flow"].shift(1)
    # ===== 加入自回归特征（核心改动）=====
    df["y_lag1"] = df["green_bond_yield"].shift(1)
    df["y_lag2"] = df["green_bond_yield"].shift(2)
    # PolicyRateAvg_t：用美/欧政策利率预期均值近似
    df["policy_rate_avg"] = (df["fed_rate_exp"].astype(float) + df["ecb_rate_exp"].astype(float)) / 2.0
    crisis_col = (args.crisis_dummy_col or "").strip()
    if crisis_col and crisis_col in df.columns:
        df["crisis_x_oil_vol"] = df[crisis_col].astype(float) * df["oil_volatility"].astype(float)

    # 交互项：用于 stage2 的非线性残差修正（不强制进入主线性方程）
    df["oil_vol_x_greenium_lag1"] = df["oil_volatility"].astype(float) * df["greenium_lag1"].astype(float)
    df["oil_vol_x_esg_flow_lag1"] = df["oil_volatility"].astype(float) * df["esg_flow_lag1"].astype(float)
    # 额外增强项：用于提升 Ridge 基线的表达能力（仍基于公式变量）
    df["oil_volatility_sq"] = df["oil_volatility"].astype(float) ** 2
    df["oil_price_pred_x_oil_vol"] = df["oil_price_pred"].astype(float) * df["oil_volatility"].astype(float)
    df["treasury_x_policy_rate_avg"] = df["treasury_10y"].astype(float) * df["policy_rate_avg"].astype(float)
    df["greenium_x_esg_flow_lag1"] = df["greenium_lag1"].astype(float) * df["esg_flow_lag1"].astype(float)
    if args.paper_synthesis:
        df = _add_paper_features(
            df, chol_window=int(args.chol_window), ewma_span=int(args.ewma_span)
        )
        df["greenium_x_vol_lag1"] = df["greenium_x_vol"].shift(1)
    df = df.dropna().reset_index(drop=True)

    # 主预测方程（按你给的公式）：
    # Y_{GB,t+1} = α
    #          + β1 * OilPricePred_t
    #          + β2 * Treasury10Y_t
    #          + β3 * PolicyRateAvg_t
    #          + γ1 * Greenium_{t-1}
    #          + γ2 * ESGFlow_{t-1}
    #          + γ3 * OilVolatility_t
    #          + （可选）CrisisDummy_t * OilVolatility_t
    # 其中 Greenium_{t-1}/ESGFlow_{t-1} 由 shift(1) 得到。
    # Ridge 基线：先只使用公式六特征（避免过拟合；R2 通过 ridge_alpha 调参提升）
    BASE_FEATURES = [
        "oil_price_pred",
        "treasury_10y",
        "policy_rate_avg",
        "greenium_lag1",
        "esg_flow_lag1",
        "oil_volatility",
    ]

    # 自动筛选存在的特征
    stage1_features = [f for f in BASE_FEATURES if f in df.columns]
    # ===== 加入 AR 特征到模型 =====
    if "y_lag1" in df.columns:
        stage1_features.append("y_lag1")
    if "y_lag2" in df.columns:
        stage1_features.append("y_lag2")

    print(f"[info] 实际用于建模的特征: {stage1_features}")

    if "crisis_x_oil_vol" in df.columns:
        stage1_features.append("crisis_x_oil_vol")
    stage1_features = [f for f in stage1_features if f in df.columns]

    # 先关闭 stage2，避免过拟合把 R2 拉坏
    stage2_features = [
        "oil_vol_x_greenium_lag1",
        "oil_vol_x_esg_flow_lag1",
        "oil_price_pred_x_oil_vol",
        "treasury_x_policy_rate_avg",
        "greenium_x_esg_flow_lag1"
    ]
    target = "green_bond_yield"

    min_len = 30 if not args.paper_synthesis else max(30, int(args.chol_window) + 15)
    if len(df) < min_len:
        raise RuntimeError(f"有效样本过少: {len(df)}（文献模式建议 ≥ {min_len}）")

    split_idx = int(len(df) * (1 - float(args.test_ratio)))
    split_idx = max(10, min(split_idx, len(df) - 5))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    # 如果第一阶段特征在训练/测试中全为 0（例如你删除了宏观/油价数据后 merged 数据用 0 补），
    # 则剔除它们，避免第一阶段学不到任何信息。
    stage1_features_use: list[str] = []
    for f in stage1_features:
        if f not in df.columns:
            continue
        train_sum = float(train_df[f].abs().sum())
        test_sum = float(test_df[f].abs().sum())
        if (train_sum + test_sum) > 0.0:
            stage1_features_use.append(f)
    if len(stage1_features_use) != len(stage1_features):
        print(f"[info] 第一阶段有效特征：{stage1_features_use}（原始：{stage1_features}，已剔除全0列）")

    print("=" * 60)
    print("线性方程基线 + stage2 残差修正（尽量提高 R2）")
    if args.paper_synthesis:
        print(
            "[paper-synthesis] 使用条件分位数 CI（主预测仍为线性方程）"
        )
    print("=" * 60)
    print(f"数据：{data_path}")
    print(f"第一阶段特征（有效）：{stage1_features_use}")
    print(f"第二阶段特征：{stage2_features}")
    print(f"样本：总 {len(df)} | 训练 {len(train_df)} | 测试 {len(test_df)}")
    print(f"第二阶段 GBDT 参数：{gb_kw}")

    # holdout：用于主 CSV / 图（与原先一致）
    X2_train, X2_test = train_df[stage2_features], test_df[stage2_features]
    y_train, y_test = train_df[target], test_df[target]
    y_train_arr = np.asarray(y_train, dtype=float)
    y_test_arr = np.asarray(y_test, dtype=float)

    # 第一阶段：如果没有可用宏观特征，就用训练集均值做基线预测。
    if len(stage1_features_use) > 0:
        X1_train, X1_test = train_df[stage1_features_use], test_df[stage1_features_use]
        sc1 = StandardScaler()
        X1_tr = sc1.fit_transform(X1_train)
        X1_te = sc1.transform(X1_test)

        # ridge_alpha 简单调参：只在 train 内切一个验证段选 alpha，避免对 holdout test 泄漏
        cand_alphas = [
            0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5,
            1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0,
            200.0, 300.0, 500.0, 1000.0,
        ]
        # 若用户显式给的 ridge_alpha 不在候选集合中，也加进去
        if float(args.ridge_alpha) not in cand_alphas:
            cand_alphas.append(float(args.ridge_alpha))
        cand_alphas = sorted(set(cand_alphas))

        # 内部验证段：取训练集最后 20%
        n_train = len(train_df)
        n_val = max(10, int(round(n_train * 0.2)))
        n_fit = n_train - n_val
        X_fit = X1_tr[:n_fit]
        y_fit = y_train_arr[:n_fit]
        X_val = X1_tr[n_fit:]
        y_val = y_train_arr[n_fit:]

        best_alpha = float(args.ridge_alpha)
        best_r2 = -np.inf
        for a in cand_alphas:
            m = Ridge(alpha=float(a))
            m.fit(X_fit, y_fit)
            y_val_pred = m.predict(X_val)
            r2v = float(r2_score(y_val, y_val_pred))
            if r2v > best_r2:
                best_r2 = r2v
                best_alpha = float(a)

        model1 = Ridge(alpha=float(best_alpha))
        model1.fit(X1_tr, y_train_arr)
        y_tr_p1 = model1.predict(X1_tr)
        y_te_p1 = model1.predict(X1_te)
        res_tr = y_train_arr - y_tr_p1
        res_te = y_test_arr - y_te_p1

        print("\n===== 线性方程（Ridge）=====")
        print(
            f"[ridge-tune] best_alpha={best_alpha}  val_R2={best_r2:.4f}  "
            f"训练 R2: {r2_score(y_train_arr, y_tr_p1):.4f}  测试 R2: {r2_score(y_test_arr, y_te_p1):.4f}"
        )
    else:
        base_pred = float(np.mean(y_train_arr))
        y_tr_p1 = np.full_like(y_train_arr, base_pred, dtype=float)
        y_te_p1 = np.full_like(y_test_arr, base_pred, dtype=float)
        res_tr = y_train_arr - base_pred
        res_te = y_test_arr - base_pred

        print("\n===== 线性方程（无有效特征：训练均值基线）=====")
        print(f"训练 R2: {r2_score(y_train_arr, y_tr_p1):.4f}  测试 R2: {r2_score(y_test_arr, y_te_p1):.4f}")

    # 主预测：当前配置使用 Ridge 基线（stage2 默认关闭）
    if len(stage2_features) == 0:
        y_final_tr = y_tr_p1
        y_final_te = y_te_p1
        print("\n===== 二阶段残差修正：关闭（stage2_features 为空）=====")
        print(
            f"最终 测试 RMSE: {np.sqrt(mean_squared_error(y_test_arr, y_final_te)):.6f}  "
            f"MAE: {mean_absolute_error(y_test_arr, y_final_te):.6f}  R2: {r2_score(y_test_arr, y_final_te):.4f}"
        )
    else:
        # 二阶段：拟合第一阶段残差
        sc2 = StandardScaler()
        X2_tr = sc2.fit_transform(X2_train)
        X2_te = sc2.transform(X2_test)
        gb = GradientBoostingRegressor(**gb_kw)
        gb.fit(X2_tr, res_tr)
        pred_res_tr = gb.predict(X2_tr)
        pred_res_te = gb.predict(X2_te)
        # 训练集上对残差修正做强度标定（shrinkage），避免过度修正导致 holdout R2 下滑
        denom = float(np.sum(np.square(pred_res_tr)) + 1e-12)
        alpha = float(np.sum(res_tr * pred_res_tr) / denom)
        alpha = float(np.clip(alpha, -1.5, 1.5))
        y_final_tr = y_tr_p1 + alpha * pred_res_tr
        y_final_te = y_te_p1 + alpha * pred_res_te
        print("\n===== 二阶段（GBDT 拟合残差）=====")
        print(
            f"残差 R2 训练: {r2_score(res_tr, pred_res_tr):.4f}  测试: {r2_score(res_te, pred_res_te):.4f}"
        )
        print(f"[stage2] residual shrinkage alpha={alpha:.4f}")
        print(
            f"最终 测试 RMSE: {np.sqrt(mean_squared_error(y_test_arr, y_final_te)):.6f}  "
            f"MAE: {mean_absolute_error(y_test_arr, y_final_te):.6f}  R2: {r2_score(y_test_arr, y_final_te):.4f}"
        )
    if args.paper_synthesis:
        # 为了更贴近 QQ/分位回归思想：直接对 y_t 的条件分位数做预测，
        # 再用 (τ_low, τ_high) 生成 CI（而不是在 residual 上再叠加）。
        tau_pair = {0.90: (0.05, 0.95), 0.95: (0.025, 0.975), 0.99: (0.005, 0.995)}
        lo, hi = tau_pair[float(args.conf_level)]

        # 条件分位数的自变量：沿用两阶段模型的特征，但合并成单一 Xq。
        xq_features = [*stage1_features_use, *stage2_features]
        xq_features = [f for f in xq_features if f in df.columns]

        if len(xq_features) == 0:
            # 理论上不会发生（stage2 至少存在），但兜底保持可运行。
            y_tr_q = np.asarray(y_train_arr, dtype=float)
            ci_lo_r = np.full(shape=(len(y_test_arr),), fill_value=float(np.quantile(y_tr_q, lo)), dtype=float)
            ci_hi_r = np.full(shape=(len(y_test_arr),), fill_value=float(np.quantile(y_tr_q, hi)), dtype=float)
        else:
            Xq_train = train_df[xq_features]
            Xq_test = test_df[xq_features]
            scq = StandardScaler()
            Xq_tr = scq.fit_transform(Xq_train)
            Xq_te = scq.transform(Xq_test)

            gb_lo = GradientBoostingRegressor(loss="quantile", alpha=lo, **{**gb_kw, "random_state": 44})
            gb_hi = GradientBoostingRegressor(loss="quantile", alpha=hi, **{**gb_kw, "random_state": 45})
            gb_lo.fit(Xq_tr, y_train_arr)
            gb_hi.fit(Xq_tr, y_train_arr)
            ci_lo_r = gb_lo.predict(Xq_te).astype(float)
            ci_hi_r = gb_hi.predict(Xq_te).astype(float)

            # 保证区间上下界顺序正确（quantile 学习可能产生轻微交叉）
            lo_swap = np.minimum(ci_lo_r, ci_hi_r)
            hi_swap = np.maximum(ci_lo_r, ci_hi_r)
            ci_lo_r, ci_hi_r = lo_swap, hi_swap

        print(f"\n===== 文献模式：条件分位数 CI（Lin 思路近似，τ 分位=({lo},{hi})）=====")

    if args.walk_forward:
        wf_min = max(20, int(args.wf_min_train))
        wf_step = max(1, int(args.wf_step))
        if wf_min + wf_step > len(df):
            print(
                f"\n[walk-forward] 跳过：wf_min_train({wf_min}) + wf_step({wf_step}) > 样本({len(df)})"
            )
        else:
            wf_df = _walk_forward_eval(
                df,
                stage1_features_use,
                stage2_features,
                target,
                float(args.ridge_alpha),
                wf_min,
                wf_step,
                gb_kw=gb_kw,
            )
            print("\n" + "=" * 60)
            print("Walk-forward 块验证（扩展训练窗，测试块不重叠）")
            print("=" * 60)
            print(f"wf_min_train={wf_min}  wf_step={wf_step}  折数={len(wf_df)}")
            if len(wf_df) == 0:
                print("无有效折，请增大样本或减小 wf_min_train / wf_step")
            else:
                print(wf_df.to_string(index=False))
                print(
                    f"\n折间均值 — RMSE: {wf_df['RMSE'].mean():.6f}  MAE: {wf_df['MAE'].mean():.6f}  "
                    f"R2: {wf_df['R2'].mean():.4f}"
                )
                print(
                    f"折间标准差 — RMSE: {wf_df['RMSE'].std():.6f}  MAE: {wf_df['MAE'].std():.6f}  "
                    f"R2: {wf_df['R2'].std():.4f}"
                )
                out_dir_wf = os.path.abspath(args.out_dir)
                os.makedirs(out_dir_wf, exist_ok=True)
                wf_name = (args.wf_metrics_csv or "").strip()
                if wf_name:
                    wf_path = _resolve_output_path(wf_name, out_dir_wf)
                    wf_df.to_csv(wf_path, index=False, encoding="utf-8-sig")
                    print(f"\nWalk-forward 指标已保存：{wf_path}")

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = _resolve_output_path(args.output_csv, out_dir)

    dates = test_df["date"].dt.strftime("%Y-%m-%d").values
    oil_used = test_df["oil_price_pred"].astype(float).values
    mean_pred = y_final_te.astype(float)

    # ===== Actual vs Pred 图 =====
    try:
        plot_prediction(
            y_true=y_test_arr.flatten(),
            y_pred=mean_pred.flatten(),
            save_path=f"{stem}_plot_actual_vs_pred.png"
        )
        print(f"已保存图表：{stem}_plot_actual_vs_pred.png")
    except Exception as e:
        print(f"[警告] 生成 Actual vs Pred 图失败：{e}")

    if args.paper_synthesis:
        sigma = np.maximum((ci_hi_r - ci_lo_r) / (2.0 * z_alpha), 1e-12)
        ci_low_out = np.asarray(ci_lo_r, dtype=float)
        ci_high_out = np.asarray(ci_hi_r, dtype=float)
    else:
        res_te_arr = np.asarray(res_te, dtype=float)
        sigma = np.abs(res_te_arr)
        sigma = np.maximum(sigma, 1e-12)
        ci_low_out = (mean_pred - z_alpha * sigma).astype(float)
        ci_high_out = (mean_pred + z_alpha * sigma).astype(float)

    out = pd.DataFrame(
        {
            "Date_target": dates,
            "Oil_GRU_z_used": oil_used,
            "NewEnergy_MeanPred": mean_pred,
            "NewEnergy_Sigma": sigma,
            "CI_low": ci_low_out,
            "CI_high": ci_high_out,
            "ConfLevel": float(args.conf_level),
        }
    )
    q50 = float(out["NewEnergy_Sigma"].quantile(0.5))
    q80 = float(out["NewEnergy_Sigma"].quantile(0.8))
    out["RiskLevel"] = np.where(
        out["NewEnergy_Sigma"] >= q80, "HIGH", np.where(out["NewEnergy_Sigma"] >= q50, "MEDIUM", "LOW")
    )

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n已保存：{out_path}")

    stem = out_path.rsplit(".", 1)[0]
    if args.make_viz:
        try:
            op = out.copy()
            op["Date_target"] = pd.to_datetime(op["Date_target"], errors="coerce")
            op = op.dropna(subset=["Date_target"]).sort_values("Date_target")

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(op["Date_target"], op["NewEnergy_MeanPred"], label="MeanPred", linewidth=1.4)
            ax.fill_between(
                op["Date_target"],
                op["CI_low"],
                op["CI_high"],
                alpha=0.25,
                label=f"{int(float(args.conf_level) * 100)}% CI",
            )
            ax.set_title("Green Bond Mean Prediction with Confidence Band")
            ax.set_xlabel("Date")
            ax.set_ylabel("Yield")
            ax.legend()
            ax.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(f"{stem}_plot_ci.png", dpi=150)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(op["Date_target"], op["NewEnergy_Sigma"], label="Sigma", color="#1f77b4", linewidth=1.3)
            ax.axhline(q50, color="#ff7f0e", linestyle="--", label="Q50")
            ax.axhline(q80, color="#d62728", linestyle="--", label="Q80")
            ax.set_title("Volatility Proxy (Sigma) and Risk Thresholds")
            ax.set_xlabel("Date")
            ax.set_ylabel("Sigma")
            ax.legend()
            ax.grid(alpha=0.3)
            fig.tight_layout()
            fig.savefig(f"{stem}_plot_sigma.png", dpi=150)
            plt.close(fig)

            risk_order = ["LOW", "MEDIUM", "HIGH"]
            rc = op["RiskLevel"].value_counts().reindex(risk_order, fill_value=0)
            fig, ax = plt.subplots(figsize=(7, 4))
            bars = ax.bar(rc.index, rc.values, color=["#2ca02c", "#ffbf00", "#d62728"])
            ax.set_title("Risk Level Distribution")
            ax.set_xlabel("RiskLevel")
            ax.set_ylabel("Count")
            for b in bars:
                h = b.get_height()
                ax.text(b.get_x() + b.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontsize=9)
            ax.grid(axis="y", alpha=0.25)
            fig.tight_layout()
            fig.savefig(f"{stem}_plot_risk.png", dpi=150)
            plt.close(fig)
            print(f"已保存图表：{stem}_plot_ci.png / {stem}_plot_sigma.png / {stem}_plot_risk.png")
        except Exception as e:
            print(f"[警告] 生成图表失败：{e}")



    try:
        risk_counts = out["RiskLevel"].value_counts(dropna=False).to_dict()
        ci_width = (out["CI_high"] - out["CI_low"]).values.astype(float)
        quantiles = out["NewEnergy_Sigma"].quantile([0.1, 0.5, 0.9]).to_dict()
        top_rows = out.loc[
            out["NewEnergy_Sigma"].sort_values(ascending=False).head(5).index,
            ["Date_target", "NewEnergy_Sigma", "RiskLevel"],
        ].copy()

        print("\n" + "=" * 60)
        print("绿债风险与置信区间分析报告（列名与新能源脚本对齐，便于统一读取）")
        print("=" * 60)
        print(f"样本数（测试集）：{len(out)}")
        print(f"置信水平：{float(args.conf_level):.2f}（z_alpha={z_alpha:.3f}）")
        print(f"RiskLevel 统计：{risk_counts}")
        print("NewEnergy_Sigma 分位数：")
        for q, v in quantiles.items():
            print(f"  {q:.1f}分位：{float(v):.6f}")
        print(f"CI 宽度均值：{float(np.mean(ci_width)):.6f}  最大：{float(np.max(ci_width)):.6f}")
        print("Top-5 高 Sigma 日期：")
        print(top_rows.to_string(index=False))
        if args.paper_synthesis:
            print(
                "\n说明：NewEnergy_MeanPred=两阶段最终预测；CI 为残差分位数 GB（Lin 近似）；"
                "NewEnergy_Sigma=(CI_high-CI_low)/(2z)；Oil_GRU_z_used=油价预测值。"
            )
        else:
            print(
                "\n说明：NewEnergy_MeanPred=两阶段最终预测；NewEnergy_Sigma=第一阶段残差绝对值；"
                "Oil_GRU_z_used=油价预测值。"
            )
    except Exception as e:
        print(f"[警告] 终端报告失败：{e}")


if __name__ == "__main__":
    main()
