"""
WTI 收益单步预测脚本（固定默认流程）
====================================

当前脚本不走命令行参数，直接用代码里的默认配置执行。

固定流程：
1) 读取 `Date` / `ClosePrice`
2) 价格序列转收益率（`simple` 或 `log`）
3) 对收益标签做 VMD，并按主频删除最高频 IMF 后重构
4) 用 `StandardScaler`（仅训练段 fit）标准化标签
5) 构造单点监督样本：`X=过去 time_steps`，`y=下一天（horizon=1）`
6) 训练 RNN（默认双向 LSTM）并评估 `MAE/RMSE/R²/方向一致性`
7) 可选输出：下一天预测、预测对比图、loss 曲线、VMD 分解图
"""

from __future__ import annotations

import os
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    r2_score,
    roc_auc_score,
)
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.ensemble import RandomForestRegressor

try:
    from tensorflow.keras.layers import GRU, LSTM, Bidirectional, Dense, Dropout, Input
    from tensorflow.keras.models import Model
    from tensorflow.keras.losses import Huber
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.metrics import BinaryAccuracy
    from tensorflow.keras.callbacks import EarlyStopping
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "需要安装 TensorFlow 2：pip install tensorflow\n"
        f"导入失败: {e}"
    ) from e


DEFAULT_OILDATA_DIR = (
    r"C:\Users\12725\Desktop\大宗绿测_基于油价因子的绿色金融产品预测与风险分析 - 副本"
    r"\技术文档\源代码\web_runs\run_20260413_144847_top10\_data\OilData"
)
DEFAULT_CSV = os.path.join(DEFAULT_OILDATA_DIR, "raw_data", "WTI_futuresprice.csv")


def get_train_length(
    dataset_len: int, batch_size: int, test_percent: float, *, verbose: bool = True
) -> int:
    """
    训练长度截断策略。

    目的：
    - 先按 test_percent 粗分训练区间
    - 再在该区间末尾附近找一个能被 batch_size 整除的长度
      （便于 stateful/固定 batch 训练时不丢尾批）
    """
    length = int(dataset_len * (1 - test_percent))
    train_length_values = []
    for x in range(int(length) - 100, int(length)):
        if x % batch_size == 0:
            train_length_values.append(x)
            if verbose:
                print(x)
    if not train_length_values:
        raise ValueError(
            "get_train_length 未找到合法长度；请减小 batch_size 或调整 test_percent。"
        )
    return max(train_length_values)


def load_price_frame(
    csv_path: str,
    *,
    price_col: str = "ClosePrice",
    date_col: str = "Date",
) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if price_col not in df.columns:
        alias_price = {
            "ClosePrice": ["收盘", "close", "Close", "CLOSE", "close_price"],
            "收盘": ["ClosePrice", "close", "Close", "CLOSE"],
        }
        cand = alias_price.get(price_col, [])
        hit = next((c for c in cand if c in df.columns), None)
        if hit is not None:
            print(f"[列名兼容] price_col={price_col!r} 未找到，自动改用 {hit!r}")
            df = df.rename(columns={hit: price_col})
        else:
            raise ValueError(f"列 {price_col!r} 不存在，实际列：{list(df.columns)}")
    if date_col not in df.columns:
        alias_date = {
            "Date": ["日期", "date", "DATE"],
            "日期": ["Date", "date", "DATE"],
        }
        cand = alias_date.get(date_col, [])
        hit = next((c for c in cand if c in df.columns), None)
        if hit is not None:
            print(f"[列名兼容] date_col={date_col!r} 未找到，自动改用 {hit!r}")
            df = df.rename(columns={hit: date_col})
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.loc[df[price_col].notna()].reset_index(drop=True)
    # Date 列可能有空；不强制丢弃，后面打印时会处理
    return df


def load_price_series(csv_path: str, price_col: str = "ClosePrice") -> np.ndarray:
    df = load_price_frame(csv_path, price_col=price_col)
    return df[[price_col]].values.astype(np.float64)


