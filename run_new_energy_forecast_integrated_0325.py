# -*- coding: utf-8 -*-
"""
该脚本联合 `predict_new_energy_from_gru.py` 使用。

常用启动命令示例：
python .\run_new_energy_forecast_integrated.py --series new_energy --conf-level 0.95 --rebuild-returns --make-viz

该脚本用于整合新能源 datawork，使其能被 `predict_new_energy_from_gru.py` 使用。
"""
 
import argparse
import glob
import subprocess
import sys
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _to_float_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


def _to_datetime_series(s: pd.Series) -> pd.Series:
    """
    优先按 YYYYMMDD 解析（很多指数文件日期是 8 位整数），失败再用通用解析。
    """
    s_str = s.astype(str).str.strip()
    dt_ymd = pd.to_datetime(s_str, format="%Y%m%d", errors="coerce")
    dt_fallback = pd.to_datetime(s, errors="coerce")
    return dt_ymd.fillna(dt_fallback)


def compute_log_return(close: pd.Series, scale: float = 100.0) -> pd.Series:
    """
    按论文/脚本口径生成对数收益代理：r_t = scale * ln(P_t / P_{t-1})
    """
    close = _to_float_series(close)
    return scale * np.log(close / close.shift(1))


def load_perf_returns(perf_path: str, date_col: str, close_col: str, scale: float = 100.0) -> pd.DataFrame:
    df = pd.read_excel(perf_path)
    if date_col not in df.columns:
        raise ValueError(f"perf 文件缺少日期列：{date_col}，实际列：{list(df.columns)}")
    if close_col not in df.columns:
        raise ValueError(f"perf 文件缺少收盘列：{close_col}，实际列：{list(df.columns)}")

    df = df[[date_col, close_col]].copy()
    df[date_col] = _to_datetime_series(df[date_col])
    df[close_col] = _to_float_series(df[close_col])
    df = df.dropna(subset=[date_col, close_col]).sort_values(date_col)

    out = pd.DataFrame(
        {
            "Date": df[date_col],
            "r_new": compute_log_return(df[close_col], scale=scale),
        }
    )
    out = out.dropna(subset=["r_new"]).drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
    return out


def load_zip_returns(zip_path: str, indexcd: int, scale: float = 100.0) -> pd.DataFrame:
    z = zipfile.ZipFile(zip_path)
    csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise ValueError(f"zip 内找不到 csv：{zip_path}")
    # 你的 zip 里 csv 文件名是固定的 IDX_Idxtrd.csv，这里取第一个 csv 即可
    csv_name = csv_names[0]

    df = pd.read_csv(z.open(csv_name))
    need_cols = {"Indexcd", "Idxtrd01", "Idxtrd05"}
    if not need_cols.issubset(df.columns):
        raise ValueError(f"zip csv 列名不匹配，需要 {need_cols}，实际列：{list(df.columns)}")

    df = df[df["Indexcd"] == indexcd].copy()
    df["Date"] = _to_datetime_series(df["Idxtrd01"])
    df["close"] = _to_float_series(df["Idxtrd05"])
    df = df.dropna(subset=["Date", "close"]).sort_values("Date")

    out = pd.DataFrame({"Date": df["Date"], "r_new": compute_log_return(df["close"], scale=scale)})
    out = out.dropna(subset=["r_new"]).drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
    return out


def find_files(desktop_base: Path, patterns: list[str]) -> list[str]:
    """
    在桌面目录下递归查找匹配的文件。
    这里用 patterns 只包含文件名/后缀的关键片段，避免在命令行/字符串里出现中文路径导致编码问题。
    """
    results: list[str] = []
    for pat in patterns:
        # recursive glob: ** 适配多层目录
        results.extend(glob.glob(str(desktop_base / "**" / pat), recursive=True))
    # 去重且稳定排序
    results = sorted(list(set(results)))
    return results


