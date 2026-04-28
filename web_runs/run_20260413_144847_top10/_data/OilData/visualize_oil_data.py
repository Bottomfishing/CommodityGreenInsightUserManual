import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 尝试使用常见中文字体，避免事件中文标注变成方块
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def load_events_data(events_path: Path, sheet_name: str | None = None) -> pd.DataFrame:
    """
    读取地缘事件数据，返回两列: event_date, event_name
    非标准日期（如"2014中-2016初"）会被自动过滤。
    """
    kwargs = {}
    if sheet_name:
        kwargs["sheet_name"] = sheet_name
    events = pd.read_excel(events_path, **kwargs)

    # 若读取到多sheet字典，默认取第一个sheet
    if isinstance(events, dict):
        first_key = next(iter(events))
        events = events[first_key]

    # 自动识别事件名和日期列
    name_candidates = ["事件名称", "事件", "Event", "event_name"]
    date_candidates = ["开始日期", "日期", "Date", "event_date"]

    event_col = next((c for c in name_candidates if c in events.columns), None)
    date_col = next((c for c in date_candidates if c in events.columns), None)
    if event_col is None or date_col is None:
        raise ValueError("事件文件缺少必要列（事件名称/开始日期）")

    out = events[[event_col, date_col]].copy()
    out.columns = ["event_name", "event_date"]
    out["event_date"] = pd.to_datetime(out["event_date"], errors="coerce")
    out["event_name"] = out["event_name"].astype(str).str.strip()
    out = out.dropna(subset=["event_date"])
    out = out[out["event_name"].str.len() > 0]
    out = out.sort_values("event_date").reset_index(drop=True)
    return out


def load_oil_data(file_path: Path) -> pd.DataFrame:
    """
    读取油价数据并自动适配常见的中英文列名。
    支持类似:
    - 日期,收盘,开盘,高,低,交易量,涨跌幅
    - Date,ClosePrice
    """
    # 尝试常见编码与两种头格式（标准头/跳过前置说明）
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    read_attempts = [0, 2]  # skiprows
    df = None
    last_error = None

    for enc in encodings:
        for skiprows in read_attempts:
            try:
                candidate = pd.read_csv(file_path, encoding=enc, skiprows=skiprows)
                cols = set(candidate.columns)
                has_date = any(c in cols for c in ["月份", "日期", "Date"])
                has_price = any(c in cols for c in ["收盘", "ClosePrice"]) or any(
                    "oil price" in str(c).lower() for c in cols
                )
                if has_date and has_price:
                    df = candidate
                    break
            except Exception as e:
                last_error = e
        if df is not None:
            break

    if df is None:
        raise ValueError(f"读取CSV失败，请检查文件格式/编码。原始错误: {last_error}")

    # 兼容带有说明头的文件
    if "月份" in df.columns:
        date_col = "月份"
    elif "日期" in df.columns:
        date_col = "日期"
    elif "Date" in df.columns:
        date_col = "Date"
    else:
        raise ValueError("未找到日期列（支持: 月份/日期/Date）")

    if "收盘" in df.columns:
        price_col = "收盘"
    elif "ClosePrice" in df.columns:
        price_col = "ClosePrice"
    else:
        # 尝试寻找含 oil price 的列
        oil_cols = [c for c in df.columns if "oil price" in c.lower()]
        if oil_cols:
            price_col = oil_cols[0]
        else:
            raise ValueError("未找到价格列（支持: 收盘/ClosePrice/oil price）")

    clean = df[[date_col, price_col]].copy()
    clean.columns = ["date", "price"]
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["price"] = pd.to_numeric(clean["price"], errors="coerce")
    clean = clean.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)
    return clean


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["return"] = out["price"].pct_change()
    # 12期滚动波动率，按周频近似为季度；按日频近似为半月
    out["vol_12"] = out["return"].rolling(12).std() * np.sqrt(12)
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month
    return out