def _load_financial_csv_like_main0309(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    date_col = df.columns[0]
    df = df[df[date_col].astype(str).str.strip().str.lower() != "date"].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.rename(columns={date_col: "Date"}).set_index("Date").sort_index()
    return df


def _geo_sign_from_text(text: object) -> int:
    s = str(text).strip().lower()
    if not s or s == "nan":
        return 0
    pos_keywords = [
        # 中文：偏利多油价（供给收缩/地缘风险上升）
        "减产", "减供", "限产", "禁运", "制裁升级", "冲突", "战争", "危机",
        "袭击", "中断", "航运受阻", "封锁", "油田受损", "供应紧张", "紧张局势",
        "地缘风险", "红海危机", "霍尔木兹", "胡塞", "俄乌冲突", "飓风", "风暴",
        "opec+减产", "延长减产", "减产协议",
        # 英文
        "supply disruption", "sanction", "sanctions tighten", "geopolitical risk",
        "conflict", "war", "outage", "shipping disruption", "strait risk",
        "opec cut", "opec+ cut", "production cut", "supply tightness", "embargo",
    ]
    neg_keywords = [
        # 中文：偏利空油价（供给恢复/需求走弱）
        "增产", "恢复供应", "复产", "制裁放松", "停火", "和谈", "缓和",
        "释放战略石油储备", "抛储", "需求下滑", "需求疲软", "衰退", "库存增加",
        "opec+增产", "逐步增产",
        # 英文
        "supply recovery", "supply resume", "ceasefire", "peace talk", "de-escalation",
        "sanction relief", "production increase", "opec+ hike", "output increase",
        "spr release", "strategic reserve release", "demand slowdown", "recession",
    ]
    pos = sum(1 for k in pos_keywords if k in s)
    neg = sum(1 for k in neg_keywords if k in s)
    if pos > neg:
        return 1
    if neg > pos:
        return -1
    return 0


def build_geo_rigorous_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    严格因果地缘特征：所有特征均基于 t-1 及之前信息（通过 shift(1) 实现）。
    需要列：GeoEvent（0/1）、GeoEvent_Count、GeoEvent_Impact、GeoEvent_SignedImpact。
    """
    out = pd.DataFrame(index=df.index)
    if "GeoEvent" not in df.columns:
        return out
    ev = pd.to_numeric(df.get("GeoEvent", 0), errors="coerce").fillna(0.0)
    cnt = pd.to_numeric(df.get("GeoEvent_Count", 0), errors="coerce").fillna(0.0)
    imp = pd.to_numeric(df.get("GeoEvent_Impact", 0), errors="coerce").fillna(0.0)
    simp = pd.to_numeric(df.get("GeoEvent_SignedImpact", 0), errors="coerce").fillna(0.0)

    ev_l1 = ev.shift(1).fillna(0.0)
    cnt_l1 = cnt.shift(1).fillna(0.0)
    imp_l1 = imp.shift(1).fillna(0.0)
    simp_l1 = simp.shift(1).fillna(0.0)

    out["GeoEvent_OnDate_l1"] = ev_l1
    out["GeoEvent_Count_l1"] = cnt_l1
    out["GeoEvent_Impact_l1"] = imp_l1
    out["GeoEvent_SignedImpact_l1"] = simp_l1
    out["GeoEvent_PosImpact_l1"] = np.clip(simp_l1, 0.0, None)
    out["GeoEvent_NegImpact_l1"] = np.clip(-simp_l1, 0.0, None)

    for w in (5, 10, 20):
        out[f"GeoEvent_NetImpact_{w}d"] = simp_l1.rolling(w, min_periods=1).sum()
        out[f"GeoEvent_AbsImpact_{w}d"] = np.abs(simp_l1).rolling(w, min_periods=1).sum()
        out[f"GeoEvent_PosCount_{w}d"] = (simp_l1 > 0).astype(float).rolling(w, min_periods=1).sum()
        out[f"GeoEvent_NegCount_{w}d"] = (simp_l1 < 0).astype(float).rolling(w, min_periods=1).sum()

    # 指数衰减累计冲击（半衰期约 5 天）
    alpha = 1.0 - np.exp(-np.log(2) / 5.0)
    out["GeoEvent_DecayImpact"] = simp_l1.ewm(alpha=alpha, adjust=False).mean()
    out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def load_multisource_data_like_main0309(base_dir: str) -> pd.DataFrame:
    """
    按 oil_price_prediction_main_0309.py 风格加载多源数据，并返回包含 Date/ClosePrice 的总表。
    """
    raw_data_path = os.path.join(base_dir, "raw_data")
    energy_data_path = os.path.join(base_dir, "能源基本面与下游产业")

    # 1) WTI 主价格
    wti_futures = pd.read_csv(os.path.join(raw_data_path, "WTI_futuresprice.csv"))
    if "Date" not in wti_futures.columns:
        raise ValueError("WTI_futuresprice.csv 缺少 Date 列")
    wti_futures["Date"] = pd.to_datetime(wti_futures["Date"], errors="coerce")
    wti_futures = wti_futures.dropna(subset=["Date"])
    if "ClosePrice" not in wti_futures.columns:
        raise ValueError("WTI_futuresprice.csv 缺少 ClosePrice 列")
    wti_futures = wti_futures.rename(columns={"ClosePrice": "WTI_Futures"})
    keep_cols = [c for c in ["Date", "WTI_Futures", "OpenPrice", "HighPrice", "LowPrice", "Volume"] if c in wti_futures.columns]
    combined = wti_futures[keep_cols].set_index("Date").sort_index()

    # 尝试载入现货并计算基差
    spot_path = os.path.join(raw_data_path, "WTI_spotprice.xls")
    if os.path.isfile(spot_path):
        try:
            wti_spot = pd.read_excel(spot_path)
            if len(wti_spot.columns) >= 2:
                wti_spot.iloc[:, 0] = pd.to_datetime(wti_spot.iloc[:, 0], errors="coerce")
                wti_spot = wti_spot.dropna(subset=[wti_spot.columns[0]])
                wti_spot = wti_spot.set_index(wti_spot.columns[0]).sort_index()
                price_col = next((c for c in wti_spot.columns if "price" in str(c).lower() or "close" in str(c).lower()), wti_spot.columns[-1])
                wti_spot = wti_spot[[price_col]].rename(columns={price_col: "WTI_Spot"})
                combined = pd.merge(combined, wti_spot, left_index=True, right_index=True, how="outer")
                if "WTI_Futures" in combined.columns and "WTI_Spot" in combined.columns:
                    combined["Basis"] = combined["WTI_Futures"] - combined["WTI_Spot"]
        except Exception:
            pass

    # 2) 金融因子
    financial_map = {
        "DXY_Index.csv": "DXY",
        "SP500_Index.csv": "SP500",
        "US10Y_Yield.csv": "US10Y",
        "VIX_index.csv": "VIX",
        "OVX_index.csv": "OVX",
    }
    fin_df = None
    for fn, out_name in financial_map.items():
        fp = os.path.join(raw_data_path, fn)
        if not os.path.isfile(fp):
            continue
        try:
            tmp = _load_financial_csv_like_main0309(fp)
            val_col = next((c for c in tmp.columns if "close" in str(c).lower()), tmp.columns[-1])
            one = tmp[[val_col]].rename(columns={val_col: out_name})
            fin_df = one if fin_df is None else pd.merge(fin_df, one, left_index=True, right_index=True, how="outer")
        except Exception:
            continue
    if fin_df is not None:
        combined = pd.merge(combined, fin_df, left_index=True, right_index=True, how="left")

    # 3) 供给侧（周频上采样到日频）
    supply_df = None
    supply_specs = [
        ("一、原油供需情况/美国商业原油库存.csv", "Stocks"),
        ("一、原油供需情况/美国原油产量周度数据.csv", "Production"),
    ]
    for rel, cname in supply_specs:
        fp = os.path.join(energy_data_path, rel)
        if not os.path.isfile(fp):
            continue
        try:
            tmp = pd.read_csv(fp, skiprows=4)
            tmp.columns = ["Date", cname]
            tmp["Date"] = pd.to_datetime(tmp["Date"], errors="coerce")
            tmp = tmp.dropna(subset=["Date"]).set_index("Date").sort_index()
            supply_df = tmp if supply_df is None else pd.merge(supply_df, tmp, left_index=True, right_index=True, how="outer")
        except Exception:
            continue

    rigs_path = os.path.join(energy_data_path, "一、原油供需情况", "活跃钻井机数量.xlsx")
    if os.path.isfile(rigs_path):
        try:
            rigs = pd.read_excel(rigs_path)
            date_col = "Date" if "Date" in rigs.columns else ("日期" if "日期" in rigs.columns else None)
            if date_col is None:
                for c in ["Last Count", "Date of Prior Count", "Date"]:
                    if c in rigs.columns:
                        date_col = c
                        break
            if date_col is None:
                for c in rigs.columns:
                    s = pd.to_datetime(rigs[c], errors="coerce")
                    if s.notna().sum() > len(rigs) // 2:
                        date_col = c
                        break
            if date_col is None:
                date_col = rigs.columns[0]
            rigs[date_col] = pd.to_datetime(rigs[date_col], errors="coerce")
            rigs = rigs.dropna(subset=[date_col])
            num_cols = rigs.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                val_col = "Count" if "Count" in num_cols else num_cols[0]
                agg = rigs.groupby(rigs[date_col].dt.normalize())[val_col].sum().sort_index()
                rigs_df = agg.to_frame(name="Rigs")
                supply_df = rigs_df if supply_df is None else pd.merge(supply_df, rigs_df, left_index=True, right_index=True, how="outer")
        except Exception:
            pass
    if supply_df is not None:
        combined = pd.merge(combined, supply_df.resample("D").ffill(), left_index=True, right_index=True, how="left")

    # 4) 情绪（月频上采样）
    try:
        oil_fp = os.path.join(raw_data_path, "情绪指标", "oil price.csv")
        gas_fp = os.path.join(raw_data_path, "情绪指标", "gas price.csv")
        if os.path.isfile(oil_fp) and os.path.isfile(gas_fp):
            oil_trends = pd.read_csv(oil_fp, skiprows=2)
            if "月份" in oil_trends.columns:
                oil_trends["Date"] = pd.to_datetime(oil_trends["月份"].astype(str) + "-01", errors="coerce")
            else:
                oil_trends["Date"] = pd.to_datetime(oil_trends.iloc[:, 0].astype(str) + "-01", errors="coerce")
            oil_col = oil_trends.columns[-1]
            oil_trends = oil_trends.set_index("Date")[[oil_col]].rename(columns={oil_col: "Oil_Trends"})

            gas_trends = pd.read_csv(gas_fp, skiprows=2)
            if "月份" in gas_trends.columns:
                gas_trends["Date"] = pd.to_datetime(gas_trends["月份"].astype(str) + "-01", errors="coerce")
            else:
                gas_trends["Date"] = pd.to_datetime(gas_trends.iloc[:, 0].astype(str) + "-01", errors="coerce")
            gas_col = gas_trends.columns[-1]
            gas_trends = gas_trends.set_index("Date")[[gas_col]].rename(columns={gas_col: "Gas_Trends"})
            sentiment = pd.merge(oil_trends, gas_trends, left_index=True, right_index=True, how="outer")
            combined = pd.merge(combined, sentiment.resample("D").ffill(), left_index=True, right_index=True, how="left")
    except Exception:
        pass

    # 5) 地缘事件（更严谨：支持影响强度、同日多事件计数、非交易日映射）
    geo_fp = os.path.join(energy_data_path, "三、地缘大事记.xlsx")
    if os.path.isfile(geo_fp):
        try:
            raw_geo = pd.read_excel(geo_fp, sheet_name=0)
            date_col = next((c for c in raw_geo.columns if str(c).strip() == "开始日期"), raw_geo.columns[0])
            raw_geo[date_col] = pd.to_datetime(raw_geo[date_col], errors="coerce")
            raw_geo = raw_geo.dropna(subset=[date_col])
            raw_geo["EventDate"] = raw_geo[date_col].dt.normalize()

            # 严格规则：
            # 1) 影响强度只来自“显式结构化分值列”（不从备注文本中抽数字）
            # 2) 备注文本仅用于方向关键词判定，不用于强度
            note_col = next((c for c in raw_geo.columns if str(c).strip() == "关键影响/备注"), None)
            name_col = next((c for c in raw_geo.columns if str(c).strip() == "事件名称"), None)
            score_candidates = ["影响分值", "ImpactScore", "GeoImpactScore", "Impact_Score"]
            sign_candidates = ["方向", "Sign", "ImpactSign", "GeoSign"]
            score_col = next((c for c in raw_geo.columns if str(c).strip() in score_candidates), None)
            sign_col = next((c for c in raw_geo.columns if str(c).strip() in sign_candidates), None)

            if score_col is not None:
                score = pd.to_numeric(raw_geo[score_col], errors="coerce")
                # 无效分值回退为 1，保证事件强度存在但不夸大
                raw_geo["GeoEvent_Impact"] = score.abs().fillna(1.0)
            else:
                raw_geo["GeoEvent_Impact"] = 1.0

            sgn_from_struct = pd.Series(0.0, index=raw_geo.index)
            if sign_col is not None:
                v = raw_geo[sign_col]
                if pd.api.types.is_numeric_dtype(v):
                    sgn_from_struct = np.sign(pd.to_numeric(v, errors="coerce").fillna(0.0))
                else:
                    s = v.astype(str).str.strip().str.lower()
                    pos_set = {"1", "+1", "+", "pos", "positive", "bull", "up", "利多"}
                    neg_set = {"-1", "-", "neg", "negative", "bear", "down", "利空"}
                    sgn_from_struct = np.where(s.isin(pos_set), 1.0, np.where(s.isin(neg_set), -1.0, 0.0))
                    sgn_from_struct = pd.Series(sgn_from_struct, index=raw_geo.index, dtype=float)

            text_source = pd.Series("", index=raw_geo.index, dtype=object)
            if note_col is not None:
                text_source = text_source.astype(str) + " " + raw_geo[note_col].astype(str)
            if name_col is not None:
                text_source = text_source.astype(str) + " " + raw_geo[name_col].astype(str)
            sgn_from_text = text_source.map(_geo_sign_from_text).astype(float)

            raw_geo["GeoEvent_Sign"] = np.where(sgn_from_struct != 0, sgn_from_struct, sgn_from_text)
            raw_geo["GeoEvent_SignedImpact"] = raw_geo["GeoEvent_Sign"] * raw_geo["GeoEvent_Impact"]

            # 按事件日聚合：同日事件数 + 最大影响 + 净方向冲击
            geo_agg = (
                raw_geo.groupby("EventDate")
                .agg(
                    GeoEvent_Count=("EventDate", "size"),
                    GeoEvent_Impact=("GeoEvent_Impact", "max"),
                    GeoEvent_SignedImpact=("GeoEvent_SignedImpact", "sum"),
                )
                .sort_index()
            )
            if len(geo_agg) > 0:
                # 将非交易日事件映射到“下一个可用交易日”，避免周末事件丢失
                trade_idx = pd.DatetimeIndex(combined.index).sort_values().unique()
                mapped_dates = trade_idx.searchsorted(geo_agg.index, side="left")
                valid = mapped_dates < len(trade_idx)
                if np.any(valid):
                    mapped = pd.DataFrame(
                        {
                            "MappedDate": trade_idx[mapped_dates[valid]],
                            "GeoEvent_Count": geo_agg["GeoEvent_Count"].values[valid],
                            "GeoEvent_Impact": geo_agg["GeoEvent_Impact"].values[valid],
                            "GeoEvent_SignedImpact": geo_agg["GeoEvent_SignedImpact"].values[valid],
                        }
                    )
                    geo_mapped = mapped.groupby("MappedDate", as_index=True).agg(
                        GeoEvent_Count=("GeoEvent_Count", "sum"),
                        GeoEvent_Impact=("GeoEvent_Impact", "max"),
                        GeoEvent_SignedImpact=("GeoEvent_SignedImpact", "sum"),
                    )
                    geo_mapped["GeoEvent"] = (geo_mapped["GeoEvent_Count"] > 0).astype(int)
                    combined = pd.merge(combined, geo_mapped, left_index=True, right_index=True, how="left")
                    combined["GeoEvent"] = combined["GeoEvent"].fillna(0).astype(int)
                    combined["GeoEvent_Count"] = combined["GeoEvent_Count"].fillna(0).astype(float)
                    combined["GeoEvent_Impact"] = combined["GeoEvent_Impact"].fillna(0).astype(float)
                    combined["GeoEvent_SignedImpact"] = combined["GeoEvent_SignedImpact"].fillna(0).astype(float)
                    print(
                        "  已加载地缘事件："
                        f"事件日={int((combined['GeoEvent'] > 0).sum())}, "
                        f"净冲击和={float(combined['GeoEvent_SignedImpact'].sum()):.3f}"
                    )
        except Exception:
            pass

    combined = combined.sort_index()
    # 多源 outer merge 后可能引入重复日期（多对多连接），会把收益压成大量 0。
    # 严格按交易日保留一行，避免重复日期污染时序样本。
    if combined.index.has_duplicates:
        dup_cnt = int(combined.index.duplicated(keep="last").sum())
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        print(f"[数据清理] 检测到重复日期，已去重 {dup_cnt} 行。")
    if "WTI_Futures" not in combined.columns:
        raise ValueError("多源加载失败：缺少 WTI_Futures 列")
    combined["ClosePrice"] = pd.to_numeric(combined["WTI_Futures"], errors="coerce")
    # 关键：多源 outer merge 后会出现非交易日/缺失主价行，必须先剔除
    # 否则收益序列可能退化（NaN/近常数），导致 RF 重要性接近 0。
    combined = combined.loc[combined["ClosePrice"].notna()].copy()
    combined = combined.reset_index().rename(columns={"index": "Date"})
    return combined


def price_to_return_series(
    prices: np.ndarray,
    *,
    return_type: str,
) -> np.ndarray:
    """
    prices: shape (n, 1) 的价格序列
    return: shape (n-1, 1) 的收益序列
    - simple: r_t = p_t/p_{t-1} - 1
    - log:    r_t = log(p_t/p_{t-1})
    """
    prices = np.asarray(prices, dtype=np.float64).reshape(-1)
    if len(prices) < 2:
        raise ValueError("价格序列太短，无法计算收益")
    if np.any(prices <= 0) and return_type == "log":
        raise ValueError("log return 需要价格为正")

    return_type = return_type.lower().strip()
    if return_type == "simple":
        r = prices[1:] / prices[:-1] - 1.0
    elif return_type == "log":
        r = np.log(prices[1:] / prices[:-1])
    else:
        raise ValueError("return_type 必须是 simple 或 log")
    return r.reshape(-1, 1)


def price_to_forward_return_series(
    prices: np.ndarray,
    *,
    return_type: str,
    horizon: int,
) -> np.ndarray:
    """
    以前一日价格 P_t 为基准的 forward return（预测未来 horizon 天累计收益）：
    - simple: P_{t+h}/P_t - 1
    - log:    log(P_{t+h}/P_t)
    返回 shape (n-horizon, 1)，对应 t=0..n-h-1
    """
    h = int(horizon)
    if h <= 0:
        raise ValueError("horizon 必须 > 0")
    p = np.asarray(prices, dtype=np.float64).reshape(-1)
    if len(p) <= h:
        raise ValueError("价格序列太短，无法计算 forward return")
    if return_type.lower().strip() == "log" and np.any(p <= 0):
        raise ValueError("log return 需要价格为正")
    p0 = p[:-h]
    p1 = p[h:]
    if return_type.lower().strip() == "log":
        r = np.log(p1 / p0)
    else:
        r = p1 / p0 - 1.0
    return r.reshape(-1, 1)


def compress_returns(
    r: np.ndarray,
    *,
    method: str,
    scale: float,
) -> np.ndarray:
    """收益压缩入口（当前固定 none，原样返回）。"""
    r = np.asarray(r, dtype=np.float64)
    method = method.lower().strip()
    if method != "none":
        raise ValueError("当前版本仅支持 return-compress=none")
    return r


def decompress_returns(
    r_c: np.ndarray,
    *,
    method: str,
    scale: float,
) -> np.ndarray:
    """收益解压入口（当前固定 none，原样返回）。"""
    r_c = np.asarray(r_c, dtype=np.float64)
    method = method.lower().strip()
    if method != "none":
        raise ValueError("当前版本仅支持 return-compress=none")
    return r_c


def vmd_decompose_signal(
    series: np.ndarray,
    *,
    k: int,
    alpha: float,
    tau: float,
    dc: int,
    init: int,
    tol: float,
) -> np.ndarray:
    """对一维序列做 VMD，返回 shape=(k, n) 的 IMF。"""
    try:
        from vmdpy import VMD
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "需要安装 vmdpy：pip install vmdpy\n"
            f"导入失败: {e}"
        ) from e

    x = np.asarray(series, dtype=np.float64).reshape(-1)
    u, _, _ = VMD(x, alpha, tau, k, dc, init, tol)
    return u


def apply_vmd_on_target(
    target_series: np.ndarray,
    *,
    k: int,
    alpha: float,
    tau: float,
    dc: int,
    init: int,
    tol: float,
    drop_high_freq: int,
    drop_mode: str = "freq",
    debug_print: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """
    对标签序列做 VMD 并重构训练标签。

    参数语义：
    - drop_high_freq: 需要删除的 IMF 数量 N
    - drop_mode:
      - index: 直接按 IMF 原始索引删前 N 个（仅做对照，不推荐）
      - freq: 先按主频评估高低，再删最高频 N 个（推荐）

    返回：
    - reconstructed_target: 删除指定 IMF 后重构出的单一标签序列
    - imfs: 原始 IMF 矩阵，shape=(K, T)
    """
    x = np.asarray(target_series, dtype=np.float64).reshape(-1)
    imfs = vmd_decompose_signal(
        x, k=k, alpha=alpha, tau=tau, dc=dc, init=init, tol=tol
    )
    drop_n = int(max(0, drop_high_freq))
    if drop_n >= imfs.shape[0]:
        raise ValueError("vmd-drop-high-freq 不能 >= vmd-k")

    # 频率打分：FFT 主峰归一化频率，越大越高频
    peak_freqs = []
    for idx in range(imfs.shape[0]):
        spec = np.abs(np.fft.rfft(imfs[idx]))
        peak_bin = int(np.argmax(spec[1:]) + 1) if len(spec) > 1 else 0
        peak_freqs.append(peak_bin / max(1, imfs.shape[1]))
    peak_freqs = np.asarray(peak_freqs, dtype=np.float64)

    drop_mode = drop_mode.lower().strip()
    if drop_mode not in ("index", "freq"):
        raise ValueError("vmd-drop-mode 必须是 index 或 freq")

    if drop_mode == "index":
        kept_idx = np.arange(drop_n, imfs.shape[0])
        dropped_idx = np.arange(0, drop_n)
    else:
        # 真正删高频：按主频从高到低排序后删前 drop_n 个
        order_high2low = np.argsort(-peak_freqs)
        dropped_idx = order_high2low[:drop_n]
        kept_mask = np.ones(imfs.shape[0], dtype=bool)
        kept_mask[dropped_idx] = False
        kept_idx = np.where(kept_mask)[0]

    reconstructed = np.sum(imfs[kept_idx], axis=0)

    # 某些实现/参数下 VMD 输出长度可能与原序列有 1 个点偏差，统一对齐到最短长度
    target_len = min(len(x), imfs.shape[1], len(reconstructed))
    imfs = imfs[:, :target_len]
    reconstructed = reconstructed[:target_len]

    if debug_print:
        # 调试信息：用于人工核验 IMF 频率排序是否符合预期
        print("VMD IMF 调试统计（用于检查是否删错分量）:")
        print("idx\tstd\tenergy\tzcr\tpeak_freq_norm")
        for idx in range(imfs.shape[0]):
            imf = imfs[idx]
            std = float(np.std(imf))
            energy = float(np.mean(imf**2))
            zcr = float(np.mean(np.sign(imf[1:]) != np.sign(imf[:-1])))
            peak_freq_norm = float(peak_freqs[idx])
            print(f"{idx + 1}\t{std:.6f}\t{energy:.6e}\t{zcr:.4f}\t{peak_freq_norm:.6f}")

        dropped = (dropped_idx + 1).tolist()
        kept = (kept_idx + 1).tolist()
        print(f"VMD 删除规则（drop_mode={drop_mode}）: 丢弃 IMF 索引 {dropped}，保留 {kept}")
    return reconstructed.reshape(-1, 1), imfs


def apply_vmd_train_prefix_only(
    target_series: np.ndarray,
    *,
    prefix_end_exclusive: int,
    k: int,
    alpha: float,
    tau: float,
    dc: int,
    init: int,
    tol: float,
    drop_high_freq: int,
    drop_mode: str = "freq",
    debug_print: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """
    仅对前缀 [0, prefix_end_exclusive) 做 VMD，其后索引保持原始收益不变。

    原因：对整条序列做 VMD 时，分解在数学上会用到全序列信息，等价于把
    “未来测试段”混进训练标签的重构里，评估指标会严重虚高（R² 贴 1）。
    horizon=1 且训练窗终点为 length-2 时，应取 prefix_end_exclusive = length - 1，
    使第一个测试标签点及之后不参与 VMD。
    """
    full = np.asarray(target_series, dtype=np.float64).reshape(-1)
    n = len(full)
    cut = int(prefix_end_exclusive)
    if cut <= 0:
        raise ValueError("apply_vmd_train_prefix_only: prefix_end_exclusive 必须 > 0")
    if cut > n:
        cut = n
    prefix = full[:cut]
    recon, imfs = apply_vmd_on_target(
        prefix.reshape(-1, 1),
        k=k,
        alpha=alpha,
        tau=tau,
        dc=dc,
        init=init,
        tol=tol,
        drop_high_freq=drop_high_freq,
        drop_mode=drop_mode,
        debug_print=debug_print,
    )
    recon = recon.reshape(-1)
    if len(recon) < cut:
        recon = np.concatenate([recon, prefix[len(recon) : cut]])
    elif len(recon) > cut:
        recon = recon[:cut]
    out = np.concatenate([recon, full[cut:]]).reshape(-1, 1)
    return out, imfs


def build_windows(
    scaled: np.ndarray,
    raw_len: int,
    time_steps: int,
    length: int,
    max_test_window: int,
    *,
    use_window_vmd: bool = False,
    vmd_k: int = 6,
    vmd_alpha: float = 2000.0,
    vmd_tau: float = 0.0,
    vmd_dc: int = 0,
    vmd_init: int = 1,
    vmd_tol: float = 1e-7,
    vmd_drop_high_freq: int = 1,
    vmd_drop_mode: str = "freq",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    单点预测（horizon=1）：
    对每个窗终点 i（scaled 的下标，time_steps <= i <= raw_len-2）：
      X = scaled[i-time_steps : i]            -> 对应历史 time_steps 个点
      y = scaled[i]                           -> 预测下一点（相对窗末端的“下一天”）
    其中 scaled[i] 在原序列上就是窗末端那个点的“下一天”。
    """
    xtrain, ytrain, xtest, ytest = [], [], [], []
    # 记录测试样本对应的目标下标 k（在标签序列中的位置）；
    # 后续用于收益->价格还原与方向一致性计算对齐。
    test_k = []
    for i in range(time_steps, raw_len - 1):
        window_x = scaled[i - time_steps : i]  # 历史
        if use_window_vmd:
            # 严格因果：每个样本仅用该窗口历史做一次 VMD，再用重构序列当输入特征
            window_x, _ = apply_vmd_on_target(
                window_x,
                k=vmd_k,
                alpha=vmd_alpha,
                tau=vmd_tau,
                dc=vmd_dc,
                init=vmd_init,
                tol=vmd_tol,
                drop_high_freq=vmd_drop_high_freq,
                drop_mode=vmd_drop_mode,
                debug_print=False,
            )
        target_y = scaled[i]  # 下一点（horizon=1）
        if i < length - 1:
            xtrain.append(window_x)
            ytrain.append(target_y)
        else:
            xtest.append(window_x)
            ytest.append(target_y)
            test_k.append(i)

    xtrain = np.asarray(xtrain, dtype=np.float64)
    ytrain = np.asarray(ytrain, dtype=np.float64).reshape(-1, 1)
    xtest = np.asarray(xtest, dtype=np.float64)
    ytest = np.asarray(ytest, dtype=np.float64).reshape(-1, 1)
    test_k = np.asarray(test_k, dtype=np.int64)

    # 测试集最多保留 max_test_window 条，并对齐 batch
    if len(xtest) > max_test_window:
        xtest = xtest[:max_test_window]
        ytest = ytest[:max_test_window]
        test_k = test_k[:max_test_window]

    return xtrain, ytrain, xtest, ytest, test_k


def build_windows_from_features(
    features_scaled: np.ndarray,
    target_scaled: np.ndarray,
    *,
    time_steps: int,
    length: int,
    max_test_window: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    多特征版本滑窗：
    - X = features_scaled[i-time_steps:i, :]
    - y = target_scaled[i]
    """
    feats = np.asarray(features_scaled, dtype=np.float64)
    tgt = np.asarray(target_scaled, dtype=np.float64).reshape(-1, 1)
    if len(feats) != len(tgt):
        raise ValueError("features_scaled 与 target_scaled 长度不一致")

    raw_len = len(tgt)
    xtrain, ytrain, xtest, ytest = [], [], [], []
    test_k = []
    for i in range(time_steps, raw_len - 1):
        window_x = feats[i - time_steps : i]
        target_y = tgt[i]
        if i < length - 1:
            xtrain.append(window_x)
            ytrain.append(target_y)
        else:
            xtest.append(window_x)
            ytest.append(target_y)
            test_k.append(i)

    xtrain = np.asarray(xtrain, dtype=np.float64)
    ytrain = np.asarray(ytrain, dtype=np.float64).reshape(-1, 1)
    xtest = np.asarray(xtest, dtype=np.float64)
    ytest = np.asarray(ytest, dtype=np.float64).reshape(-1, 1)
    test_k = np.asarray(test_k, dtype=np.int64)

    if len(xtest) > max_test_window:
        xtest = xtest[:max_test_window]
        ytest = ytest[:max_test_window]
        test_k = test_k[:max_test_window]
    return xtrain, ytrain, xtest, ytest, test_k


def build_windows_from_features_with_direction(
    features_scaled: np.ndarray,
    target_scaled: np.ndarray,
    target_unscaled: np.ndarray,
    *,
    time_steps: int,
    length: int,
    max_test_window: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    与 build_windows_from_features 相同滑窗，额外构造方向标签：
    用 target_unscaled[i]（未标准化的下一期收益）> 0 为 1，否则为 0。
    """
    feats = np.asarray(features_scaled, dtype=np.float64)
    tgt = np.asarray(target_scaled, dtype=np.float64).reshape(-1, 1)
    raw = np.asarray(target_unscaled, dtype=np.float64).reshape(-1, 1)
    if len(feats) != len(tgt) or len(feats) != len(raw):
        raise ValueError("features_scaled / target_scaled / target_unscaled 长度不一致")

    raw_len = len(tgt)
    xtrain, ytrain, ydir_train = [], [], []
    xtest, ytest, ydir_test = [], [], []
    test_k = []
    for i in range(time_steps, raw_len - 1):
        window_x = feats[i - time_steps : i]
        target_y = tgt[i]
        d = 1.0 if float(raw[i, 0]) > 0.0 else 0.0
        if i < length - 1:
            xtrain.append(window_x)
            ytrain.append(target_y)
            ydir_train.append(d)
        else:
            xtest.append(window_x)
            ytest.append(target_y)
            ydir_test.append(d)
            test_k.append(i)

    xtrain = np.asarray(xtrain, dtype=np.float64)
    ytrain = np.asarray(ytrain, dtype=np.float64).reshape(-1, 1)
    ydir_train = np.asarray(ydir_train, dtype=np.float64).reshape(-1, 1)
    xtest = np.asarray(xtest, dtype=np.float64)
    ytest = np.asarray(ytest, dtype=np.float64).reshape(-1, 1)
    ydir_test = np.asarray(ydir_test, dtype=np.float64).reshape(-1, 1)
    test_k = np.asarray(test_k, dtype=np.int64)

    if len(xtest) > max_test_window:
        xtest = xtest[:max_test_window]
        ytest = ytest[:max_test_window]
        ydir_test = ydir_test[:max_test_window]
        test_k = test_k[:max_test_window]
    return xtrain, ytrain, ydir_train, xtest, ytest, ydir_test, test_k


def create_rework_style_features(df_prices: pd.DataFrame, *, price_col: str) -> pd.DataFrame:
    """
    lite 特征工程（严格因果）：
    1) 价格技术特征
    2) 金融市场特征（DXY/SP500/VIX/US10Y/OVX）
    3) 基本面特征（Stocks/Production/Rigs/Demand）
    4) 情绪特征（Oil_Trends/Gas_Trends）
    """
    df = df_prices.copy()
    p = pd.to_numeric(df[price_col], errors="coerce").astype(float)
    eps = 1e-8
    out = pd.DataFrame(index=df.index)
    # ---- 1) 价格特征 ----
    out["ret1"] = p.pct_change(fill_method=None).shift(1)
    out["ret2"] = p.pct_change(2, fill_method=None).shift(1)
    out["ret5"] = p.pct_change(5, fill_method=None).shift(1)
    out["mom1"] = p.diff(1).shift(1)
    out["mom3"] = p.diff(3).shift(1)
    out["mom5"] = p.diff(5).shift(1)
    out["ma5"] = p.rolling(5).mean().shift(1)
    out["ma10"] = p.rolling(10).mean().shift(1)
    out["ma20"] = p.rolling(20).mean().shift(1)
    out["std5"] = p.rolling(5).std().shift(1)
    out["std10"] = p.rolling(10).std().shift(1)
    out["zscore20"] = ((p - p.rolling(20).mean()) / (p.rolling(20).std() + eps)).shift(1)
    for lag in (1, 2, 3, 5, 10, 20):
        out[f"price_lag{lag}"] = p.shift(lag)

    # RSI(14)
    delta = p.diff()
    gain = delta.clip(lower=0.0).rolling(14).mean()
    loss = (-delta.clip(upper=0.0)).rolling(14).mean()
    rs = gain / (loss + eps)
    out["rsi14"] = (100.0 - (100.0 / (1.0 + rs))).shift(1)

    # MACD(12,26,9)
    ema12 = p.ewm(span=12, adjust=False).mean()
    ema26 = p.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    out["macd"] = macd.shift(1)
    out["macd_signal"] = signal.shift(1)
    out["macd_hist"] = (macd - signal).shift(1)

    # Bollinger(20,2)
    bb_mid = p.rolling(20).mean()
    bb_std = p.rolling(20).std()
    bb_up = bb_mid + 2.0 * bb_std
    bb_dn = bb_mid - 2.0 * bb_std
    out["bb_pos"] = ((p - bb_dn) / (bb_up - bb_dn + eps)).shift(1)
    out["bb_width"] = ((bb_up - bb_dn) / (bb_mid.abs() + eps)).shift(1)

    def _add_market_block(src_col: str, prefix: str):
        nonlocal out
        if src_col not in df.columns:
            return
        s = pd.to_numeric(df[src_col], errors="coerce").astype(float)
        block: dict[str, pd.Series] = {}
        block[f"{prefix}_Level"] = s.shift(1)
        block[f"{prefix}_Change"] = s.diff().shift(1)
        block[f"{prefix}_Diff2"] = s.diff().diff().shift(1)
        block[f"{prefix}_Return"] = np.log((s + eps) / (s.shift(1) + eps)).shift(1)
        for lag in (1, 2, 3, 5, 10, 20):
            block[f"{prefix}_Lag{lag}"] = s.shift(lag)
        for w in (5, 10, 20, 60):
            rm = s.rolling(w).mean()
            rsd = s.rolling(w).std()
            block[f"{prefix}_MA_{w}"] = rm.shift(1)
            block[f"{prefix}_Std_{w}"] = rsd.shift(1)
            block[f"{prefix}_Z_{w}"] = ((s - rm) / (rsd + eps)).shift(1)
            block[f"{prefix}_Momentum_{w}"] = s.pct_change(w, fill_method=None).shift(1)
        for w in (20, 60):
            block[f"{prefix}_Percentile_{w}"] = s.rolling(w).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == w else np.nan
            ).shift(1)
        out = pd.concat([out, pd.DataFrame(block, index=df.index)], axis=1)

    # ---- 2) 金融市场特征 ----
    _add_market_block("DXY", "DXY")
    _add_market_block("SP500", "SP500")
    _add_market_block("VIX", "VIX")
    _add_market_block("US10Y", "US10Y")
    _add_market_block("OVX", "OVX")
    if all(c in df.columns for c in ("OVX", "VIX")):
        ovx = pd.to_numeric(df["OVX"], errors="coerce").astype(float)
        vix = pd.to_numeric(df["VIX"], errors="coerce").astype(float)
        ratio = ovx / (vix + eps)
        out["OVX_VIX_Ratio"] = ratio.shift(1)
        out["OVX_VIX_Spread"] = (ovx - vix).shift(1)
        out["OVX_VIX_Ratio_Change"] = ratio.diff().shift(1)
    if all(c in out.columns for c in ("SP500_Return", "DXY_Return")):
        for w in (20, 60):
            out[f"SP500_DXY_Corr_{w}"] = out["SP500_Return"].rolling(w).corr(out["DXY_Return"]).shift(1)

    # ---- 3) 基本面特征 ----
    def _add_fund_block(src_col: str, prefix: str):
        nonlocal out
        if src_col not in df.columns:
            return
        s = pd.to_numeric(df[src_col], errors="coerce").astype(float)
        block: dict[str, pd.Series] = {}
        block[f"{prefix}_Level"] = s.shift(1)
        block[f"{prefix}_Change"] = s.diff().shift(1)
        block[f"{prefix}_Diff2"] = s.diff().diff().shift(1)
        block[f"{prefix}_PctChange"] = s.pct_change(fill_method=None).shift(1)
        for lag in (1, 2, 3, 5, 10, 20, 28):
            block[f"{prefix}_Lag{lag}"] = s.shift(lag)
        for w in (5, 10, 20, 60):
            rm = s.rolling(w).mean()
            rsd = s.rolling(w).std()
            block[f"{prefix}_MA_{w}"] = rm.shift(1)
            block[f"{prefix}_Std_{w}"] = rsd.shift(1)
            block[f"{prefix}_Z_{w}"] = ((s - rm) / (rsd + eps)).shift(1)
            block[f"{prefix}_Momentum_{w}"] = s.diff(w).shift(1)
            block[f"{prefix}_Trend_{w}"] = s.rolling(w).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == w else np.nan
            ).shift(1)
        for w in (20, 60):
            block[f"{prefix}_Percentile_{w}"] = s.rolling(w).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == w else np.nan
            ).shift(1)
        out = pd.concat([out, pd.DataFrame(block, index=df.index)], axis=1)

    _add_fund_block("Stocks", "Stocks")
    _add_fund_block("Production", "Production")
    _add_fund_block("Rigs", "Rigs")
    if all(c in df.columns for c in ("Production", "Demand")):
        prod = pd.to_numeric(df["Production"], errors="coerce").astype(float)
        dem = pd.to_numeric(df["Demand"], errors="coerce").astype(float)
        bal = prod - dem
        ratio = prod / (dem + eps)
        out["Supply_Demand_Balance"] = bal.shift(1)
        out["Supply_Demand_Ratio"] = ratio.shift(1)
        out["Supply_Demand_Balance_Change"] = bal.diff().shift(1)
        out["Supply_Demand_Ratio_Change"] = ratio.diff().shift(1)
        for w in (5, 20, 60):
            bmean = bal.rolling(w).mean()
            bstd = bal.rolling(w).std()
            out[f"Supply_Demand_Balance_Z_{w}"] = ((bal - bmean) / (bstd + eps)).shift(1)

    # ---- 4) 情绪特征 ----
    def _add_sent_block(src_col: str, prefix: str):
        nonlocal out
        if src_col not in df.columns:
            return
        s = pd.to_numeric(df[src_col], errors="coerce").astype(float)
        block: dict[str, pd.Series] = {}
        block[f"{prefix}_Trend"] = s.shift(1)
        block[f"{prefix}_Change"] = s.diff().shift(1)
        for lag in (1, 2, 3, 5, 10, 20):
            block[f"{prefix}_Lag{lag}"] = s.shift(lag)
        for w in (5, 10, 20, 60):
            rm = s.rolling(w).mean()
            rsd = s.rolling(w).std()
            block[f"{prefix}_MA_{w}"] = rm.shift(1)
            block[f"{prefix}_Std_{w}"] = rsd.shift(1)
            block[f"{prefix}_Z_{w}"] = ((s - rm) / (rsd + eps)).shift(1)
            block[f"{prefix}_Momentum_{w}"] = s.pct_change(w, fill_method=None).shift(1)
        out = pd.concat([out, pd.DataFrame(block, index=df.index)], axis=1)

    _add_sent_block("Oil_Trends", "Oil_Search")
    _add_sent_block("Gas_Trends", "Gas_Search")
    if all(c in df.columns for c in ("Oil_Trends", "Gas_Trends")):
        oil = pd.to_numeric(df["Oil_Trends"], errors="coerce").astype(float)
        gas = pd.to_numeric(df["Gas_Trends"], errors="coerce").astype(float)
        ratio = oil / (gas + eps)
        spread = oil - gas
        out["Oil_Gas_Search_Ratio"] = ratio.shift(1)
        out["Oil_Gas_Search_Spread"] = spread.shift(1)
        out["Oil_Gas_Search_Ratio_Change"] = ratio.diff().shift(1)
        for w in (5, 20, 60):
            rmean = ratio.rolling(w).mean()
            rstd = ratio.rolling(w).std()
            out[f"Oil_Gas_Search_Ratio_Z_{w}"] = ((ratio - rmean) / (rstd + eps)).shift(1)
            out[f"Oil_Gas_Search_Corr_{w}"] = oil.rolling(w).corr(gas).shift(1)

    # pandas 在大量逐列赋值后会出现 DataFrame fragmentation；
    # 这里做一次 copy() 去碎片化，避免后续连续告警与性能劣化。
    out = out.copy()

    # 季节性（Date 可用时）
    if "Date" in df.columns:
        dt = pd.to_datetime(df["Date"], errors="coerce")
        dow = dt.dt.weekday.astype(float)
        month = dt.dt.month.astype(float)
        out["dow_sin"] = np.sin(2.0 * np.pi * dow / 7.0)
        out["dow_cos"] = np.cos(2.0 * np.pi * dow / 7.0)
        out["mon_sin"] = np.sin(2.0 * np.pi * month / 12.0)
        out["mon_cos"] = np.cos(2.0 * np.pi * month / 12.0)

    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.ffill().bfill().fillna(0.0)
    return out