def build_returns_for_series(
    series: str,
    desktop_base: Path,
    scale: float,
) -> pd.DataFrame:
    """
    series:
      - new_energy : 来自中证环保&上证新能源 zip 中 Indexcd=941（名称字段为“新能源”）
      - csi_env    : 来自中证环保&上证新能源 zip 中 Indexcd=827（名称字段为“中证环保”）
      - esg300     : 来自 ESG300 perf（.xls）
      - csi120_esg : 来自 中证120ESG策略指数 perf（931476perf.xlsx）
      - csi300_esg : 来自 沪深300ESG基准指数 perf（931463perf.xlsx）
    """
    if series in {"new_energy", "csi_env"}:
        # 你给的三个 zip，对应不同时段：143136736/143542603/143658220
        zip_digits = ["143136736", "143542603", "143658220"]
        zip_paths = []
        for d in zip_digits:
            # 只按数字片段定位，避免包含中文目录名
            matches = find_files(desktop_base, [f"*{d}*.zip"])
            zip_paths.extend(matches)
        zip_paths = sorted(list(set(zip_paths)))
        if not zip_paths:
            raise FileNotFoundError(f"未在桌面目录下找到新能源 zip（digits={zip_digits}）")

        indexcd = 941 if series == "new_energy" else 827
        parts = [load_zip_returns(zp, indexcd=indexcd, scale=scale) for zp in zip_paths]
        df = pd.concat(parts, ignore_index=True)
        df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date").reset_index(drop=True)
        return df

    if series == "esg300":
        matches = find_files(desktop_base, ["*399378_perf_20160104-20260316*.xls", "*399378_perf_*.xls"])
        if not matches:
            raise FileNotFoundError("未找到 ESG300 perf(.xls)")
        return load_perf_returns(matches[0], date_col="日期", close_col="收盘价", scale=scale)

    if series == "csi120_esg":
        matches = find_files(desktop_base, ["*931476perf.xlsx"])
        if not matches:
            raise FileNotFoundError("未找到 931476perf.xlsx（中证120ESG策略指数）")
        return load_perf_returns(matches[0], date_col="日期Date", close_col="收盘Close", scale=scale)

    if series == "csi300_esg":
        matches = find_files(desktop_base, ["*931463perf.xlsx"])
        if not matches:
            raise FileNotFoundError("未找到 931463perf.xlsx（沪深300ESG基准指数）")
        return load_perf_returns(matches[0], date_col="日期Date", close_col="收盘Close", scale=scale)

    raise ValueError(f"未知 series：{series}")


def call_predict_script(
    predict_script: Path,
    oil_pred_csv: Path,
    new_energy_returns_csv: Path,
    out_csv: Path,
    conf_level: float,
    scale_oil_return: float,
):
    cmd = [
        sys.executable,
        str(predict_script),
        "--prediction-csv",
        str(oil_pred_csv),
        "--new-energy-csv",
        str(new_energy_returns_csv),
        "--new-date-col",
        "Date",
        "--new-return-col",
        "r_new",
        "--conf-level",
        str(conf_level),
        "--scale-oil-return",
        str(scale_oil_return),
        "--output-csv",
        str(out_csv),
    ]
    subprocess.run(cmd, check=True)


