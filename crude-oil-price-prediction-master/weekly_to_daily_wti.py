import argparse
from pathlib import Path

import pandas as pd


def _parse_volume(v: object) -> float:
    if pd.isna(v):
        return float("nan")
    s = str(v).strip().upper().replace(",", "")
    if not s:
        return float("nan")
    mul = 1.0
    if s.endswith("K"):
        mul = 1_000.0
        s = s[:-1]
    elif s.endswith("M"):
        mul = 1_000_000.0
        s = s[:-1]
    elif s.endswith("B"):
        mul = 1_000_000_000.0
        s = s[:-1]
    return float(s) * mul


def _parse_pct(v: object) -> float:
    if pd.isna(v):
        return float("nan")
    s = str(v).strip().replace("%", "")
    if not s:
        return float("nan")
    return float(s) / 100.0


def weekly_to_daily(input_csv: Path, output_csv: Path, freq: str = "D") -> None:
    tried: list[str] = []
    df = None
    for enc in ("utf-8", "utf-8-sig", "gb18030", "gbk", "cp936"):
        try:
            df = pd.read_csv(input_csv, encoding=enc)
            break
        except UnicodeDecodeError:
            tried.append(enc)
    if df is None:
        raise UnicodeDecodeError(
            "auto-detect",
            b"",
            0,
            1,
            f"无法解码文件，请确认编码；已尝试: {tried}",
        )
    if "日期" not in df.columns:
        raise ValueError("输入文件缺少 `日期` 列")

    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期").drop_duplicates("日期")

    if "交易量" in df.columns:
        df["交易量"] = df["交易量"].map(_parse_volume)
    if "涨跌幅" in df.columns:
        df["涨跌幅"] = df["涨跌幅"].map(_parse_pct)

    df = df.set_index("日期")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    other_cols = [c for c in df.columns if c not in num_cols]

    daily_idx = pd.date_range(df.index.min(), df.index.max(), freq=freq)
    out = df.reindex(daily_idx)

    if num_cols:
        out[num_cols] = out[num_cols].interpolate(method="time")
    if other_cols:
        out[other_cols] = out[other_cols].ffill()

    out = out.reset_index().rename(columns={"index": "日期"})
    out.to_csv(output_csv, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="将周频 WTI 数据插值为日频")
    parser.add_argument("input_csv", help="输入周频 CSV 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        default="WTI_weekly_to_daily.csv",
        help="输出日频 CSV 文件路径（默认: WTI_weekly_to_daily.csv）",
    )
    parser.add_argument(
        "--freq",
        default="D",
        choices=["D", "B"],
        help="目标频率：D=自然日，B=工作日（默认 D）",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output_csv = Path(args.output)
    weekly_to_daily(input_csv, output_csv, freq=args.freq)
    print(f"转换完成: {output_csv.resolve()}")


if __name__ == "__main__":
    main()