def create_rework_full_features(
    df_prices: pd.DataFrame,
    *,
    price_col: str,
    rework_script_path: str,
    enable_alias_features: bool = False,
) -> pd.DataFrame:
    """
    内置 full 特征工程（全部写在当前文件）：
    - 基于 lite 特征（价格/金融/基本面/情绪/季节性）
    - 追加波动率、市场结构、跨市场衍生关系
    - 追加严格地缘冲击特征（t-1 因果）
    """
    _ = rework_script_path  # 兼容现有参数签名；full 不再依赖外部脚本
    df = df_prices.copy()
    eps = 1e-8

    # 1) 先构建已有 lite 特征（已含严格 shift(1)）
    feat_df = create_rework_style_features(df, price_col=price_col)
    # full 阶段还会继续追加大量列，先去碎片化一次减少性能告警
    feat_df = feat_df.copy()

    # 2) 波动率扩展（历史/年化/变化/偏度/峰度）
    p = pd.to_numeric(df[price_col], errors="coerce").astype(float)
    log_ret = np.log((p + eps) / (p.shift(1) + eps))
    for w in (5, 10, 20, 60):
        vol = log_ret.rolling(w).std()
        feat_df[f"Volatility_{w}d"] = vol.shift(1)
        feat_df[f"Volatility_Annualized_{w}d"] = (vol * np.sqrt(252.0)).shift(1)
        if w >= 10:
            feat_df[f"Volatility_Change_{w}d"] = vol.diff().shift(1)
    for w in (20, 60):
        feat_df[f"Volatility_Skew_{w}"] = log_ret.rolling(w).skew().shift(1)
        feat_df[f"Volatility_Kurtosis_{w}"] = log_ret.rolling(w).kurt().shift(1)
    if "OVX" in df.columns and "Volatility_Annualized_20d" in feat_df.columns:
        ovx = pd.to_numeric(df["OVX"], errors="coerce").astype(float)
        feat_df["Volatility_Risk_Premium"] = (ovx - feat_df["Volatility_Annualized_20d"]).shift(1)

    # 3) 市场结构（期现/跨油种/期限结构）
    if all(c in df.columns for c in ("WTI_Futures", "WTI_Spot")):
        fut = pd.to_numeric(df["WTI_Futures"], errors="coerce").astype(float)
        spot = pd.to_numeric(df["WTI_Spot"], errors="coerce").astype(float)
        basis = fut - spot
        feat_df["Basis"] = basis.shift(1)
        feat_df["Basis_Change"] = basis.diff().shift(1)
        feat_df["Basis_Pct"] = (basis / (spot.abs() + eps)).shift(1)
        # np.where 返回 ndarray；转成 Series 后再 shift 以保持时间索引对齐
        market_structure = pd.Series(
            np.where(basis > 0.0, 1.0, -1.0), index=df.index, dtype=float
        )
        feat_df["Market_Structure"] = market_structure.shift(1)
    if all(c in df.columns for c in ("CL1", "CL2")):
        cl1 = pd.to_numeric(df["CL1"], errors="coerce").astype(float)
        cl2 = pd.to_numeric(df["CL2"], errors="coerce").astype(float)
        spread = cl1 - cl2
        feat_df["Term_Spread_1_2"] = spread.shift(1)
        feat_df["Term_Spread_Pct"] = (spread / (cl2.abs() + eps)).shift(1)
    if all(c in df.columns for c in ("WTI_Futures", "Brent")):
        fut = pd.to_numeric(df["WTI_Futures"], errors="coerce").astype(float)
        brent = pd.to_numeric(df["Brent"], errors="coerce").astype(float)
        feat_df["WTI_Brent_Spread"] = (fut - brent).shift(1)
        feat_df["WTI_Brent_Ratio"] = (fut / (brent + eps)).shift(1)

    # 4) 衍生关系（滚动相关 + 市场状态）
    if all(c in feat_df.columns for c in ("SP500_Return", "DXY_Return")):
        for w in (20, 60):
            feat_df[f"SP500_DXY_Corr_{w}"] = feat_df["SP500_Return"].rolling(w).corr(
                feat_df["DXY_Return"]
            ).shift(1)
    if all(c in feat_df.columns for c in ("DXY_Return", "ret1")):
        for w in (20, 60):
            feat_df[f"Oil_Dollar_Correlation_{w}"] = feat_df["ret1"].rolling(w).corr(
                feat_df["DXY_Return"]
            ).shift(1)
    if all(c in feat_df.columns for c in ("SP500_Return", "ret1")):
        for w in (20, 60):
            feat_df[f"Oil_Stock_Correlation_{w}"] = feat_df["ret1"].rolling(w).corr(
                feat_df["SP500_Return"]
            ).shift(1)
    if "ret1" in feat_df.columns and "Volatility_20d" in feat_df.columns:
        ret20 = feat_df["ret1"].rolling(20).sum()
        vol20 = feat_df["Volatility_20d"]
        feat_df["Market_HighVol_Up"] = (
            (ret20 > ret20.rolling(60).mean()) & (vol20 > vol20.rolling(60).mean())
        ).astype(float).shift(1)
        feat_df["Market_LowVol_Down"] = (
            (ret20 < ret20.rolling(60).mean()) & (vol20 < vol20.rolling(60).mean())
        ).astype(float).shift(1)

    # 4.5 命名兼容层（可选）：默认关闭，避免同义特征重复入模
    if enable_alias_features:
        alias_prefixes: list[str] = []
        if price_col:
            alias_prefixes.append(str(price_col))
        if "WTI_Futures" in df.columns and "WTI_Futures" not in alias_prefixes:
            alias_prefixes.append("WTI_Futures")
        if "ClosePrice" in df.columns and "ClosePrice" not in alias_prefixes:
            alias_prefixes.append("ClosePrice")
        for px in alias_prefixes:
            if "ret1" in feat_df.columns and f"{px}_Return" not in feat_df.columns:
                feat_df[f"{px}_Return"] = feat_df["ret1"]
            if "mom1" in feat_df.columns and f"{px}_Change" not in feat_df.columns:
                feat_df[f"{px}_Change"] = feat_df["mom1"]
            if "price_lag1" in feat_df.columns and f"{px}_Lag1" not in feat_df.columns:
                feat_df[f"{px}_Lag1"] = feat_df["price_lag1"]
            if "ma5" in feat_df.columns and f"{px}_MA_5" not in feat_df.columns:
                feat_df[f"{px}_MA_5"] = feat_df["ma5"]
            if "std5" in feat_df.columns and f"{px}_Std_5" not in feat_df.columns:
                feat_df[f"{px}_Std_5"] = feat_df["std5"]
            if "zscore20" in feat_df.columns and f"{px}_Z_20" not in feat_df.columns:
                feat_df[f"{px}_Z_20"] = feat_df["zscore20"]

    # 5) 追加严格地缘冲击特征（因果：全部 t-1）
    geo_feat = build_geo_rigorous_features(
        df.set_index("Date") if "Date" in df.columns else df
    )
    if not geo_feat.empty:
        feat_df = feat_df.join(geo_feat, how="left")
    # 只保留数值特征列（避免字符串/对象列进入模型）
    feat_df = feat_df.select_dtypes(include=[np.number]).copy()
    feat_df = feat_df.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)
    return feat_df