def make_plots(
    df: pd.DataFrame,
    out_dir: Path,
    show: bool = False,
    events_df: pd.DataFrame | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    # 1) 油价趋势 + 12期均线
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["date"], df["price"], label="Oil Price", linewidth=1.8)
    ax.plot(df["date"], df["price"].rolling(12).mean(), label="MA(12)", linewidth=1.5)
    if events_df is not None and len(events_df) > 0:
        y_min = float(df["price"].min())
        y_max = float(df["price"].max())
        y_span = y_max - y_min if y_max > y_min else 1.0
        label_levels = [y_max - y_span * 0.04, y_max - y_span * 0.12, y_max - y_span * 0.20]
        for i, row in events_df.iterrows():
            event_date = row["event_date"]
            if event_date < df["date"].min() or event_date > df["date"].max():
                continue
            ax.axvline(event_date, color="crimson", linestyle="--", linewidth=0.9, alpha=0.55)
            y_text = label_levels[i % len(label_levels)]
            ax.text(
                event_date,
                y_text,
                row["event_name"],
                rotation=90,
                fontsize=8,
                color="crimson",
                va="top",
                ha="right",
                alpha=0.85,
            )
    ax.set_title("Oil Price Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "01_oil_price_trend.png", dpi=160)

    # 2) 收益率分布
    ret = df["return"].dropna()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(ret, bins=40, alpha=0.85)
    ax.set_title("Return Distribution")
    ax.set_xlabel("Return")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    fig.savefig(out_dir / "02_return_distribution.png", dpi=160)

    # 3) 滚动波动率
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["date"], df["vol_12"], linewidth=1.8)
    ax.set_title("Rolling Volatility (12 periods)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Volatility")
    fig.tight_layout()
    fig.savefig(out_dir / "03_rolling_volatility.png", dpi=160)

    # 4) 月度季节性
    monthly = df.groupby("month", as_index=False)["return"].mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(monthly["month"], monthly["return"], width=0.7)
    ax.set_title("Average Monthly Return (Seasonality)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Return")
    ax.set_xticks(range(1, 13))
    fig.tight_layout()
    fig.savefig(out_dir / "04_monthly_seasonality.png", dpi=160)

    if show:
        plt.show()
    else:
        plt.close("all")


def print_quick_stats(df: pd.DataFrame) -> None:
    ret = df["return"].dropna()
    print("===== Oil Data Quick Stats =====")
    print(f"样本区间: {df['date'].min().date()} ~ {df['date'].max().date()}")
    print(f"样本数量: {len(df)}")
    print(f"均价: {df['price'].mean():.4f}")
    print(f"价格标准差: {df['price'].std():.4f}")
    if len(ret) > 0:
        print(f"平均收益率: {ret.mean():.4%}")
        print(f"收益率波动率: {ret.std():.4%}")
        print(f"最大单期涨幅: {ret.max():.4%}")
        print(f"最大单期跌幅: {ret.min():.4%}")


def main() -> None:
    parser = argparse.ArgumentParser(description="油价数据可视化脚本")
    parser.add_argument(
        "--input",
        type=str,
        default="raw_data/WTI_futuresprice.csv",
        help="输入CSV文件路径",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="plots",
        help="图表输出目录",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="是否弹窗显示图表",
    )
    parser.add_argument(
        "--events",
        type=str,
        default="能源基本面与下游产业/三、地缘大事记.xlsx",
        help="事件Excel路径（可选，不存在则不标注）",
    )
    parser.add_argument(
        "--event-sheet",
        type=str,
        default="",
        help="事件Excel的sheet名（默认自动/首个sheet）",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    df = load_oil_data(input_path)
    df = add_derived_features(df)
    events_df = None
    events_path = Path(args.events)
    if events_path.exists():
        try:
            events_df = load_events_data(events_path, sheet_name=args.event_sheet or None)
            print(f"已加载事件数: {len(events_df)}")
        except Exception as e:
            print(f"事件文件读取失败，将跳过事件标注。原因: {e}")

    print_quick_stats(df)
    make_plots(df, Path(args.outdir), show=args.show, events_df=events_df)
    print(f"\n图表已保存到: {Path(args.outdir).resolve()}")


if __name__ == "__main__":
    main()
