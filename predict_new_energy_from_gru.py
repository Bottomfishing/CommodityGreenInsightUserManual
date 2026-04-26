import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def export_chart_csvs(out: pd.DataFrame, output_csv_path: str) -> list[str]:
    """
    导出前端可直接渲染的图表 CSV（尽量多图，先用写死图）。
    返回生成的文件路径列表。
    """
    stem = output_csv_path.rsplit(".", 1)[0]
    saved: list[str] = []

    # 1) 均值预测 + CI
    ci_df = out[
        ["Date_target", "NewEnergy_MeanPred", "CI_low", "CI_high", "NewEnergy_Sigma"]
    ].copy()
    ci_path = f"{stem}_chart_ci_band.csv"
    ci_df.to_csv(ci_path, index=False, encoding="utf-8-sig")
    saved.append(ci_path)

    # 2) Sigma + 阈值线
    q50 = float(out["NewEnergy_Sigma"].quantile(0.5))
    q80 = float(out["NewEnergy_Sigma"].quantile(0.8))
    sigma_df = out[["Date_target", "NewEnergy_Sigma"]].copy()
    sigma_df["Q50"] = q50
    sigma_df["Q80"] = q80
    sigma_path = f"{stem}_chart_sigma.csv"
    sigma_df.to_csv(sigma_path, index=False, encoding="utf-8-sig")
    saved.append(sigma_path)

    # 3) 风险等级分布
    risk_order = ["LOW", "MEDIUM", "HIGH"]
    risk_counts = out["RiskLevel"].value_counts().reindex(risk_order, fill_value=0)
    risk_df = pd.DataFrame(
        {"RiskLevel": risk_counts.index, "Count": risk_counts.values}
    )
    risk_path = f"{stem}_chart_risk_distribution.csv"
    risk_df.to_csv(risk_path, index=False, encoding="utf-8-sig")
    saved.append(risk_path)

    # 4) CI 宽度分布
    ciw_df = pd.DataFrame({"CI_width": (out["CI_high"] - out["CI_low"]).astype(float)})
    ciw_path = f"{stem}_chart_ci_width_hist.csv"
    ciw_df.to_csv(ciw_path, index=False, encoding="utf-8-sig")
    saved.append(ciw_path)

    # 5) 均值预测分布
    mean_df = pd.DataFrame({"NewEnergy_MeanPred": out["NewEnergy_MeanPred"].astype(float)})
    mean_path = f"{stem}_chart_meanpred_hist.csv"
    mean_df.to_csv(mean_path, index=False, encoding="utf-8-sig")
    saved.append(mean_path)

    # 6) Lambda-Sigma 散点
    scatter_df = out[["Date_target"]].copy()
    scatter_df["Lambda_t"] = np.nan
    scatter_df["NewEnergy_Sigma"] = out["NewEnergy_Sigma"].astype(float).values
    # Lambda 来自外部变量，由调用方补充
    scatter_path = f"{stem}_chart_lambda_sigma_scatter.csv"
    scatter_df.to_csv(scatter_path, index=False, encoding="utf-8-sig")
    saved.append(scatter_path)

    return saved