def rf_select_top_n_features(
    feat_df: pd.DataFrame,
    *,
    y: np.ndarray,
    train_end_exclusive: int,
    top_n: int,
    n_estimators: int,
    random_state: int,
    max_depth: int | None = None,
    keep_also_cols: list[str] | None = None,
    plot_path: str | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    对齐 rework 的 RF Top-N 特征选择逻辑（仅训练段拟合，再筛选列）。
    说明：这里没有单独 val/test DataFrame，故仅返回筛选后的特征矩阵与特征名。
    """
    if top_n <= 0:
        raise ValueError("rf_top_n 必须 > 0")
    if keep_also_cols is None:
        keep_also_cols = []

    # 保留全部数值型特征（避免只识别 float64/int64 导致特征被误过滤）
    feature_cols = [c for c in feat_df.columns if pd.api.types.is_numeric_dtype(feat_df[c])]
    if len(feature_cols) == 0:
        raise ValueError("随机森林特征选择：未找到可用的数值型特征列。")

    y = np.asarray(y, dtype=np.float64).reshape(-1)
    n = min(len(feat_df), len(y))
    fit_df = feat_df.iloc[:n][feature_cols].copy()
    y = y[:n]
    te = int(min(max(1, train_end_exclusive), n))
    y_train = y[:te]
    y_std = float(np.nanstd(y_train))
    print(f"RF 拟合目标统计: n={len(y_train)}, std={y_std:.8f}")

    # 与 rework 一致：特征 fillna(0)，不额外 drop 行
    X_train = fit_df.iloc[:te].fillna(0).values

    rf = RandomForestRegressor(
        n_estimators=int(n_estimators),
        random_state=int(random_state),
        max_depth=max_depth,
        n_jobs=1,
    )
    rf.fit(X_train, y_train)
    importances = np.asarray(rf.feature_importances_, dtype=np.float64)
    if len(importances) != len(feature_cols):
        raise RuntimeError("随机森林特征重要性长度异常")
    imp_max = float(np.nanmax(importances)) if len(importances) > 0 else float("nan")
    imp_sum = float(np.nansum(importances)) if len(importances) > 0 else float("nan")
    print(f"RF 重要性统计: max={imp_max:.8e}, sum={imp_sum:.8e}")
    if np.all(np.isfinite(importances)) and np.all(importances <= 1e-12):
        print("[警告] RF 重要性几乎全为 0：目标可能近常数或输入特征信息不足。")

    top_n = min(int(top_n), len(feature_cols))
    order = np.argsort(importances)[::-1][:top_n]
    selected_cols = [feature_cols[i] for i in order]

    if plot_path:
        import matplotlib.pyplot as plt

        top_k = min(30, len(feature_cols))
        order_all = np.argsort(importances)[::-1][:top_k]
        names = [feature_cols[i] for i in order_all][::-1]
        vals = importances[order_all][::-1]
        fig_rf, ax_rf = plt.subplots(1, 1, figsize=(10, 7), constrained_layout=True)
        ax_rf.barh(names, vals, color="#F58518")
        ax_rf.set_title(f"RF Feature Importance Top-{top_k}")
        ax_rf.set_xlabel("importance")
        if np.all(np.asarray(vals) <= 1e-12):
            ax_rf.text(
                0.5,
                0.5,
                "All importances are ~0\n(check target variance / data quality)",
                transform=ax_rf.transAxes,
                ha="center",
                va="center",
                fontsize=10,
                color="red",
            )
        fig_rf.savefig(plot_path, dpi=180, bbox_inches="tight")
        plt.close(fig_rf)

    # 对齐 rework：支持强制追加一些时序关键列
    for col in keep_also_cols:
        if col in feature_cols and col not in selected_cols:
            selected_cols.append(col)
    return feat_df[selected_cols].copy(), selected_cols


def shap_refine_feature_columns(
    feat_df: pd.DataFrame,
    selected_cols: list[str],
    y: np.ndarray,
    train_end_exclusive: int,
    *,
    shap_top_n: int,
    n_estimators: int,
    random_state: int,
    max_depth: int | None = None,
    max_shap_samples: int = 512,
    plot_path: str | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    在 RF 初筛后的列上重训随机森林，用 SHAP(TreeExplainer) 的 mean(|SHAP|) 再取前 shap_top_n。
    """
    try:
        import shap
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            f"已启用 SHAP 特征精炼，需要安装：pip install shap\n导入失败: {e}"
        ) from e

    if shap_top_n <= 0:
        raise ValueError("shap_top_n 必须 > 0")
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    n = min(len(feat_df), len(y))
    te = int(min(max(1, train_end_exclusive), n))
    X_all = feat_df.iloc[:n][selected_cols].fillna(0).values
    y = y[:n]
    X_train = X_all[:te]
    y_train = y[:te]

    rf = RandomForestRegressor(
        n_estimators=int(n_estimators),
        random_state=int(random_state),
        max_depth=max_depth,
        n_jobs=1,
    )
    rf.fit(X_train, y_train)

    m = min(int(max_shap_samples), len(X_train))
    if m < 1:
        raise ValueError("SHAP 精炼：训练样本过少")
    rng = np.random.RandomState(int(random_state))
    if m >= len(X_train):
        idx = np.arange(len(X_train))
    else:
        idx = rng.choice(len(X_train), size=m, replace=False)
    X_sub = X_train[idx]

    explainer = shap.TreeExplainer(rf)
    sv = explainer.shap_values(X_sub)
    if isinstance(sv, list):
        sv = sv[0]
    sv = np.asarray(sv, dtype=np.float64)
    mean_abs = np.mean(np.abs(sv), axis=0)
    k = min(int(shap_top_n), len(selected_cols))
    order = np.argsort(mean_abs)[::-1][:k]
    final_cols = [selected_cols[j] for j in order]

    if plot_path:
        import matplotlib.pyplot as plt

        top_k = min(20, len(selected_cols))
        top_all_idx = np.argsort(mean_abs)[::-1][:top_k]
        top_names = [selected_cols[j] for j in top_all_idx][::-1]
        top_vals = mean_abs[top_all_idx][::-1]
        fig_shap, ax_shap = plt.subplots(1, 1, figsize=(10, 6), constrained_layout=True)
        ax_shap.barh(top_names, top_vals, color="#4C78A8")
        ax_shap.set_title(f"SHAP mean(|value|) Top-{top_k}")
        ax_shap.set_xlabel("mean(|SHAP value|)")
        fig_shap.savefig(plot_path, dpi=180, bbox_inches="tight")
        plt.close(fig_shap)
    return feat_df[final_cols].copy(), final_cols


def trim_to_batch(x: np.ndarray, y: np.ndarray, batch_size: int) -> tuple[np.ndarray, np.ndarray]:
    n = (len(x) // batch_size) * batch_size
    return x[:n], y[:n]


def directional_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    exclude_flat_true: bool = True,
) -> float:
    """
    相邻测试窗在「逆变换后价格」上的涨跌方向是否一致。
    exclude_flat_true=True 时跳过真实 Δy==0（无方向）的相邻对。
    """
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()
    if len(y_true) < 2:
        return float("nan")
    d_true = np.diff(y_true)
    d_pred = np.diff(y_pred)
    if exclude_flat_true:
        mask = d_true != 0
    else:
        mask = np.ones_like(d_true, dtype=bool)
    if not np.any(mask):
        return float("nan")
    agree = np.sign(d_true[mask]) == np.sign(d_pred[mask])
    return float(np.mean(agree))


def build_sequence_model(
    cell: str,
    batch_size: int,
    time_steps: int,
    *,
    n_features: int = 1,
    bidirectional: bool,
    stateful: bool,
    units: int,
    dropout: float,
) -> Model:
    """
    结构：Input(batch, time_steps, n_features)
    -> (Bi-)?(LSTM|GRU)(units=units, stateful) x2（第一层 return_sequences=True，第二层 False）
    -> Dense(10) -> Dense(1) -> 单点输出（horizon=1）
    """
    cell = cell.lower().strip()
    if cell not in ("lstm", "gru"):
        raise ValueError("cell 必须是 lstm 或 gru")

    Rnn = LSTM if cell == "lstm" else GRU
    if stateful:
        input_layer = Input(batch_shape=(batch_size, time_steps, n_features))
    else:
        input_layer = Input(shape=(time_steps, n_features))

    if bidirectional:
        r1 = Bidirectional(
            Rnn(units=units, stateful=stateful, return_sequences=True, dropout=dropout)
        )(input_layer)
        r2 = Bidirectional(
            Rnn(units=units, stateful=stateful, return_sequences=False, dropout=dropout)
        )(r1)
    else:
        r1 = Rnn(
            units=units, stateful=stateful, return_sequences=True, dropout=dropout
        )(input_layer)
        r2 = Rnn(
            units=units, stateful=stateful, return_sequences=False, dropout=dropout
        )(r1)

    if dropout > 0:
        r2 = Dropout(dropout)(r2)
    l1 = Dense(units=10)(r2)
    out = Dense(units=1)(l1)
    return Model(inputs=input_layer, outputs=out)


def build_sequence_model_multi(
    cell: str,
    batch_size: int,
    time_steps: int,
    *,
    n_features: int = 1,
    bidirectional: bool,
    stateful: bool,
    units: int,
    dropout: float,
) -> Model:
    """
    双输出：return（回归，与原先一致）+ dir（涨跌方向，sigmoid 二分类）。
    """
    cell = cell.lower().strip()
    if cell not in ("lstm", "gru"):
        raise ValueError("cell 必须是 lstm 或 gru")

    Rnn = LSTM if cell == "lstm" else GRU
    if stateful:
        input_layer = Input(batch_shape=(batch_size, time_steps, n_features))
    else:
        input_layer = Input(shape=(time_steps, n_features))

    if bidirectional:
        r1 = Bidirectional(
            Rnn(units=units, stateful=stateful, return_sequences=True, dropout=dropout)
        )(input_layer)
        r2 = Bidirectional(
            Rnn(units=units, stateful=stateful, return_sequences=False, dropout=dropout)
        )(r1)
    else:
        r1 = Rnn(
            units=units, stateful=stateful, return_sequences=True, dropout=dropout
        )(input_layer)
        r2 = Rnn(
            units=units, stateful=stateful, return_sequences=False, dropout=dropout
        )(r1)

    if dropout > 0:
        r2 = Dropout(dropout)(r2)
    shared = Dense(units=10, activation="relu")(r2)
    out_return = Dense(units=1, name="return")(shared)
    dir_h = Dense(units=16, activation="relu")(r2)
    out_dir = Dense(units=1, activation="sigmoid", name="dir")(dir_h)
    return Model(inputs=input_layer, outputs=[out_return, out_dir])