def generate_visualizations(
    out_dir: Path,
    forecast_map: dict[str, Path],
):
    """
    基于每个 series 的 forecast csv 生成对比图：
      1) Sigma 时间序列对比
      2) RiskLevel 分布对比
      3) CI 宽度分布箱线图
    """
    data_map: dict[str, pd.DataFrame] = {}
    for series, fp in forecast_map.items():
        if not fp.exists():
            continue
        df = pd.read_csv(fp)
        if "Date_target" not in df.columns:
            continue
        df["Date_target"] = pd.to_datetime(df["Date_target"], errors="coerce")
        df = df.dropna(subset=["Date_target"]).sort_values("Date_target")
        data_map[series] = df

    if not data_map:
        print("[可视化] 未找到可用 forecast 文件，跳过绘图。")
        return

    # 1) Sigma 时间序列对比
    fig, ax = plt.subplots(figsize=(12, 5))
    for series, df in data_map.items():
        if "NewEnergy_Sigma" not in df.columns:
            continue
        ax.plot(df["Date_target"], df["NewEnergy_Sigma"], linewidth=1.2, label=series)
    ax.set_title("Sigma Comparison Across Series")
    ax.set_xlabel("Date")
    ax.set_ylabel("Sigma")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    sigma_cmp = out_dir / "compare_sigma_timeseries.png"
    fig.savefig(sigma_cmp, dpi=150)
    plt.close(fig)

    # 2) 风险等级分布对比
    risk_order = ["LOW", "MEDIUM", "HIGH"]
    risk_df = pd.DataFrame(index=risk_order)
    for series, df in data_map.items():
        if "RiskLevel" not in df.columns:
            continue
        counts = df["RiskLevel"].value_counts().reindex(risk_order, fill_value=0)
        risk_df[series] = counts
    if not risk_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        risk_df.T.plot(kind="bar", stacked=True, ax=ax)
        ax.set_title("Risk Level Distribution by Series")
        ax.set_xlabel("Series")
        ax.set_ylabel("Count")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(title="RiskLevel")
        fig.tight_layout()
        risk_cmp = out_dir / "compare_risk_distribution.png"
        fig.savefig(risk_cmp, dpi=150)
        plt.close(fig)

    # 3) CI 宽度分布箱线图
    widths = []
    labels = []
    for series, df in data_map.items():
        if {"CI_low", "CI_high"}.issubset(df.columns):
            w = (pd.to_numeric(df["CI_high"], errors="coerce") - pd.to_numeric(df["CI_low"], errors="coerce")).dropna()
            if len(w) > 0:
                widths.append(w.values)
                labels.append(series)
    if widths:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.boxplot(widths, tick_labels=labels, showfliers=False)
        ax.set_title("Confidence Interval Width Distribution")
        ax.set_xlabel("Series")
        ax.set_ylabel("CI Width")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        ci_cmp = out_dir / "compare_ci_width_boxplot.png"
        fig.savefig(ci_cmp, dpi=150)
        plt.close(fig)

    print(f"[可视化] 已生成：{sigma_cmp}")
    if not risk_df.empty:
        print(f"[可视化] 已生成：{out_dir / 'compare_risk_distribution.png'}")
    if widths:
        print(f"[可视化] 已生成：{out_dir / 'compare_ci_width_boxplot.png'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--oil-pred-csv",
        default=str(Path(__file__).resolve().parent / "prediction_results.csv"),
        help="油价预测结果 csv（含 Date_target / GRU_Pred_Return）",
    )
    ap.add_argument(
        "--series",
        default="new_energy",
        help="要跑的序列，逗号分隔：new_energy,csi_env,esg300,csi120_esg,csi300_esg",
    )
    ap.add_argument(
        "--scale",
        type=float,
        default=100.0,
        help="收益缩放：r_new = scale * ln(P_t/P_{t-1})",
    )
    ap.add_argument(
        "--desktop-base",
        default=str(Path.home() / "Desktop"),
        help="用于搜索你附件中 zip/xlsx/xls 的桌面目录根路径（默认自动取当前用户 Desktop）",
    )
    ap.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parent / "new_energy_integrated_outputs"),
        help="输出目录（包含中间 returns csv + 最终 forecast csv）",
    )
    ap.add_argument("--conf-level", type=float, default=0.95, help="置信水平：0.90/0.95/0.99")
    ap.add_argument("--scale-oil-return", type=float, default=100.0, help="与 predict_new_energy_from_gru.py 保持一致的油收益缩放")
    ap.add_argument("--rebuild-returns", action="store_true", help="强制重建 returns csv")
    ap.add_argument("--make-viz", action="store_true", help="跑完后生成对比可视化图片")
    ap.add_argument(
        "--align-to-oil-dates",
        action="store_true",
        default=True,
        help="将 returns 的 Date 过滤到油价预测的 Date_target 交集，避免均值回归矩阵里出现 NaN 导致 lstsq 不收敛",
    )
    args = ap.parse_args()

    oil_pred_csv = Path(args.oil_pred_csv).resolve()
    predict_script = Path(__file__).resolve().parent / "predict_new_energy_from_gru.py"
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    desktop_base = Path(args.desktop_base).resolve()
    series_list = [s.strip() for s in args.series.split(",") if s.strip()]

    if not oil_pred_csv.exists():
        raise FileNotFoundError(f"--oil-pred-csv 不存在：{oil_pred_csv}")
    if not predict_script.exists():
        raise FileNotFoundError(f"找不到脚本：{predict_script}")

    # 供对齐日期使用（预测脚本会把这些日期字符串用于映射 z/lambda）
    oil_df = pd.read_csv(oil_pred_csv)
    if "Date_target" not in oil_df.columns:
        raise ValueError("oil-pred-csv 缺少列：Date_target")
    oil_df["Date_target"] = pd.to_datetime(oil_df["Date_target"], errors="coerce")
    oil_dates_str = set(oil_df["Date_target"].dt.strftime("%Y-%m-%d").dropna().tolist())

    forecast_map: dict[str, Path] = {}
    for series in series_list:
        returns_csv = out_dir / f"new_energy_returns_{series}.csv"
        out_csv = out_dir / f"new_energy_forecast_{series}_conf{args.conf_level}.csv"

        if args.rebuild_returns or (not returns_csv.exists()):
            df_ret = build_returns_for_series(series=series, desktop_base=desktop_base, scale=args.scale)
            if args.align_to_oil_dates:
                df_ret = df_ret[df_ret["Date"].dt.strftime("%Y-%m-%d").isin(oil_dates_str)].copy()
                df_ret = df_ret.sort_values("Date").reset_index(drop=True)
            df_ret.to_csv(returns_csv, index=False, encoding="utf-8-sig")
            print(f"[{series}] 已生成 returns：{returns_csv}（样本数={len(df_ret)}）")
        else:
            print(f"[{series}] 使用已有 returns：{returns_csv}")

        if returns_csv.exists():
            ret_df = pd.read_csv(returns_csv)
            if len(ret_df) < 10:
                print(f"[{series}] returns 样本过少（{len(ret_df)}），跳过预测。")
                continue

        print(f"[{series}] 开始调用 predict_new_energy_from_gru.py ...")
        try:
            call_predict_script(
                predict_script=predict_script,
                oil_pred_csv=oil_pred_csv,
                new_energy_returns_csv=returns_csv,
                out_csv=out_csv,
                conf_level=args.conf_level,
                scale_oil_return=args.scale_oil_return,
            )
            print(f"[{series}] 完成输出：{out_csv}")
            forecast_map[series] = out_csv
        except Exception as e:
            print(f"[{series}] 预测失败，已跳过。错误：{e}")

    if args.make_viz:
        generate_visualizations(out_dir=out_dir, forecast_map=forecast_map)


if __name__ == "__main__":
    main()