def egarch_arji_variance_from_oil_return(
    oil_ret: np.ndarray,
    params: dict,
    xi_mode: str = "abs_std_resid",
):
    """
    从油价（用 GRU 预测收益序列）递推：
      1) EGARCH 条件方差 h_t
      2) 跳跃强度 λ_t
      3) V_t = 0.0001*h_t + 0.5198*λ_t - 0.5337*λ_{t-1}
    返回：
      h_t, lambda_t, V_t, sigma2_proxy
    """
    # oil_ret: z_t, 你截图里 R_oil,t 的同口径序列（已按需要乘以100）
    omega = params["omega"]
    alpha = params["alpha"]
    beta = params["beta"]
    k = params["k"]

    lam0 = params["lambda0"]
    rho = params["rho"]
    gamma = params["gamma"]

    v1 = params["v1"]
    v2 = params["v2"]
    v3 = params["v3"]

    n = len(oil_ret)
    oil_ret = oil_ret.astype(float)

    # 先用一个简化均值模型（AR(1)）得到残差 a_t
    # a_t 你截图里是“均值方程后的残差项”。这里先用最简单版本近似。
    # 如果你想严格复刻“ARMA(1,1)+N_t”，需要你把均值方程的参数也给出来/接入你的实现。
    c = np.mean(oil_ret)
    phi = 0.0
    if n >= 2:
        x = oil_ret[:-1]
        y = oil_ret[1:]
        denom = np.sum(x * x)
        if denom > 1e-12:
            phi = float(np.sum(x * y) / denom)
            c = float(np.mean(y - phi * x))

    a = np.zeros(n, dtype=float)
    a[0] = oil_ret[0] - c
    for t in range(1, n):
        a[t] = oil_ret[t] - (c + phi * oil_ret[t - 1])

    # 初始化 h_0
    a_var = np.var(a[np.isfinite(a)]) if np.isfinite(a).all() else np.var(a[~np.isnan(a)])
    if not np.isfinite(a_var) or a_var <= 1e-12:
        a_var = 1e-6
    h = np.zeros(n, dtype=float)
    h[0] = a_var

    lam = np.zeros(n, dtype=float)
    lam[0] = max(0.0, lam0 / (1 - max(rho, 0.0) + 1e-6))  # 一个稳定的初始值

    V = np.zeros(n, dtype=float)
    sigma2_proxy = np.zeros(n, dtype=float)

    for t in range(1, n):
        # EGARCH(1,1)（截图形式：ln(h_t)=ω + α*(|a_{t-1}| + k*a_{t-1})/sqrt(h_{t-1}) + β*ln(h_{t-1})
        # 你截图里还带了 abs(|a|+k*a) 的变体；这里用截图那种 (|a| + k*a)。
        ln_h_prev = np.log(max(h[t - 1], 1e-12))
        num = (abs(a[t - 1]) + k * a[t - 1])
        egarch_part = omega + alpha * (num / np.sqrt(max(h[t - 1], 1e-12))) + beta * ln_h_prev
        h[t] = float(np.exp(egarch_part))

        # 跳跃强度 λ_t：λ_t = max(0, λ0 + ρ*λ_{t-1} + γ*ξ_{t-1})
        # 按你截图定义，ξ_{t-1} 使用标准化残差绝对值 |z_{t-1}/σ_{t-1}|
        if xi_mode == "abs_std_resid":
            xi = abs(a[t - 1]) / np.sqrt(max(h[t - 1], 1e-12))
        elif xi_mode == "std_sq_minus1":
            xi = (a[t - 1] ** 2) / max(h[t - 1], 1e-12) - 1.0
        elif xi_mode == "std_sq":
            xi = (a[t - 1] ** 2) / max(h[t - 1], 1e-12)
        else:
            raise ValueError("xi_mode must be abs_std_resid / std_sq_minus1 / std_sq")

        lam[t] = max(0.0, lam0 + rho * lam[t - 1] + gamma * xi)

        # V_t = 0.0001*h_t + 0.5198*λ_t - 0.5337*λ_{t-1}
        V[t] = float(v1 * h[t] + v2 * lam[t] + v3 * lam[t - 1])

        # 你截图的“新能源方差方程 ln(σ^2)= EGARCH部分 + V_t + x_v*G_{t-1}”
        # 截图里 EGARCH部分对新能源到底用哪个残差/哪个 a_t 不够清晰。
        # 所以这里先用 sigma2_proxy = exp(V_t) 作为“信心区间宽度”的代理。
        sigma2_proxy[t] = float(np.exp(V[t]))

    return {
        "a_resid": a,
        "h_t": h,
        "lambda_t": lam,
        "V_t": V,
        "sigma2_proxy": sigma2_proxy,
        "c_ar1": c,
        "phi_ar1": phi,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prediction-csv", required=True, help="prediction_results.csv 路径（包含 GRU_Pred_Return）")
    ap.add_argument("--new-energy-csv", default=None, help="可选：新能源历史收益（Date, r_new, 可选 M/G 列）")
    ap.add_argument("--date-col-oil", default="Date_target", help="油价预测日期列名（默认 Date_target）")

    ap.add_argument("--new-date-col", default="Date", help="新能源数据日期列名（默认 Date）")
    ap.add_argument("--new-return-col", default="r_new", help="新能源收益列名（默认 r_new）")

    ap.add_argument("--conf-level", type=float, default=0.95, help="置信水平：0.90/0.95/0.99")
    ap.add_argument("--oil-return-col", default="GRU_Pred_Return", help="油价收益列名（默认 GRU_Pred_Return）")
    ap.add_argument("--scale-oil-return", type=float, default=100.0,
                    help="把油收益乘以 100，匹配截图 R_oil,t = 100*ln(P_t/P_{t-1}) 的量纲口径。")
    ap.add_argument("--output-csv", default="new_energy_forecast_with_confidence.csv", help="输出文件路径")

    args = ap.parse_args()

    oil = pd.read_csv(args.prediction_csv)
    oil[args.date_col_oil] = pd.to_datetime(oil[args.date_col_oil])
    oil = oil.sort_values(args.date_col_oil)

    if args.oil_return_col not in oil.columns:
        raise ValueError(f"prediction-csv 缺少列 {args.oil_return_col}")

    z = oil[args.oil_return_col].astype(float).values * float(args.scale_oil_return)

    # 截图里 EGARCH-ARJI 参数（你需要确认最终数值是否一致；这里用截图可读值做默认）
    params = {
        "omega": -0.0023,
        "alpha": 0.0738,
        "beta": 0.9893,
        "k": -0.0585,
        "lambda0": 0.0238,
        "rho": 0.9266,
        "gamma": 0.3063,
        "v1": 0.0001,
        "v2": 0.5198,
        "v3": -0.5337,
    }

    var_dict = egarch_arji_variance_from_oil_return(z, params=params, xi_mode="abs_std_resid")
    sigma2 = var_dict["sigma2_proxy"]
    sigma = np.sqrt(np.maximum(sigma2, 1e-18))

    # 置信区间：正态近似
    # conf_level: 0.95 -> z=1.96, 0.90 -> 1.645, 0.99 -> 2.576
    # 这里简单用常见值映射；你也可以换成 scipy.stats 的精确分位数。
    conf_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    if args.conf_level not in conf_map:
        raise ValueError("目前只支持 0.90/0.95/0.99 置信水平；你可告诉我想要的分位数，我再改。")
    z_alpha = conf_map[args.conf_level]

    dates = oil[args.date_col_oil].dt.strftime("%Y-%m-%d").values
    # 如果没有新能源历史数据，就只能给出“以 0 为均值的置信区间宽度代理”
    if args.new_energy_csv is None:
        mean_pred = np.zeros_like(sigma)
    else:
        ne = pd.read_csv(args.new_energy_csv)
        ne[args.new_date_col] = pd.to_datetime(ne[args.new_date_col])
        ne = ne.sort_values(args.new_date_col)

        if args.new_return_col not in ne.columns:
            raise ValueError(f"new-energy-csv 缺少列 {args.new_return_col}")

        # 控制变量：如果没有就用默认
        M_col = "M" if "M" in ne.columns else None
        G_col = "G" if "G" in ne.columns else None

        ne["M_use"] = ne[M_col] if M_col else 0.0
        ne["G_use"] = ne[G_col] if G_col else 1.0

        # 为了“能跑”，均值模型用一个简单回归来近似截图里的均值方程结构：
        # r_new,t ≈ b0 + b1*r_new,t-1 + b2*z_{t-1} + b3*M_t + b4*lambda_t*G_t
        # 其中 z_{t-1} / lambda_t 来自油价预测序列的同日期对齐（这里只演示）。
        # 如果你要严格复刻截图均值方程，需要把截图里 r_new 的 phi/theta 参数也接入。
        ne = ne.copy()
        ne["r_new_lag"] = ne[args.new_return_col].shift(1)
        ne["z_oil_aligned"] = np.nan
        ne["lam_aligned"] = np.nan

        # 把 z 与 lambda 对齐到新能源日期
        z_map = dict(zip(oil[args.date_col_oil].dt.strftime("%Y-%m-%d"), z))
        lam_map = dict(zip(oil[args.date_col_oil].dt.strftime("%Y-%m-%d"), var_dict["lambda_t"]))

        ne["date_str"] = ne[args.new_date_col].dt.strftime("%Y-%m-%d")
        ne["z_oil_aligned"] = ne["date_str"].map(z_map)
        ne["lam_aligned"] = ne["date_str"].map(lam_map)

        ne["z_lag"] = ne["z_oil_aligned"].shift(1)

        # 构造训练样本（只使用能形成完整特征的行）
        feat = pd.DataFrame({
            "b0": np.ones(len(ne)),
            "r_new_lag": ne["r_new_lag"],
            "z_lag": ne["z_lag"],
            "M": ne["M_use"],
            "lamG": ne["lam_aligned"] * ne["G_use"],
        })
        y = ne[args.new_return_col].values

        mask = np.isfinite(feat["r_new_lag"].values) & np.isfinite(feat["z_lag"].values)
        X = feat.loc[mask, :].values
        y_train = y[mask]

        if len(y_train) < 10:
            raise RuntimeError("新能源历史数据太少，无法估计均值回归系数。")

        # OLS: b = (X'X)^-1 X'y
        b, *_ = np.linalg.lstsq(X, y_train, rcond=None)

        # 对油预测日期做均值预测（用最近一期 r_new_lag）
        # 递推：为了简单，这里用最后一个已知 r_new 来做 one-step（你可再让我改成多步递推）
        last_known = float(ne[args.new_return_col].iloc[-1])
        lam_series = var_dict["lambda_t"]
        z_series = z
        M_series = np.zeros_like(z_series)
        G_series = np.ones_like(z_series)

        # 对齐控制变量：如果新能源文件包含这些未来日期就映射，否则用默认 0/1
        M_map = dict(zip(ne["date_str"], ne["M_use"]))
        G_map = dict(zip(ne["date_str"], ne["G_use"]))

        for i, d in enumerate(dates):
            M_series[i] = float(M_map.get(d, 0.0))
            G_series[i] = float(G_map.get(d, 1.0))

        mean_pred = np.zeros_like(sigma)
        r_new_lag = last_known
        # 简化：z_lag 用油预测序列的前一时点；第一天用上一条的 z（用 z[0] 的前值近似）
        z_lag0 = float(z_series[0])
        z_lag = z_lag0
        for i in range(len(sigma)):
            lamG = float(lam_series[i] * G_series[i])
            # mean: b0 + b1*r_new_lag + b2*z_lag + b3*M + b4*lamG
            mean_pred[i] = (
                b[0]
                + b[1] * r_new_lag
                + b[2] * z_lag
                + b[3] * M_series[i]
                + b[4] * lamG
            )
            # 递推更新
            r_new_lag = mean_pred[i]
            z_lag = float(z_series[i])

    # 输出结果
    out = pd.DataFrame({
        "Date_target": dates,
        "Oil_GRU_z_used": z,               # 用于方差递推的油收益（乘以100）
        "NewEnergy_MeanPred": mean_pred, # 均值预测（若无新能源数据则为0）
        "NewEnergy_Sigma": sigma,
        "CI_low": mean_pred - z_alpha * sigma,
        "CI_high": mean_pred + z_alpha * sigma,
        "ConfLevel": args.conf_level
    })

    # 风险等级：按波动（Sigma）分位数分桶
    sigma_q50 = float(out["NewEnergy_Sigma"].quantile(0.5))
    sigma_q80 = float(out["NewEnergy_Sigma"].quantile(0.8))
    out["RiskLevel"] = np.where(
        out["NewEnergy_Sigma"] >= sigma_q80,
        "HIGH",
        np.where(out["NewEnergy_Sigma"] >= sigma_q50, "MEDIUM", "LOW"),
    )
    out["Lambda_t"] = var_dict["lambda_t"]
    out["V_t"] = var_dict["V_t"]

    out.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"已保存：{args.output_csv}")
    chart_csvs = export_chart_csvs(out, args.output_csv)
    # 回填散点 CSV 的 Lambda 列
    scatter_path = args.output_csv.rsplit(".", 1)[0] + "_chart_lambda_sigma_scatter.csv"
    try:
        scatter_df = pd.read_csv(scatter_path)
        scatter_df["Lambda_t"] = out["Lambda_t"].astype(float).values
        scatter_df.to_csv(scatter_path, index=False, encoding="utf-8-sig")
    except Exception:
        pass
    print("已保存图表CSV：")
    for p in chart_csvs:
        print(f"  - {p}")

    # ========== 可视化输出 ==========
    # 统一使用英文标签，避免不同系统中文字体导致的乱码。
    try:
        out_plot = out.copy()
        out_plot["Date_target"] = pd.to_datetime(out_plot["Date_target"], errors="coerce")
        out_plot = out_plot.dropna(subset=["Date_target"]).sort_values("Date_target")

        out_path = args.output_csv
        stem = out_path.rsplit(".", 1)[0]

        # 1) Mean prediction + confidence interval
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(out_plot["Date_target"], out_plot["NewEnergy_MeanPred"], label="MeanPred", linewidth=1.4)
        ax.fill_between(
            out_plot["Date_target"],
            out_plot["CI_low"],
            out_plot["CI_high"],
            alpha=0.25,
            label=f"{int(args.conf_level * 100)}% CI",
        )
        ax.set_title("New Energy Mean Prediction with Confidence Band")
        ax.set_xlabel("Date")
        ax.set_ylabel("Return")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(f"{stem}_plot_ci.png", dpi=150)
        plt.close(fig)

        # 2) Volatility proxy + risk thresholds
        q50 = float(out_plot["NewEnergy_Sigma"].quantile(0.5))
        q80 = float(out_plot["NewEnergy_Sigma"].quantile(0.8))
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(out_plot["Date_target"], out_plot["NewEnergy_Sigma"], label="Sigma", color="#1f77b4", linewidth=1.3)
        ax.axhline(q50, color="#ff7f0e", linestyle="--", linewidth=1.0, label="Q50")
        ax.axhline(q80, color="#d62728", linestyle="--", linewidth=1.0, label="Q80")
        ax.set_title("Volatility Proxy (Sigma) and Risk Thresholds")
        ax.set_xlabel("Date")
        ax.set_ylabel("Sigma")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(f"{stem}_plot_sigma.png", dpi=150)
        plt.close(fig)

        # 3) Risk level distribution
        risk_order = ["LOW", "MEDIUM", "HIGH"]
        risk_counts = out_plot["RiskLevel"].value_counts().reindex(risk_order, fill_value=0)
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(risk_counts.index, risk_counts.values, color=["#2ca02c", "#ffbf00", "#d62728"])
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

    # ========== 终端分析报告（新手可读版） ==========
    try:
        risk_counts = out["RiskLevel"].value_counts(dropna=False).to_dict()
        ci_width = (out["CI_high"] - out["CI_low"]).values.astype(float)

        quantiles = out["NewEnergy_Sigma"].quantile([0.1, 0.5, 0.9]).to_dict()
        top_rows = (
            out.loc[out["NewEnergy_Sigma"].sort_values(ascending=False).head(5).index,
                    ["Date_target", "NewEnergy_Sigma", "RiskLevel"]]
            .copy()
        )
        top_rows["NewEnergy_Sigma"] = top_rows["NewEnergy_Sigma"].astype(float)

        print("\n" + "=" * 60)
        print("新能源风险与置信区间分析报告（基于油价 GRU 预测递推）")
        print("=" * 60)
        print(f"样本数：{len(out)}")
        print(f"置信水平：{args.conf_level:.2f}（对应 z_alpha={z_alpha:.3f}）")
        print(f"RiskLevel 统计：{risk_counts}")
        print("NewEnergy_Sigma 分位数：")
        for q, v in quantiles.items():
            print(f"  {q:.1f}分位：{float(v):.6f}")
        print(f"CI 宽度（CI_high-CI_low）均值：{float(np.mean(ci_width)):.6f}")
        print(f"CI 宽度（最大值）：{float(np.max(ci_width)):.6f}")
        print("Top-5 高波动日期（按 Sigma）：")
        print(top_rows.to_string(index=False))

        if args.new_energy_csv is None:
            print("\n提示：未提供新能源历史数据，因此 MeanPred=0，只输出波动/置信区间宽度的风险强度。")
        else:
            print("\n提示：已提供新能源历史数据，MeanPred 来自截图均值方程的简化回归近似（AR+外生控制）。")
    except Exception as e:
        print(f"[警告] 生成终端分析报告失败：{e}")


if __name__ == "__main__":
    main()