def trim_to_batch_multi(
    x: np.ndarray,
    y_ret: np.ndarray,
    y_dir: np.ndarray,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = (len(x) // batch_size) * batch_size
    return x[:n], y_ret[:n], y_dir[:n]


def predict_next_day(
    *,
    trained_model: Model,
    cell: str,
    bidirectional: bool,
    stateful: bool,
    units: int,
    dropout: float,
    time_steps: int,
    n_features: int,
    use_window_vmd: bool,
    vmd_k: int,
    vmd_alpha: float,
    vmd_tau: float,
    vmd_dc: int,
    vmd_init: int,
    vmd_tol: float,
    vmd_drop_high_freq: int,
    vmd_drop_mode: str,
    sc,
    scaled_series: np.ndarray,
    return_type: str,
    prices: np.ndarray,
    last_date: object | None,
    multi_head: bool = False,
) -> dict[str, object]:
    """
    用最后 time_steps 个点预测下一天。
    收益任务：预测下一天收益，并还原对应下一天价格。
    multi_head=True 时与训练一致，使用双头结构，仅取 return 头做收益与价格还原。
    """
    if len(scaled_series) < time_steps:
        raise ValueError("序列长度不足以构造预测窗口")

    # 构建 batch_size=1 的“同构模型”并拷贝权重。
    # 这样可以不受训练时 batch_size 的限制，直接对最后一个窗口做单样本推理。
    if multi_head:
        infer_model = build_sequence_model_multi(
            cell,
            1,
            time_steps,
            n_features=n_features,
            bidirectional=bidirectional,
            stateful=stateful,
            units=units,
            dropout=dropout,
        )
        infer_model.compile(
            optimizer="adam",
            loss={"return": "mae", "dir": "binary_crossentropy"},
        )
    else:
        infer_model = build_sequence_model(
            cell,
            1,
            time_steps,
            n_features=n_features,
            bidirectional=bidirectional,
            stateful=stateful,
            units=units,
            dropout=dropout,
        )
        infer_model.compile(optimizer="adam", loss="mae")
    infer_model.set_weights(trained_model.get_weights())
    infer_model.reset_states()

    x_last_raw = np.asarray(scaled_series[-time_steps:], dtype=np.float64)
    if use_window_vmd:
        x_last_proc, _ = apply_vmd_on_target(
            x_last_raw,
            k=vmd_k,
            alpha=vmd_alpha,
            tau=vmd_tau,
            dc=vmd_dc,
            init=vmd_init,
            tol=vmd_tol,
            drop_high_freq=vmd_drop_high_freq,
            drop_mode=vmd_drop_mode,
            debug_print=False,
        )
    else:
        x_last_proc = x_last_raw
    if n_features == 1:
        x_last = x_last_proc.reshape(1, time_steps, 1)
    else:
        x_last = x_last_proc.reshape(1, time_steps, n_features)
    raw_pred = infer_model.predict(x_last, batch_size=1, verbose=0)
    if multi_head:
        y_last_scaled = np.asarray(raw_pred[0], dtype=np.float64).reshape(1, 1)
        p_dir = float(np.asarray(raw_pred[1], dtype=np.float64).ravel()[0])
    else:
        y_last_scaled = np.asarray(raw_pred, dtype=np.float64).reshape(1, 1)
        p_dir = float("nan")

    pred = sc.inverse_transform(y_last_scaled).reshape(1, 1)
    pred_r = float(pred[0, 0])
    last_price = float(prices[-1, 0])
    if return_type == "log":
        pred_price = last_price * float(np.exp(pred_r))
    else:
        pred_price = last_price * (1.0 + pred_r)
    out: dict[str, object] = {
        "pred_return": pred_r,
        "pred_price": pred_price,
        "last_price": last_price,
        "last_date": last_date,
    }
    if multi_head and not np.isnan(p_dir):
        out["pred_prob_up"] = p_dir
    return out


def load_saved_runtime_params(path: str) -> dict:
    """
    读取运行参数 JSON。
    优先级：
    1) params（推荐，放全量可调参数）
    2) best_params（兼容历史 Optuna 导出）
    3) 顶层常见参数键（直接平铺在 JSON）
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON 顶层必须是对象: {path}")

    if isinstance(data.get("params"), dict):
        return dict(data["params"])
    if isinstance(data.get("best_params"), dict):
        return dict(data["best_params"])

    # 兜底：若 JSON 平铺参数，则仅采集 DEFAULT_ARGS 中定义的可配置键。
    candidate_keys = set(DEFAULT_ARGS.keys())
    flat = {k: v for k, v in data.items() if k in candidate_keys}
    if flat:
        return flat
    raise ValueError(f"JSON 未找到可用参数（params/best_params/平铺参数）: {path}")


def persist_runtime_params(path: str, args: SimpleNamespace) -> None:
    """将当前可配置参数完整写回 JSON，作为单一配置源。"""
    payload = {k: getattr(args, k) for k in DEFAULT_ARGS.keys() if hasattr(args, k)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"params": payload}, f, ensure_ascii=False, indent=2)


def run_optuna_search(prices: np.ndarray, base_args: SimpleNamespace) -> dict:
    """
    Optuna 自动调参。
    目标：在训练段内部留出时间序列验证集，最大化综合分数（默认偏重方向准确率）：
      score = w_r2 * r2_return + w_dir * dir_acc - w_rmse * rmse

    加速：`base_args.optuna_quick=True` 时缩小搜索空间、降低每 trial 的 epochs（粗搜）；
    再配合较小的 `optuna_n_trials`。精细搜可设 quick=False 并增大 trials。
    """
    try:
        import optuna
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "需要安装 Optuna：pip install optuna\n"
            f"导入失败: {e}"
        ) from e

    raw_returns = price_to_return_series(prices, return_type=base_args.return_type)
    quick = getattr(base_args, "optuna_quick", False)
    if quick:
        print(
            "Optuna 快速模式：离散化超参 + 每 trial 更少 epoch；"
            f"n_trials={base_args.optuna_n_trials}。"
        )

    def objective(trial):
        args = SimpleNamespace(**vars(base_args))
        args.cell = trial.suggest_categorical("cell", ["lstm", "gru"])
        args.bidirectional = trial.suggest_categorical("bidirectional", [True, False])
        if quick:
            args.units = trial.suggest_categorical("units", [32, 64, 96, 128])
            args.dropout = trial.suggest_categorical("dropout", [0.0, 0.1, 0.2])
            args.batch_size = trial.suggest_categorical("batch_size", [32, 64])
            args.time_steps = trial.suggest_categorical("time_steps", [10, 20, 30, 40])
            args.epochs = trial.suggest_int("epochs", 4, 12)
            args.loss = trial.suggest_categorical("loss", ["huber", "mae"])
            args.learning_rate = trial.suggest_float(
                "learning_rate", 5e-4, 3e-3, log=True
            )
            args.vmd_k = int(trial.suggest_categorical("vmd_k", [4, 6, 8]))
            args.vmd_alpha = trial.suggest_float(
                "vmd_alpha", 1000.0, 6000.0, log=True
            )
            args.vmd_tau = trial.suggest_categorical("vmd_tau", [0.0, 0.01])
        else:
            args.units = trial.suggest_int("units", 32, 256, step=32)
            args.dropout = trial.suggest_float("dropout", 0.0, 0.4, step=0.05)
            args.batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128])
            args.time_steps = trial.suggest_int("time_steps", 10, 60, step=5)
            args.epochs = trial.suggest_int("epochs", 50, 100)
            args.loss = trial.suggest_categorical("loss", ["huber", "mae", "mse"])
            args.learning_rate = trial.suggest_float(
                "learning_rate", 1e-4, 5e-3, log=True
            )
            args.vmd_k = trial.suggest_int("vmd_k", 4, 10)
            args.vmd_alpha = trial.suggest_float(
                "vmd_alpha", 500.0, 8000.0, log=True
            )
            args.vmd_tau = trial.suggest_categorical("vmd_tau", [0.0, 0.01, 0.1])
        args.vmd_drop_high_freq = trial.suggest_int(
            "vmd_drop_high_freq", 1, min(3, args.vmd_k - 1)
        )

        # 标签：收益（none 压缩）+ 全局 VMD 重构
        training_set = compress_returns(raw_returns, method="none", scale=1.0)
        n = len(training_set)
        try:
            length = get_train_length(
                n, args.batch_size, args.test_percent, verbose=False
            )
        except ValueError:
            raise optuna.TrialPruned()
        if args.vmd_drop_high_freq >= args.vmd_k:
            raise optuna.TrialPruned()
        training_set, _ = apply_vmd_on_target(
            training_set,
            k=args.vmd_k,
            alpha=args.vmd_alpha,
            tau=args.vmd_tau,
            dc=args.vmd_dc,
            init=args.vmd_init,
            tol=args.vmd_tol,
            drop_high_freq=args.vmd_drop_high_freq,
            drop_mode=args.vmd_drop_mode,
            debug_print=False,
        )
        sc = StandardScaler(with_mean=True, with_std=True)
        sc.fit(training_set[:length])
        training_set_scaled = sc.transform(training_set)

        xtrain, ytrain, _, _, _ = build_windows(
            training_set_scaled,
            raw_len=n,
            time_steps=args.time_steps,
            length=length,
            max_test_window=args.max_test,
        )
        xtrain, ytrain = trim_to_batch(xtrain, ytrain, args.batch_size)
        # 训练窗目标下标 i 覆盖 [time_steps, length-2]
        train_k = np.arange(args.time_steps, length - 1, dtype=np.int64)
        train_k = train_k[: len(xtrain)]
        if len(xtrain) < args.batch_size * 4:
            raise optuna.TrialPruned()

        # 时间序列验证集：训练尾部 20%
        split = int(len(xtrain) * 0.8)
        split = max(args.batch_size, split - (split % args.batch_size))
        xtr, ytr = xtrain[:split], ytrain[:split]
        xval, yval = xtrain[split:], ytrain[split:]
        kval = train_k[split:]
        xval, yval = trim_to_batch(xval, yval, args.batch_size)
        kval = kval[: len(xval)]
        if len(xval) == 0:
            raise optuna.TrialPruned()

        model = build_sequence_model(
            args.cell,
            args.batch_size,
            args.time_steps,
            bidirectional=args.bidirectional,
            stateful=args.stateful,
            units=args.units,
            dropout=args.dropout,
        )
        loss_fn = Huber() if args.loss == "huber" else args.loss
        model.compile(optimizer=Adam(learning_rate=args.learning_rate), loss=loss_fn)
        model.fit(
            xtr,
            ytr,
            shuffle=not args.stateful,
            epochs=args.epochs,
            batch_size=args.batch_size,
            verbose=0,
        )
        if args.stateful and args.reset_states_before_eval:
            model.reset_states()

        per = model.predict(xval, batch_size=args.batch_size, verbose=0)
        p = sc.inverse_transform(per.reshape(-1, 1))
        y = sc.inverse_transform(yval.reshape(-1, 1))
        rmse = float(np.sqrt(np.mean((p - y) ** 2)))
        dir_acc = directional_accuracy(y, p, exclude_flat_true=True)

        if np.any(kval < 0) or np.any(kval >= len(prices) - 1):
            raise optuna.TrialPruned()
        base_price = prices[kval].reshape(-1, 1)
        if args.return_type == "log":
            p_price = base_price * np.exp(p)
            y_price = base_price * np.exp(y)
        else:
            p_price = base_price * (1.0 + p)
            y_price = base_price * (1.0 + y)
        r2_price = float(r2_score(y_price, p_price))
        r2_return = float(r2_score(y, p))

        w_r2 = float(getattr(base_args, "optuna_score_w_r2", 0.25))
        w_dir = float(getattr(base_args, "optuna_score_w_dir", 0.70))
        w_rmse = float(getattr(base_args, "optuna_score_w_rmse", 0.05))
        score = w_r2 * r2_return + w_dir * dir_acc - w_rmse * rmse
        trial.set_user_attr("r2_return", r2_return)
        trial.set_user_attr("r2_price", r2_price)
        trial.set_user_attr("dir_acc", dir_acc)
        trial.set_user_attr("rmse", rmse)
        return score

    sampler = optuna.samplers.TPESampler(seed=base_args.optuna_seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=base_args.optuna_n_trials, show_progress_bar=False)

    best = {
        "best_value": study.best_value,
        "best_params": study.best_params,
        "best_user_attrs": study.best_trial.user_attrs,
    }
    with open(base_args.optuna_best_path, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)
    print(f"Optuna 完成：best_score={study.best_value:.6f}")
    print(f"best_params 已保存到 {base_args.optuna_best_path}")
    return best["best_params"]


def run_optuna_quick_basic(
    prices: np.ndarray, df_prices: pd.DataFrame, base_args: SimpleNamespace
) -> dict:
    """
    快速专项搜索：调 learning_rate / rf_top_n / shap_top_n / epochs / 早停参数。
    其余参数固定当前配置，适配 use_rework_features=True 的主流程。
    """
    try:
        import optuna
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "需要安装 Optuna：pip install optuna\n"
            f"导入失败: {e}"
        ) from e

    raw_returns = price_to_return_series(prices, return_type=base_args.return_type)

    def objective(trial):
        args = SimpleNamespace(**vars(base_args))
        args.learning_rate = trial.suggest_float("learning_rate", 3e-4, 3e-3, log=True)
        args.rf_top_n = trial.suggest_int("rf_top_n", 8, 40)
        args.shap_top_n = trial.suggest_int("shap_top_n", 5, min(30, int(args.rf_top_n)))
        args.epochs = trial.suggest_int("epochs", 6, 24)
        args.early_stopping_patience = trial.suggest_int("early_stopping_patience", 4, 16)
        args.early_stopping_min_delta = trial.suggest_float(
            "early_stopping_min_delta", 1e-6, 1e-3, log=True
        )

        training_set = compress_returns(raw_returns, method="none", scale=1.0)
        n = len(training_set)
        try:
            length = get_train_length(n, args.batch_size, args.test_percent, verbose=False)
        except ValueError:
            raise optuna.TrialPruned()
        if args.vmd_drop_high_freq >= args.vmd_k:
            raise optuna.TrialPruned()

        training_set, _ = apply_vmd_on_target(
            training_set,
            k=args.vmd_k,
            alpha=args.vmd_alpha,
            tau=args.vmd_tau,
            dc=args.vmd_dc,
            init=args.vmd_init,
            tol=args.vmd_tol,
            drop_high_freq=args.vmd_drop_high_freq,
            drop_mode=args.vmd_drop_mode,
            debug_print=False,
        )
        n = len(training_set)
        length = min(length, n)

        sc_y = StandardScaler(with_mean=True, with_std=True)
        sc_y.fit(training_set[:length])
        y_scaled = sc_y.transform(training_set)

        # 特征：优先 full rework，其次 lite
        if args.use_rework_features:
            if str(getattr(args, "rework_feature_mode", "full")).lower().strip() == "full":
                feat_df = create_rework_full_features(
                    df_prices,
                    price_col=args.price_col,
                    rework_script_path=args.rework_script_path,
                    enable_alias_features=bool(getattr(args, "enable_alias_features", False)),
                )
            else:
                feat_df = create_rework_style_features(df_prices, price_col=args.price_col)
            feat_df = feat_df.iloc[1:].copy()
            if len(feat_df) != n:
                min_n = min(len(feat_df), n)
                feat_df = feat_df.iloc[:min_n].copy()
                y_scaled = y_scaled[:min_n]
                training_set = training_set[:min_n]
                n = min_n
                length = min(length, n)
            feat_df, _ = rf_select_top_n_features(
                feat_df,
                y=training_set.reshape(-1),
                train_end_exclusive=length,
                top_n=int(args.rf_top_n),
                n_estimators=int(args.rf_n_estimators),
                random_state=int(args.rf_random_state),
                keep_also_cols=list(getattr(args, "rf_keep_also_cols", [])),
            )
            if bool(getattr(args, "shap_refine_enable", True)):
                feat_df, _ = shap_refine_feature_columns(
                    feat_df,
                    selected_cols=list(feat_df.columns),
                    y=training_set.reshape(-1),
                    train_end_exclusive=length,
                    shap_top_n=int(getattr(args, "shap_top_n", 30)),
                    n_estimators=int(args.rf_n_estimators),
                    random_state=int(args.rf_random_state),
                    max_shap_samples=int(getattr(args, "shap_max_samples", 256)),
                )
            sc_x = StandardScaler(with_mean=True, with_std=True)
            sc_x.fit(feat_df.values[:length])
            x_scaled = sc_x.transform(feat_df.values)
            xtrain, ytrain, _, _, _ = build_windows_from_features(
                x_scaled,
                y_scaled,
                time_steps=args.time_steps,
                length=length,
                max_test_window=args.max_test,
            )
        else:
            xtrain, ytrain, _, _, _ = build_windows(
                y_scaled,
                raw_len=n,
                time_steps=args.time_steps,
                length=length,
                max_test_window=args.max_test,
            )

        xtrain, ytrain = trim_to_batch(xtrain, ytrain, args.batch_size)
        if len(xtrain) < args.batch_size * 4:
            raise optuna.TrialPruned()

        split = int(len(xtrain) * 0.8)
        split = max(args.batch_size, split - (split % args.batch_size))
        xtr, ytr = xtrain[:split], ytrain[:split]
        xval, yval = xtrain[split:], ytrain[split:]
        xval, yval = trim_to_batch(xval, yval, args.batch_size)
        if len(xval) == 0:
            raise optuna.TrialPruned()

        model = build_sequence_model(
            args.cell,
            args.batch_size,
            args.time_steps,
            n_features=xtrain.shape[-1],
            bidirectional=args.bidirectional,
            stateful=args.stateful,
            units=args.units,
            dropout=args.dropout,
        )
        loss_fn = Huber() if args.loss == "huber" else args.loss
        model.compile(optimizer=Adam(learning_rate=args.learning_rate), loss=loss_fn)
        callbacks = []
        if bool(getattr(args, "early_stopping_enable", True)):
            callbacks.append(
                EarlyStopping(
                    monitor="val_loss",
                    patience=int(getattr(args, "early_stopping_patience", 12)),
                    min_delta=float(getattr(args, "early_stopping_min_delta", 1e-5)),
                    mode="min",
                    restore_best_weights=True,
                    verbose=0,
                )
            )
        model.fit(
            xtr,
            ytr,
            validation_data=(xval, yval),
            shuffle=not args.stateful,
            epochs=args.epochs,
            batch_size=args.batch_size,
            verbose=0,
            callbacks=callbacks,
        )
        per = model.predict(xval, batch_size=args.batch_size, verbose=0)
        p = sc_y.inverse_transform(per.reshape(-1, 1))
        y = sc_y.inverse_transform(yval.reshape(-1, 1))
        rmse = float(np.sqrt(np.mean((p - y) ** 2)))
        dir_acc = directional_accuracy(y, p, exclude_flat_true=True)
        r2_return = float(r2_score(y, p))
        w_r2 = float(getattr(base_args, "optuna_score_w_r2", 0.25))
        w_dir = float(getattr(base_args, "optuna_score_w_dir", 0.70))
        w_rmse = float(getattr(base_args, "optuna_score_w_rmse", 0.05))
        score = w_r2 * r2_return + w_dir * dir_acc - w_rmse * rmse
        trial.set_user_attr("r2_return", r2_return)
        trial.set_user_attr("dir_acc", dir_acc)
        trial.set_user_attr("rmse", rmse)
        return score

    sampler = optuna.samplers.TPESampler(seed=base_args.optuna_seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=base_args.optuna_n_trials, show_progress_bar=False)
    best = {
        "best_value": study.best_value,
        "best_params": study.best_params,
        "best_user_attrs": study.best_trial.user_attrs,
    }
    with open(base_args.optuna_best_path, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)
    print(f"Optuna(quick-basic) 完成：best_score={study.best_value:.6f}")
    print(f"best_params 已保存到 {base_args.optuna_best_path}")
    return best["best_params"]


DEFAULT_ARGS: dict[str, object] = {
    "csv": DEFAULT_CSV,
    "data_base_dir": DEFAULT_OILDATA_DIR,
    "use_main0309_loader": True,
    "cell": "lstm",
    "return_type": "simple",
    "bidirectional": True,
    "stateful": False,
    "units": 64,
    "dropout": 0.1,
    "batch_size": 64,
    "epochs": 20,
    "time_steps": 60,
    "test_percent": 0.08,
    "max_test": 640,
    "price_col": "ClosePrice",
    "scaler_fit": "train",
    "reset_states_before_eval": True,
    "loss": "huber",
    "forecast_next": False,
    "vmd_k": 3,
    "vmd_alpha": 2000.0,
    "vmd_tau": 0.0,
    "vmd_dc": 0,
    "vmd_init": 1,
    "vmd_tol": 1e-7,
    "vmd_drop_high_freq": 1,
    "vmd_drop_mode": "freq",
    "vmd_plot": False,
    "no_plot": False,
    "use_rework_features": True,
    # full: 当前文件内置完整特征；lite: 当前文件内置简化特征
    "rework_feature_mode": "full",
    "rework_script_path": "rework_oil_price_prediction.py",
    "enable_alias_features": False,
    "rf_select_enable": True,
    "rf_top_n": 40,
    "rf_n_estimators": 500,
    "rf_random_state": 42,
    "rf_keep_also_cols": [],
    "shap_refine_enable": True,
    "shap_top_n": 30,
    "shap_max_samples": 256,
    "use_direction_head": True,
    "dir_loss_weight": 5.0,
    "val_ratio": 0.2,
    "rfshap_only": False,
    "rfshap_horizons": "5,20",
    "early_stopping_enable": True,
    "early_stopping_patience": 12,
    "early_stopping_min_delta": 1e-5,
    "save_model_weights": True,
    "weights_output_path": "gru_sequence_weights.weights.h5",
    # Optuna：load_best 优先；从 optuna_best_params_full.json 载入 GRU/VMD 等超参
    "optuna_load_best": True,
    "optuna_enable": False,
    "optuna_quick_basic": False,
    "optuna_quick": False,
    "optuna_n_trials": 40,
    "optuna_seed": 42,
    "optuna_best_path": (
        r"C:\Users\12725\Desktop\大宗绿测_基于油价因子的绿色金融产品预测与风险分析 - 副本"
        r"\技术文档\源代码\crude-oil-price-prediction-master\optuna_best_params_full.json"
    ),
    # Optuna 评分函数权重（当前偏重方向准确率）
    "optuna_score_w_r2": 0.25,
    "optuna_score_w_dir": 0.70,
    "optuna_score_w_rmse": 0.05,
    "learning_rate": 1e-3,
}


def make_default_args() -> SimpleNamespace:
    """集中管理默认参数，避免 main() 配置块过长。"""
    args = SimpleNamespace(**DEFAULT_ARGS)
    # 允许后端通过环境变量覆盖关键运行参数（兼容 Web API 调度）。
    data_base_dir = os.environ.get("WTI_GRU_DATA_BASE_DIR", "").strip()
    if data_base_dir:
        args.data_base_dir = data_base_dir
    output_dir = os.environ.get("WTI_GRU_OUTPUT_DIR", "").strip()
    if output_dir:
        setattr(args, "output_dir", output_dir)
    epochs_env = os.environ.get("WTI_GRU_EPOCHS", "").strip()
    if epochs_env:
        try:
            args.epochs = int(epochs_env)
        except Exception:
            pass
    early_env = os.environ.get("WTI_GRU_ENABLE_EARLY_STOPPING", "").strip()
    if early_env:
        args.early_stopping_enable = early_env not in {"0", "false", "False"}
    forecast_next_env = os.environ.get("WTI_GRU_FORECAST_NEXT", "").strip()
    if forecast_next_env:
        args.forecast_next = forecast_next_env not in {"0", "false", "False"}
    save_weights_env = os.environ.get("WTI_GRU_SAVE_MODEL_WEIGHTS", "").strip()
    if save_weights_env:
        args.save_model_weights = save_weights_env not in {"0", "false", "False"}
    weights_output_env = os.environ.get("WTI_GRU_WEIGHTS_OUTPUT_PATH", "").strip()
    if weights_output_env:
        args.weights_output_path = weights_output_env
    return args


def load_prices_for_pipeline(
    args: SimpleNamespace,
) -> tuple[pd.DataFrame, np.ndarray, object | None]:
    """按配置加载数据，并返回总表、价格列、最后日期。"""
    csv_path = str(args.csv)
    if bool(getattr(args, "use_main0309_loader", True)):
        base_dir = str(getattr(args, "data_base_dir", DEFAULT_OILDATA_DIR))
        if not os.path.isdir(base_dir):
            raise SystemExit(f"数据目录不存在: {base_dir}")
        df_prices = load_multisource_data_like_main0309(base_dir)
        print(f"已按 main_0309 风格加载多源数据: {base_dir}")
    else:
        if not os.path.isfile(csv_path):
            raise SystemExit(f"文件不存在: {csv_path}")
        df_prices = load_price_frame(csv_path, price_col=args.price_col, date_col="Date")

    prices = df_prices[[args.price_col]].values.astype(np.float64)
    last_date = None
    if "Date" in df_prices.columns and len(df_prices) > 0:
        last_date_val = df_prices["Date"].iloc[-1]
        if pd.notna(last_date_val):
            # pandas Timestamp -> python datetime for nicer str()
            last_date = last_date_val.to_pydatetime()
    return df_prices, prices, last_date


def apply_optuna_overrides(
    args: SimpleNamespace, prices: np.ndarray, df_prices: pd.DataFrame
) -> None:
    """应用 Optuna 参数：先载入 JSON，再按最终开关决定是否搜索。"""
    if getattr(args, "optuna_load_best", False):
        best_path = args.optuna_best_path
        if not os.path.isfile(best_path):
            raise SystemExit(f"optuna_load_best=True 但文件不存在: {best_path}")
        try:
            saved = load_saved_runtime_params(best_path)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            raise SystemExit(f"读取 Optuna 保存文件失败: {best_path}\n{e}") from e
        for k, v in saved.items():
            setattr(args, k, v)
        # 回写完整参数集，确保“非强制项都在 JSON 中可见可改”。
        persist_runtime_params(best_path, args)
        # 关键：以“载入后的最终开关”为准，避免默认值提前短路搜索流程。
        if not bool(getattr(args, "optuna_enable", False)):
            print(f"已从 {best_path} 载入运行参数，跳过 Optuna 搜索。")
            return
        print(f"已从 {best_path} 载入运行参数，并按载入配置继续 Optuna 搜索。")

    if not args.optuna_enable:
        return
    # 搜参阶段默认禁用可视化，避免产生大量中间图文件
    args.no_plot = True
    args.vmd_plot = False
    print("Optuna 搜参阶段：已自动禁用绘图输出（no_plot=True, vmd_plot=False）。")
    print(f"Optuna 自动调参开启（trials={args.optuna_n_trials}）...")
    if getattr(args, "optuna_quick_basic", False):
        best_params = run_optuna_quick_basic(prices, df_prices, args)
    else:
        best_params = run_optuna_search(prices, args)
    for k, v in best_params.items():
        setattr(args, k, v)
    persist_runtime_params(args.optuna_best_path, args)
    print("将使用 Optuna 最优参数继续完整训练。")


def main() -> None:
    # -----------------------------
    # 0) 固定默认配置
    # -----------------------------
    # 如果后续你要改默认值，直接改 DEFAULT_ARGS 即可。
    args = make_default_args()
    # 若指定了输出目录，统一把所有产物落到该目录（便于 Web 端按 run 目录读取）。
    output_dir = str(getattr(args, "output_dir", "") or "").strip()
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)
        print(f"[输出目录] {output_dir}")

    # 固定策略：VMD 必用；收益压缩固定为 none（无额外变换）
    force_use_vmd = True
    force_return_compress = "none"
    force_return_compress_scale = 1.0

    # -----------------------------
    # 1) 基础参数与数据读取
    # -----------------------------
    # 读取原始价格与日期（日期用于打印 last_date）
    df_prices, prices, last_date = load_prices_for_pipeline(args)
    vmd_imfs = None
    target_original = None

    def _run_rf_shap_only() -> None:
        if str(getattr(args, "rework_feature_mode", "full")).lower().strip() != "full":
            raise SystemExit("rfshap_only 需要 rework_feature_mode=full（以复用完整多源特征）。")
        feat_df0 = create_rework_full_features(
            df_prices,
            price_col=args.price_col,
            rework_script_path=args.rework_script_path,
            enable_alias_features=bool(getattr(args, "enable_alias_features", False)),
        )
        feat_df0 = feat_df0.select_dtypes(include=[np.number]).copy()
        feat_df0 = feat_df0.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0.0)

        hs_raw = str(getattr(args, "rfshap_horizons", "5,20"))
        horizons: list[int] = []
        for part in hs_raw.replace(";", ",").split(","):
            part = part.strip()
            if part:
                horizons.append(int(part))
        if not horizons:
            horizons = [5, 20]

        for h in horizons:
            y_fwd = price_to_forward_return_series(
                prices, return_type=args.return_type, horizon=h
            ).reshape(-1)
            feat_h = feat_df0.iloc[: len(y_fwd)].copy()

            train_end = int(
                len(y_fwd) * (1.0 - float(getattr(args, "test_percent", 0.08)))
            )
            train_end = max(10, min(train_end, len(y_fwd)))
            print(f"\n[RF+SHAP-only] horizon={h}：样本={len(y_fwd)}，train_end={train_end}")

            rf_plot = f"rf_feature_importance_h{h}.png"
            shap_plot = f"shap_feature_importance_h{h}.png"
            out_json = f"rf_shap_selected_features_h{h}.json"

            feat_sel, rf_cols = rf_select_top_n_features(
                feat_h,
                y=y_fwd,
                train_end_exclusive=train_end,
                top_n=int(args.rf_top_n),
                n_estimators=int(args.rf_n_estimators),
                random_state=int(args.rf_random_state),
                keep_also_cols=list(getattr(args, "rf_keep_also_cols", [])),
                plot_path=rf_plot,
            )
            print(f"[RF+SHAP-only] RF Top-{len(rf_cols)} 已保存图: {rf_plot}")

            if bool(getattr(args, "shap_refine_enable", True)) and rf_cols:
                feat_sel, shap_cols = shap_refine_feature_columns(
                    feat_sel,
                    rf_cols,
                    y=y_fwd,
                    train_end_exclusive=train_end,
                    shap_top_n=int(getattr(args, "shap_top_n", 30)),
                    n_estimators=int(args.rf_n_estimators),
                    random_state=int(args.rf_random_state),
                    max_shap_samples=int(getattr(args, "shap_max_samples", 256)),
                    plot_path=shap_plot,
                )
                print(f"[RF+SHAP-only] SHAP Top-{len(shap_cols)} 已保存图: {shap_plot}")
            else:
                shap_cols = rf_cols

            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "horizon": h,
                        "return_type": args.return_type,
                        "n_samples": int(len(y_fwd)),
                        "train_end_exclusive": int(train_end),
                        "rf_top_n": int(args.rf_top_n),
                        "shap_top_n": int(getattr(args, "shap_top_n", 30)),
                        "rf_selected": list(rf_cols),
                        "shap_selected": list(shap_cols),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            print(f"[RF+SHAP-only] 已写出特征清单: {out_json}")

        print("\n[RF+SHAP-only] 完成。未训练 GRU，也未输出预测结果。")
    # -----------------------------
    # 2) Optuna：从 JSON 加载最优参数，或在线搜索（加载优先于搜索）
    # -----------------------------
    apply_optuna_overrides(args, prices, df_prices)

    batch_size = args.batch_size
    epochs = args.epochs
    time_steps = args.time_steps
    if bool(getattr(args, "rfshap_only", False)):
        _run_rf_shap_only()
        return
    print(
        "最终生效训练参数: "
        f"epochs={epochs}, batch_size={batch_size}, time_steps={time_steps}, "
        f"cell={args.cell}, loss={args.loss}, lr={args.learning_rate}"
    )
    print(
        "特征筛选开关: "
        f"rf_select_enable={bool(getattr(args, 'rf_select_enable', False))}, "
        f"shap_refine_enable={bool(getattr(args, 'shap_refine_enable', False))}, "
        f"shap_top_n={int(getattr(args, 'shap_top_n', 0))}"
    )
    # 全局 VMD 健康检查
    if force_use_vmd:
        if args.vmd_drop_high_freq >= args.vmd_k:
            raise SystemExit(
                "vmd_drop_high_freq 过大：不能 >= vmd_k。"
                f"当前 vmd_k={args.vmd_k}, vmd_drop_high_freq={args.vmd_drop_high_freq}。"
            )
    print(
        f"滑动窗口长度 time_steps = {time_steps}："
        f"每个 x 为过去 {time_steps} 个点，形状 ({time_steps}, 1)；"
        f"单点预测 horizon=1（下一天）。"
    )
    print(
        f"当前 RNN 单元: {args.cell.upper()}，"
        f"{'双向' if args.bidirectional else '单向'}"
    )

    raw_returns = price_to_return_series(prices, return_type=args.return_type)
    training_set = compress_returns(
        raw_returns,
        method=force_return_compress,
        scale=force_return_compress_scale,
    )
    ret_std0 = float(np.nanstd(training_set))
    print(f"原始收益统计: std={ret_std0:.8e}")
    if not np.isfinite(ret_std0) or ret_std0 < 1e-10:
        raise SystemExit(
            "收益序列几乎为常数（std≈0），流程异常。请检查多源数据合并与日期去重。"
        )
    n = len(training_set)
    print(f"样本行数（有效数值）: {n}")

    length = get_train_length(n, batch_size, args.test_percent, verbose=True)
    print("选用的训练截止 length =", length)

    if force_use_vmd:
        target_original = training_set.copy()
        # 全局 VMD：对整段序列做 VMD（会引入未来信息，指标可能偏乐观；按你的要求启用）
        training_set, vmd_imfs = apply_vmd_on_target(
            training_set,
            k=args.vmd_k,
            alpha=args.vmd_alpha,
            tau=args.vmd_tau,
            dc=args.vmd_dc,
            init=args.vmd_init,
            tol=args.vmd_tol,
            drop_high_freq=args.vmd_drop_high_freq,
            drop_mode=args.vmd_drop_mode,
        )
        # VMD 输出长度可能与输入有 1 个点偏差，这里统一刷新 n / length，避免后续特征对齐出错
        if len(training_set) != n:
            n = len(training_set)
            length = min(length, n)
        if target_original.shape[0] != training_set.shape[0]:
            target_original = target_original[: training_set.shape[0]]
        print(
            f"VMD 已启用: K={args.vmd_k}, drop_high_freq={args.vmd_drop_high_freq}；"
            "全局 VMD 已应用到整条收益标签后再做滑窗。"
        )
    ret_std1 = float(np.nanstd(training_set))
    print(f"VMD 后收益统计: std={ret_std1:.8e}")
    if not np.isfinite(ret_std1) or ret_std1 < 1e-10:
        raise SystemExit(
            "VMD 后收益序列几乎为常数（std≈0）。请调小 vmd_alpha 或检查输入数据质量。"
        )
    print(f"目标: 收益率（{args.return_type}），压缩: none（固定）")
    # 按时间顺序划分训练/测试（非随机打散）
    print(
        "数据集划分：时间序列先后 — "
        f"窗终点行下标 i ∈ [{time_steps}, {length - 2}] 为训练窗；"
        f"i ∈ [{length - 1}, {n - 2}] 为测试窗（再截断到 --max-test 并对齐 batch）。"
        " 仅说明划分区间；实际 scaler 是否全量 fit 由 scaler_fit 控制。"
    )

    # -----------------------------
    # 4) 标签标准化
    # -----------------------------
    # 收益标签默认用 StandardScaler（更稳）
    sc: object = StandardScaler(with_mean=True, with_std=True)
    scaler_name = "StandardScaler"
    if args.scaler_fit == "all":
        training_set_scaled = sc.fit_transform(training_set)
        print("Scaler: fit=全量（可能泄露测试段统计信息）")
    else:
        sc.fit(training_set[:length])
        training_set_scaled = sc.transform(training_set)
        print("Scaler: fit=仅训练段（严格评估，避免泄露）")
    print(f"Scaler 类型: {scaler_name}")
    feat_mat = None
    if args.use_rework_features:
        if str(getattr(args, "rework_feature_mode", "full")).lower().strip() == "full":
            try:
                feat_df = create_rework_full_features(
                    df_prices,
                    price_col=args.price_col,
                    rework_script_path=args.rework_script_path,
                    enable_alias_features=bool(getattr(args, "enable_alias_features", False)),
                )
                print("已加载本文件内置完整特征工程（full）。")
            except Exception as e:
                print(f"[警告] 内置 full 特征工程构建失败，回退到 lite 特征：{e}")
                feat_df = create_rework_style_features(df_prices, price_col=args.price_col)
        else:
            feat_df = create_rework_style_features(df_prices, price_col=args.price_col)
        # 收益序列从第 2 行开始，特征也按同样偏移对齐
        feat_df = feat_df.iloc[1:].copy()
        # 统一以标签长度 n 为准截断，避免 VMD 对齐造成的 1 点偏差
        if len(feat_df) != n:
            min_n = min(len(feat_df), n)
            feat_df = feat_df.iloc[:min_n].copy()
            training_set_scaled = training_set_scaled[:min_n]
            training_set = training_set[:min_n]
            n = min_n
            length = min(length, n)

        # 随机森林 Top-N，再用 SHAP(mean|value|) 精炼子集
        selected_cols: list[str] | None = None
        use_multi = bool(getattr(args, "use_direction_head", True))
        if getattr(args, "rf_select_enable", False):
            total_feat_cnt = int(feat_df.shape[1])
            if int(args.rf_top_n) >= total_feat_cnt:
                print(
                    f"[提示] rf_top_n={args.rf_top_n} >= 特征总数={total_feat_cnt}，"
                    "RF 粗筛将保留全部数值列。"
                )
            feat_df, selected_cols = rf_select_top_n_features(
                feat_df,
                y=training_set.reshape(-1),
                train_end_exclusive=length,
                top_n=int(args.rf_top_n),
                n_estimators=int(args.rf_n_estimators),
                random_state=int(args.rf_random_state),
                keep_also_cols=list(getattr(args, "rf_keep_also_cols", [])),
                plot_path=(None if bool(getattr(args, "no_plot", False)) else "rf_feature_importance.png"),
            )
            print(
                f"RF 特征筛选已启用：Top-{len(selected_cols)} / {total_feat_cnt}"
            )
            print("RF 选中特征（前 30 展示）:", selected_cols[:30])
            if not bool(getattr(args, "no_plot", False)):
                print("RF 特征重要性图已保存: rf_feature_importance.png")
            if getattr(args, "shap_refine_enable", False) and selected_cols:
                before_n = len(selected_cols)
                feat_df, selected_cols = shap_refine_feature_columns(
                    feat_df,
                    selected_cols,
                    y=training_set.reshape(-1),
                    train_end_exclusive=length,
                    shap_top_n=int(getattr(args, "shap_top_n", 30)),
                    n_estimators=int(args.rf_n_estimators),
                    random_state=int(args.rf_random_state),
                    max_shap_samples=int(getattr(args, "shap_max_samples", 512)),
                    plot_path=(None if bool(getattr(args, "no_plot", False)) else "shap_feature_importance.png"),
                )
                print(
                    f"SHAP 精炼：自 RF Top-{before_n} 保留 {len(selected_cols)} 列 "
                    f"(shap_top_n={getattr(args, 'shap_top_n', 30)})"
                )
                print("SHAP 最终特征（前 30 展示）:", selected_cols[:30])
                if not bool(getattr(args, "no_plot", False)):
                    print("SHAP 重要性图已保存: shap_feature_importance.png")

        # 打印最终用于训练的特征清单（完整）
        final_feature_cols = list(feat_df.columns)
        print(f"最终训练特征总数: {len(final_feature_cols)}")
        print("最终训练特征列表（完整）:")
        for i, c in enumerate(final_feature_cols, start=1):
            print(f"[{i:03d}] {c}")

        feat_mat = feat_df.values.astype(np.float64)
        sc_x = StandardScaler(with_mean=True, with_std=True)
        sc_x.fit(feat_mat[:length])
        feat_scaled = sc_x.transform(feat_mat)
        if use_multi:
            (
                xtrain,
                ytrain,
                ydir_train,
                xtest,
                ytest,
                ydir_test,
                test_end_i,
            ) = build_windows_from_features_with_direction(
                feat_scaled,
                training_set_scaled,
                training_set,
                time_steps=time_steps,
                length=length,
                max_test_window=args.max_test,
            )
        else:
            ydir_train = ydir_test = None
            xtrain, ytrain, xtest, ytest, test_end_i = build_windows_from_features(
                feat_scaled,
                training_set_scaled,
                time_steps=time_steps,
                length=length,
                max_test_window=args.max_test,
            )
        print(f"已启用 rework 特征工程输入，特征维度={feat_scaled.shape[1]}")
    else:
        use_multi = False
        ydir_train = ydir_test = None
        feat_scaled = None
        xtrain, ytrain, xtest, ytest, test_end_i = build_windows(
            training_set_scaled,
            raw_len=n,
            time_steps=time_steps,
            length=length,
            max_test_window=args.max_test,
        )

    if use_multi and ydir_train is not None and ydir_test is not None:
        xtrain, ytrain, ydir_train = trim_to_batch_multi(
            xtrain, ytrain, ydir_train, batch_size
        )
        xtest, ytest, ydir_test = trim_to_batch_multi(
            xtest, ytest, ydir_test, batch_size
        )
    else:
        xtrain, ytrain = trim_to_batch(xtrain, ytrain, batch_size)
        xtest, ytest = trim_to_batch(xtest, ytest, batch_size)
    test_k = test_end_i[: len(xtest)]

    print("xtrain", xtrain.shape, "ytrain", ytrain.shape)
    print("xtest", xtest.shape, "ytest", ytest.shape)
    if use_multi and ydir_train is not None:
        print("ydir_train", ydir_train.shape, "（方向头：1=涨,0=跌）")

    if len(xtrain) == 0 or len(xtest) == 0:
        raise SystemExit(
            "训练或测试样本数为 0。数据太短或 batch_size 过大，请把 --batch-size 改小（如 16）。"
        )

    # 时间序列验证集：从训练尾部切分，专用于输出 val_loss / val 指标
    val_ratio = float(getattr(args, "val_ratio", 0.2))
    val_ratio = min(max(val_ratio, 0.0), 0.5)
    val_n = int(len(xtrain) * val_ratio)
    val_n = (val_n // batch_size) * batch_size
    has_val = val_n >= batch_size
    if has_val:
        split = len(xtrain) - val_n
        xtr, xval = xtrain[:split], xtrain[split:]
        ytr, yval = ytrain[:split], ytrain[split:]
        if use_multi and ydir_train is not None:
            ydir_tr, ydir_val = ydir_train[:split], ydir_train[split:]
        else:
            ydir_tr = ydir_val = None
        print(
            f"验证集切分完成：train={len(xtr)}, val={len(xval)} (val_ratio={val_ratio:.2f})"
        )
    else:
        xtr, ytr = xtrain, ytrain
        xval = yval = None
        ydir_tr = ydir_train if (use_multi and ydir_train is not None) else None
        ydir_val = None
        print("验证集切分跳过：样本不足（仅输出 train loss）")

    callbacks = []
    if bool(getattr(args, "early_stopping_enable", True)):
        monitor = "val_loss" if has_val else "loss"
        es = EarlyStopping(
            monitor=monitor,
            patience=int(getattr(args, "early_stopping_patience", 12)),
            min_delta=float(getattr(args, "early_stopping_min_delta", 1e-5)),
            mode="min",
            restore_best_weights=True,
            verbose=1,
        )
        callbacks.append(es)
        print(
            f"EarlyStopping 已启用: monitor={monitor}, "
            f"patience={int(getattr(args, 'early_stopping_patience', 12))}, "
            f"min_delta={float(getattr(args, 'early_stopping_min_delta', 1e-5))}"
        )

    # -----------------------------
    # 5) 建模与训练
    # -----------------------------
    if use_multi:
        model = build_sequence_model_multi(
            args.cell,
            batch_size,
            time_steps,
            n_features=xtrain.shape[-1],
            bidirectional=args.bidirectional,
            stateful=args.stateful,
            units=args.units,
            dropout=args.dropout,
        )
        if args.loss == "huber":
            loss_fn = Huber()
        else:
            loss_fn = args.loss
        dw = float(getattr(args, "dir_loss_weight", 5.0))
        model.compile(
            optimizer=Adam(learning_rate=args.learning_rate),
            loss={"return": loss_fn, "dir": "binary_crossentropy"},
            loss_weights={"return": 1.0, "dir": dw},
            metrics={"dir": BinaryAccuracy(name="dir_acc")},
        )
        print(
            f"双头模型：收益回归 + 方向二分类；loss_weights return=1.0, dir={dw}（方向权更大）"
        )
    else:
        model = build_sequence_model(
            args.cell,
            batch_size,
            time_steps,
            n_features=xtrain.shape[-1],
            bidirectional=args.bidirectional,
            stateful=args.stateful,
            units=args.units,
            dropout=args.dropout,
        )
        if args.loss == "huber":
            loss_fn = Huber()
        else:
            loss_fn = args.loss
        model.compile(optimizer=Adam(learning_rate=args.learning_rate), loss=loss_fn)
    model.summary()

    if use_multi and ydir_tr is not None:
        fit_kwargs = {}
        if has_val and xval is not None and yval is not None and ydir_val is not None:
            fit_kwargs["validation_data"] = (xval, {"return": yval, "dir": ydir_val})
        history = model.fit(
            xtr,
            {"return": ytr, "dir": ydir_tr},
            shuffle=not args.stateful,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=callbacks,
            **fit_kwargs,
        )
    else:
        fit_kwargs = {}
        if has_val and xval is not None and yval is not None:
            fit_kwargs["validation_data"] = (xval, yval)
        history = model.fit(
            xtr,
            ytr,
            shuffle=not args.stateful,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=callbacks,
            **fit_kwargs,
        )

    if args.stateful and args.reset_states_before_eval:
        model.reset_states()
        print("已 reset RNN states（评估前）")
    elif args.stateful:
        print("未 reset RNN states（评估前）：stateful 状态可能从训练段带入测试段")

    if bool(getattr(args, "save_model_weights", False)):
        weights_path = str(getattr(args, "weights_output_path", "gru_sequence_weights.weights.h5"))
        model.save_weights(weights_path)
        print(f"模型权重已保存: {weights_path}")

    # -----------------------------
    # 6) 测试集评估
    # -----------------------------
    raw_pred = model.predict(xtest, batch_size=batch_size, verbose=0)
    if use_multi:
        per = np.asarray(raw_pred[0], dtype=np.float64)
        per_dir = np.asarray(raw_pred[1], dtype=np.float64).reshape(-1, 1)
    else:
        per = np.asarray(raw_pred, dtype=np.float64)
        per_dir = None
    p = sc.inverse_transform(per.reshape(-1, 1))
    y = sc.inverse_transform(ytest.reshape(-1, 1))
    # 这里固定为收益任务；当前压缩为 none，decompress 等价直通
    p = decompress_returns(
        p,
        method=force_return_compress,
        scale=force_return_compress_scale,
    )
    y = decompress_returns(
        y,
        method=force_return_compress,
        scale=force_return_compress_scale,
    )

    diff = (p - y).ravel()
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff**2)))
    print(f"测试集 MAE（horizon=1）: {mae:.6f}")
    print(f"测试集 RMSE（horizon=1）: {rmse:.6f}")

    r2 = float(r2_score(y, p))
    print(f"测试集 R²（horizon=1）: {r2:.4f}")

    # 方向：收益本身的正负
    dir_acc = directional_accuracy(y, p, exclude_flat_true=True)
    dir_acc_all = directional_accuracy(y, p, exclude_flat_true=False)
    print(
        "测试集 方向一致性（收益正负符号一致率，排除真实=0）: "
        f"{dir_acc:.4f}"
        + (f"（含真实=0: {dir_acc_all:.4f}）" if not np.isnan(dir_acc_all) else "")
    )
    if use_multi and per_dir is not None and ydir_test is not None:
        pred_cls = (per_dir.ravel() >= 0.5).astype(np.int32)
        true_cls = ydir_test.ravel().astype(np.int32)
        acc_dir_head = float(accuracy_score(true_cls, pred_cls))
        print(f"测试集 方向头分类准确率（sigmoid≥0.5）: {acc_dir_head:.4f}")
        p_dir = np.clip(per_dir.ravel().astype(np.float64), 1e-7, 1 - 1e-7)
        cls_precision = float(
            precision_score(true_cls, pred_cls, zero_division=0)
        )
        cls_recall = float(recall_score(true_cls, pred_cls, zero_division=0))
        cls_f1 = float(f1_score(true_cls, pred_cls, zero_division=0))
        print(
            "方向头分类指标: "
            f"Precision={cls_precision:.4f}, Recall={cls_recall:.4f}, F1={cls_f1:.4f}"
        )
        if len(np.unique(true_cls)) > 1:
            auc = float(roc_auc_score(true_cls, p_dir))
            print(f"方向头 ROC-AUC（测试集）: {auc:.4f}")
        cm = confusion_matrix(true_cls, pred_cls, labels=[0, 1])
        print(
            "方向头混淆矩阵 [[TN, FP], [FN, TP]]: "
            f"{cm.tolist()}"
        )
    else:
        pred_cls = true_cls = cm = None

    # 补充“收益还原到价格尺度”的 R²，便于和价格指标对齐
    k = test_k
    if np.any(k < 0) or np.any(k >= len(prices) - 1):
        raise RuntimeError("收益到价格还原索引越界：请检查窗口/切分逻辑。")
    base_price = prices[k].reshape(-1, 1)  # prices[k] 是该收益对应的上一日价格

    if args.return_type == "log":
        p_price = base_price * np.exp(p)
        y_price = base_price * np.exp(y)
    else:
        p_price = base_price * (1.0 + p)
        y_price = base_price * (1.0 + y)

    r2_price = float(r2_score(y_price, p_price))
    mape_price = float(
        np.mean(np.abs((y_price - p_price) / np.maximum(np.abs(y_price), 1e-8))) * 100.0
    )
    mae_price = float(np.mean(np.abs(y_price - p_price)))
    rmse_price = float(np.sqrt(np.mean((y_price - p_price) ** 2)))
    print(f"测试集 R²（收益还原为价格后，horizon=1）: {r2_price:.6f}")
    print(
        f"测试集 价格指标: MAE={mae_price:.4f}, RMSE={rmse_price:.4f}, MAPE={mape_price:.2f}%"
    )

    # 基线对照（与 rework 对齐）：远期收益=0（随机游走）、AR(1) 与收益均值
    y_flat = y.reshape(-1)
    y_rw = np.zeros_like(y_flat)
    r2_ret_rw = float(r2_score(y_flat, y_rw))
    print(f"Baseline(远期对数收益=0，随机游走) 在收益上的 R2: {r2_ret_rw:.4f}")

    train_ret = training_set[:length].reshape(-1)
    if len(train_ret) >= 3:
        x_ar = train_ret[:-1]
        y_ar = train_ret[1:]
        denom = float(np.dot(x_ar, x_ar)) + 1e-12
        phi = float(np.dot(x_ar, y_ar) / denom)
        mu_tr = float(np.mean(train_ret))
        prev_idx = np.clip(k - 1, 0, len(training_set) - 1)
        prev_ret = training_set[prev_idx].reshape(-1)
        pred_ar1 = phi * prev_ret
        pred_mean = np.full_like(y_flat, mu_tr, dtype=np.float64)
        r2_ret_ar1 = float(r2_score(y_flat, pred_ar1))
        r2_ret_mean = float(r2_score(y_flat, pred_mean))
        print(f"Baseline(AR(1) on returns) R2_ret: {r2_ret_ar1:.4f}  (phi={phi:.3f})")
        print(f"Baseline(收益均值) R2_ret: {r2_ret_mean:.4f}  (mu={mu_tr:.6f})")

    # -----------------------------
    # 7) 结果页图表 CSV 导出（前端可直接绘图）
    # -----------------------------
    losses = history.history.get("loss", [])
    val_losses = history.history.get("val_loss", [])
    epochs_x = np.arange(1, len(losses) + 1)

    pd.DataFrame(
        {
            "test_index": np.arange(len(y)),
            "actual_return": y.reshape(-1),
            "pred_return": p.reshape(-1),
            "actual_price": y_price.reshape(-1),
            "pred_price": p_price.reshape(-1),
        }
    ).to_csv("chart_test_predictions.csv", index=False, encoding="utf-8-sig")
    print("结果图表CSV已保存: chart_test_predictions.csv")

    pd.DataFrame(
        {
            "epoch": epochs_x,
            "train_loss": np.asarray(losses, dtype=np.float64),
            "val_loss": (
                np.asarray(val_losses, dtype=np.float64)
                if len(val_losses) == len(losses) and len(val_losses) > 0
                else np.full(len(losses), np.nan, dtype=np.float64)
            ),
        }
    ).to_csv("chart_train_val_loss.csv", index=False, encoding="utf-8-sig")
    print("结果图表CSV已保存: chart_train_val_loss.csv")

    residuals = (y - p).ravel()
    pd.DataFrame({"residual": residuals}).to_csv(
        "chart_residual_distribution.csv", index=False, encoding="utf-8-sig"
    )
    print("结果图表CSV已保存: chart_residual_distribution.csv")

    pd.DataFrame({"y_true": y.reshape(-1), "y_pred": p.reshape(-1)}).to_csv(
        "chart_return_scatter.csv", index=False, encoding="utf-8-sig"
    )
    print("结果图表CSV已保存: chart_return_scatter.csv")

    strat_signal = np.sign(p.reshape(-1))
    strat_ret = strat_signal * y.reshape(-1)
    bh_ret = y.reshape(-1)
    strat_nav = np.cumprod(1.0 + strat_ret)
    bh_nav = np.cumprod(1.0 + bh_ret)
    pd.DataFrame(
        {
            "test_index": np.arange(len(strat_nav)),
            "strategy_nav": strat_nav,
            "buy_hold_nav": bh_nav,
            "strategy_return": strat_ret,
            "buy_hold_return": bh_ret,
            "signal": strat_signal,
        }
    ).to_csv("chart_backtest_nav_curve.csv", index=False, encoding="utf-8-sig")
    print("结果图表CSV已保存: chart_backtest_nav_curve.csv")

    if use_multi and per_dir is not None and ydir_test is not None:
        true_dir = ydir_test.ravel().astype(np.int32)
        pred_dir = (per_dir.ravel() >= 0.5).astype(np.int32)
        pd.DataFrame(
            {
                "test_index": np.arange(len(true_dir)),
                "true_direction": true_dir,
                "pred_direction": pred_dir,
                "pred_prob_up": per_dir.ravel(),
            }
        ).to_csv("chart_direction_prediction.csv", index=False, encoding="utf-8-sig")
        print("结果图表CSV已保存: chart_direction_prediction.csv")

        if cm is not None:
            pd.DataFrame(
                [
                    {"true_label": "down", "pred_label": "down", "count": int(cm[0, 0])},
                    {"true_label": "down", "pred_label": "up", "count": int(cm[0, 1])},
                    {"true_label": "up", "pred_label": "down", "count": int(cm[1, 0])},
                    {"true_label": "up", "pred_label": "up", "count": int(cm[1, 1])},
                ]
            ).to_csv("chart_direction_confusion_matrix.csv", index=False, encoding="utf-8-sig")
            print("结果图表CSV已保存: chart_direction_confusion_matrix.csv")

        pd.DataFrame({"pred_prob_up": per_dir.ravel()}).to_csv(
            "chart_direction_prob_distribution.csv", index=False, encoding="utf-8-sig"
        )
        print("结果图表CSV已保存: chart_direction_prob_distribution.csv")

    n_cmp = min(len(raw_returns), len(training_set), len(training_set_scaled))
    if n_cmp > 0:
        pd.DataFrame(
            {
                "sample_index": np.arange(n_cmp),
                "raw_returns": raw_returns[:n_cmp].ravel(),
                "training_returns": training_set[:n_cmp].ravel(),
                "scaled_returns": training_set_scaled[:n_cmp].ravel(),
            }
        ).to_csv("chart_preprocess_before_after_returns.csv", index=False, encoding="utf-8-sig")
        print("结果图表CSV已保存: chart_preprocess_before_after_returns.csv")

    if feat_mat is not None and feat_scaled is not None and feat_mat.shape[1] > 0:
        m = min(len(feat_mat), len(feat_scaled))
        pd.DataFrame(
            {
                "sample_index": np.arange(m),
                "raw_feature_0": feat_mat[:m, 0],
                "scaled_feature_0": feat_scaled[:m, 0],
            }
        ).to_csv("chart_preprocess_feature_compare.csv", index=False, encoding="utf-8-sig")
        print("结果图表CSV已保存: chart_preprocess_feature_compare.csv")

    if target_original is not None and training_set is not None:
        n_v = min(len(target_original), len(training_set))
        pd.DataFrame(
            {
                "sample_index": np.arange(n_v),
                "before_vmd_return": target_original[:n_v].ravel(),
                "after_vmd_return": training_set[:n_v].ravel(),
            }
        ).to_csv("chart_vmd_before_after.csv", index=False, encoding="utf-8-sig")
        print("结果图表CSV已保存: chart_vmd_before_after.csv")

    if args.forecast_next:
        # -----------------------------
        # 7) 下一天预测（最后窗口）
        # -----------------------------
        fc = predict_next_day(
            trained_model=model,
            cell=args.cell,
            bidirectional=args.bidirectional,
            stateful=args.stateful,
            units=args.units,
            dropout=args.dropout,
            time_steps=time_steps,
            n_features=xtrain.shape[-1],
            use_window_vmd=False,
            vmd_k=args.vmd_k,
            vmd_alpha=args.vmd_alpha,
            vmd_tau=args.vmd_tau,
            vmd_dc=args.vmd_dc,
            vmd_init=args.vmd_init,
            vmd_tol=args.vmd_tol,
            vmd_drop_high_freq=args.vmd_drop_high_freq,
            vmd_drop_mode=args.vmd_drop_mode,
            sc=sc,
            scaled_series=(training_set_scaled if xtrain.shape[-1] == 1 else feat_scaled),
            return_type=args.return_type,
            prices=prices,
            last_date=last_date,
            multi_head=use_multi,
        )
        last_date_str = (
            f"last_date={fc['last_date']}，" if fc.get("last_date") is not None else ""
        )
        prob_str = ""
        if use_multi and fc.get("pred_prob_up") is not None:
            prob_str = f"，pred_prob_up={float(fc['pred_prob_up']):.4f}"
        msg = (
            "下一天预测："
            + last_date_str
            + f"pred_return={float(fc['pred_return']):.6f}，"
            + f"last_price={float(fc['last_price']):.4f}，"
            + f"pred_price={float(fc['pred_price']):.4f}"
            + prob_str
        )
        print(msg)

    if (not args.no_plot) or args.vmd_plot:
        # -----------------------------
        # 8) 可视化
        # -----------------------------
        import matplotlib.pyplot as plt

        # 预处理前后对比图（收益）
        n_cmp = min(len(raw_returns), len(training_set), len(training_set_scaled))
        if n_cmp > 0:
            t_cmp = np.arange(n_cmp)
            fig_pre, axes_pre = plt.subplots(3, 1, figsize=(12, 8), constrained_layout=True)
            axes_pre[0].plot(t_cmp, raw_returns[:n_cmp].ravel(), color="tab:blue", linewidth=0.9)
            axes_pre[0].set_title("预处理前：原始收益序列")
            axes_pre[1].plot(t_cmp, training_set[:n_cmp].ravel(), color="tab:green", linewidth=0.9)
            axes_pre[1].set_title("预处理后：用于训练的收益序列（含 VMD/对齐）")
            axes_pre[2].plot(t_cmp, training_set_scaled[:n_cmp].ravel(), color="tab:orange", linewidth=0.9)
            axes_pre[2].set_title("预处理后：标准化收益序列（Scaler 输出）")
            axes_pre[2].set_xlabel("样本索引")
            fig_pre.savefig("preprocess_before_after_returns.png", dpi=180, bbox_inches="tight")
            print("预处理前后（收益）图已保存: preprocess_before_after_returns.png")

            fig_hist, ax_hist = plt.subplots(1, 1, figsize=(10, 4), constrained_layout=True)
            ax_hist.hist(raw_returns[:n_cmp].ravel(), bins=60, alpha=0.55, label="raw_returns", color="tab:blue")
            ax_hist.hist(
                training_set_scaled[:n_cmp].ravel(),
                bins=60,
                alpha=0.55,
                label="scaled_returns",
                color="tab:orange",
            )
            ax_hist.set_title("预处理前后分布对比（收益）")
            ax_hist.set_xlabel("数值")
            ax_hist.set_ylabel("频次")
            ax_hist.legend(loc="best")
            fig_hist.savefig("preprocess_distribution_compare.png", dpi=180, bbox_inches="tight")
            print("预处理分布对比图已保存: preprocess_distribution_compare.png")

        # 预处理前后对比图（首个特征，若启用多特征）
        if feat_mat is not None and feat_scaled is not None and feat_mat.shape[1] > 0:
            fig_fx, ax_fx = plt.subplots(1, 1, figsize=(12, 4), constrained_layout=True)
            m = min(len(feat_mat), len(feat_scaled))
            t_f = np.arange(m)
            ax_fx.plot(t_f, feat_mat[:m, 0], label="raw_feature_0", linewidth=0.9, color="tab:blue")
            ax_fx.plot(t_f, feat_scaled[:m, 0], label="scaled_feature_0", linewidth=0.9, color="tab:orange", alpha=0.85)
            ax_fx.set_title("特征预处理前后对比（第1个特征）")
            ax_fx.set_xlabel("样本索引")
            ax_fx.set_ylabel("值")
            ax_fx.legend(loc="best")
            fig_fx.savefig("preprocess_feature_compare.png", dpi=180, bbox_inches="tight")
            print("特征预处理前后图已保存: preprocess_feature_compare.png")

        # VMD 前后对比图（标签序列）
        if target_original is not None and training_set is not None:
            n_v = min(len(target_original), len(training_set))
            fig_vmd_ba, ax_vmd_ba = plt.subplots(1, 1, figsize=(12, 4), constrained_layout=True)
            t_v2 = np.arange(n_v)
            ax_vmd_ba.plot(
                t_v2,
                target_original[:n_v].ravel(),
                label="VMD 前（原始收益）",
                color="tab:blue",
                linewidth=0.9,
            )
            ax_vmd_ba.plot(
                t_v2,
                training_set[:n_v].ravel(),
                label="VMD 后（重构收益）",
                color="tab:green",
                linewidth=0.9,
                alpha=0.9,
            )
            ax_vmd_ba.set_title("VMD 前后标签序列对比")
            ax_vmd_ba.set_xlabel("样本索引")
            ax_vmd_ba.set_ylabel("收益")
            ax_vmd_ba.legend(loc="best")
            fig_vmd_ba.savefig("vmd_before_after.png", dpi=180, bbox_inches="tight")
            print("VMD 前后对比图已保存: vmd_before_after.png")

        if args.vmd_plot and vmd_imfs is not None and target_original is not None:
            n_imf = vmd_imfs.shape[0]
            fig_vmd, axes_vmd = plt.subplots(
                n_imf + 2,
                1,
                figsize=(12, 2.0 * (n_imf + 2)),
                constrained_layout=True,
            )
            t_v = np.arange(len(target_original))
            t_imf = np.arange(vmd_imfs.shape[1])
            axes_vmd[0].plot(t_v, target_original.ravel(), color="black", linewidth=0.9)
            axes_vmd[0].set_title("VMD 分解：原始标签序列（全段）")
            for i in range(n_imf):
                axes_vmd[i + 1].plot(t_imf, vmd_imfs[i], linewidth=0.9)
                axes_vmd[i + 1].set_title(f"IMF {i + 1}（仅训练前缀长度 {len(t_imf)}）")
            axes_vmd[-1].plot(t_v, training_set.ravel(), color="tab:green", linewidth=0.9)
            axes_vmd[-1].set_title("VMD 重构标签（用于训练）")
            axes_vmd[-1].set_xlabel("样本索引")

            fig_vmd.savefig("vmd_decomposition.png", dpi=150)
            print("VMD 分解图已保存: vmd_decomposition.png")

        if args.no_plot and args.vmd_plot:
            plt.show()
            return
        if args.no_plot and not args.vmd_plot:
            return

        fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)

        ax_y = axes[0]
        t = np.arange(len(y))
        label_unit = "收益率"
        ax_y.plot(t, y.ravel(), label=f"真实{label_unit}", color="tab:blue", linewidth=1.1)
        ax_y.plot(
            t,
            p.ravel(),
            label=f"预测{label_unit}",
            color="tab:orange",
            linewidth=1.0,
            alpha=0.92,
        )
        ax_y.set_title("测试集：真实 vs 预测（horizon=1，逆变换后）")
        ax_y.set_xlabel("测试窗索引")
        ax_y.set_ylabel(label_unit)
        ax_y.legend(loc="best")

        ax_loss = axes[1]
        losses = history.history.get("loss", [])
        val_losses = history.history.get("val_loss", [])
        epochs_x = np.arange(1, len(losses) + 1)
        ax_loss.plot(
            epochs_x,
            losses,
            color="tab:green",
            linewidth=1.2,
            marker="o",
            markersize=4,
            label="train_loss",
        )
        if len(val_losses) == len(losses) and len(val_losses) > 0:
            ax_loss.plot(
                epochs_x,
                val_losses,
                color="tab:red",
                linewidth=1.2,
                marker="s",
                markersize=3,
                label="val_loss",
            )
        loss_title = (
            "训练/验证总损失曲线（双头为加权总损失）"
            if len(val_losses) > 0
            else "训练总损失曲线"
        )
        ax_loss.set_title(loss_title)
        ax_loss.set_xlabel("Epoch")
        ax_loss.set_ylabel("Loss")
        ax_loss.grid(True, alpha=0.3)
        ax_loss.legend(loc="best")

        fig.savefig("gru_returns.png", dpi=180, bbox_inches="tight")
        print("收益与训练损失图已保存: gru_returns.png")

        # 单独输出 train/val loss 图（便于汇报）
        fig_loss, ax_loss2 = plt.subplots(1, 1, figsize=(10, 4), constrained_layout=True)
        ax_loss2.plot(epochs_x, losses, label="train_loss", color="tab:green", linewidth=1.2)
        if len(val_losses) == len(losses) and len(val_losses) > 0:
            ax_loss2.plot(epochs_x, val_losses, label="val_loss", color="tab:red", linewidth=1.2)
        ax_loss2.set_title("Train vs Validation Loss")
        ax_loss2.set_xlabel("Epoch")
        ax_loss2.set_ylabel("Loss")
        ax_loss2.grid(True, alpha=0.3)
        ax_loss2.legend(loc="best")
        fig_loss.savefig("train_val_loss.png", dpi=180, bbox_inches="tight")
        print("训练/验证 loss 图已保存: train_val_loss.png")

        # 价格对比图
        fig_price, ax_price = plt.subplots(1, 1, figsize=(11, 4), constrained_layout=True)
        t_price = np.arange(len(y_price))
        ax_price.plot(t_price, y_price.ravel(), label="真实价格", color="tab:blue", linewidth=1.1)
        ax_price.plot(
            t_price,
            p_price.ravel(),
            label="预测价格",
            color="tab:orange",
            linewidth=1.0,
            alpha=0.92,
        )
        ax_price.set_title("测试集：真实 vs 预测（价格）")
        ax_price.set_xlabel("测试窗索引")
        ax_price.set_ylabel("价格")
        ax_price.legend(loc="best")
        fig_price.savefig("gru_predictions.png", dpi=180, bbox_inches="tight")
        print("价格预测图已保存: gru_predictions.png")

        # 残差分布图
        residuals = (y - p).ravel()
        fig_res, ax_res = plt.subplots(1, 1, figsize=(10, 4), constrained_layout=True)
        ax_res.hist(residuals, bins=40, color="tab:purple", alpha=0.75, edgecolor="white")
        ax_res.axvline(0.0, color="black", linestyle="--", linewidth=1.0)
        ax_res.set_title("收益预测残差分布 (y_true - y_pred)")
        ax_res.set_xlabel("残差")
        ax_res.set_ylabel("频次")
        fig_res.savefig("residual_distribution.png", dpi=180, bbox_inches="tight")
        print("残差分布图已保存: residual_distribution.png")

        # 真实-预测散点图
        fig_sc, ax_sc = plt.subplots(1, 1, figsize=(6, 6), constrained_layout=True)
        ax_sc.scatter(y.ravel(), p.ravel(), s=14, alpha=0.65, color="tab:blue")
        vmin = float(min(np.min(y), np.min(p)))
        vmax = float(max(np.max(y), np.max(p)))
        ax_sc.plot([vmin, vmax], [vmin, vmax], color="tab:red", linestyle="--", linewidth=1.0)
        ax_sc.set_title("收益真实值 vs 预测值")
        ax_sc.set_xlabel("真实收益")
        ax_sc.set_ylabel("预测收益")
        fig_sc.savefig("return_scatter.png", dpi=180, bbox_inches="tight")
        print("收益散点图已保存: return_scatter.png")

        # 方向图与混淆矩阵（仅双头）
        if use_multi and per_dir is not None and ydir_test is not None and pred_cls is not None:
            true_dir = ydir_test.ravel().astype(np.int32)
            fig_dir, ax_dir = plt.subplots(1, 1, figsize=(11, 4), constrained_layout=True)
            ax_dir.plot(true_dir, label="真实方向(1涨/0跌)", color="tab:blue", linewidth=1.0)
            ax_dir.plot(pred_cls, label="预测方向(阈值0.5)", color="tab:orange", linewidth=1.0, alpha=0.8)
            ax_dir.set_title("方向预测对比")
            ax_dir.set_xlabel("测试窗索引")
            ax_dir.set_ylabel("方向")
            ax_dir.legend(loc="best")
            fig_dir.savefig("direction_prediction.png", dpi=180, bbox_inches="tight")
            print("方向预测图已保存: direction_prediction.png")

            if cm is not None:
                fig_cm, ax_cm = plt.subplots(1, 1, figsize=(5, 4), constrained_layout=True)
                im = ax_cm.imshow(cm, cmap="Blues")
                for i in range(cm.shape[0]):
                    for j in range(cm.shape[1]):
                        ax_cm.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
                ax_cm.set_xticks([0, 1])
                ax_cm.set_yticks([0, 1])
                ax_cm.set_xticklabels(["Pred Down", "Pred Up"])
                ax_cm.set_yticklabels(["True Down", "True Up"])
                ax_cm.set_title("方向混淆矩阵")
                fig_cm.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)
                fig_cm.savefig("direction_confusion_matrix.png", dpi=180, bbox_inches="tight")
                print("方向混淆矩阵图已保存: direction_confusion_matrix.png")

            # 方向概率分布图
            fig_prob, ax_prob = plt.subplots(1, 1, figsize=(10, 4), constrained_layout=True)
            ax_prob.hist(per_dir.ravel(), bins=30, color="tab:orange", alpha=0.8, edgecolor="white")
            ax_prob.axvline(0.5, color="black", linestyle="--", linewidth=1.0, label="threshold=0.5")
            ax_prob.set_title("方向头输出概率分布")
            ax_prob.set_xlabel("P(up)")
            ax_prob.set_ylabel("频次")
            ax_prob.legend(loc="best")
            fig_prob.savefig("direction_prob_distribution.png", dpi=180, bbox_inches="tight")
            print("方向概率分布图已保存: direction_prob_distribution.png")

        # 简易回测净值曲线（信号=预测收益符号）
        fig_nav, ax_nav = plt.subplots(1, 1, figsize=(11, 4), constrained_layout=True)
        ax_nav.plot(strat_nav, label="Strategy NAV", color="tab:green", linewidth=1.1)
        ax_nav.plot(bh_nav, label="Buy&Hold NAV", color="tab:gray", linewidth=1.0, alpha=0.8)
        ax_nav.set_title("策略净值 vs 买入持有")
        ax_nav.set_xlabel("测试窗索引")
        ax_nav.set_ylabel("净值")
        ax_nav.legend(loc="best")
        fig_nav.savefig("backtest_nav_curve.png", dpi=180, bbox_inches="tight")
        print("回测净值图已保存: backtest_nav_curve.png")

        plt.show()


if __name__ == "__main__":
    main()
