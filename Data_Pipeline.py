
import pandas as pd
import numpy as np
from pathlib import Path
import glob
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

def _to_datetime(df, col):
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df.dropna(subset=[col])


def _latest_file(pattern, root):
    paths = glob.glob(os.path.join(root, "**", pattern), recursive=True)
    if not paths:
        raise FileNotFoundError(f"找不到 {pattern}")
    return max(paths, key=os.path.getmtime)

def normalize_root(root):
    import os

    # 当前目录内容
    subdirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]

    # 如果只有一个子文件夹 → 很可能是多包了一层
    if len(subdirs) == 1:
        inner = os.path.join(root, subdirs[0])

        # 判断这个子目录是不是“真正的数据目录”
        inner_contents = os.listdir(inner)

        # 如果里面包含典型数据文件夹，就认为需要下钻
        if any(k in str(inner_contents) for k in ["绿色", "raw", "ESG", "data"]):
            print(f"[INFO] 检测到嵌套目录，自动进入: {inner}")
            return inner

    return root

def load_macro_folder(folder_path):
    import os

    all_data = []

    for file in os.listdir(folder_path):
        if not file.endswith(".xlsx"):
            continue

        path = os.path.join(folder_path, file)

        try:
            df = load_macro_excel(path)

            # 根据文件名判断变量类型
            name = file.lower()

            if "fed" in name or "美国" in name:
                df = df.rename(columns={"value": "fed_rate_exp"})

            elif "ecb" in name or "欧" in name:
                df = df.rename(columns={"value": "ecb_rate_exp"})

            elif "通胀" in name or "t5yie" in name:
                df = df.rename(columns={"value": "inflation_expectation"})

            else:
                print(f"⚠️ 未识别的宏观文件: {file}")
                continue

            print(f"✅ 使用宏观数据: {file}")
            all_data.append(df)

        except Exception as e:
            print(f"⏭️ 跳过文件（非数据）: {file} → {e}")

    if not all_data:
        print("⚠️ 没有可用宏观数据")
        return pd.DataFrame()

    # merge所有数据
    df = all_data[0]
    for d in all_data[1:]:
        df = df.merge(d, on="date", how="outer")

    return df


def load_macro_excel(path, date_col_keywords=["date"], value_col_keywords=["value", "rate", "price"]):
    import pandas as pd

    df = pd.read_excel(path)

    # 如果是说明文件，直接报错
    if "Series ID" in df.columns:
        raise ValueError("❌ 这是说明文件，不是数据文件")

    cols = df.columns

    # 找日期列
    def find_col(cols, keywords):
        for c in cols:
            for k in keywords:
                if k.lower() in c.lower():
                    return c
        return None

    date_col = find_col(cols, date_col_keywords)
    value_col = find_col(cols, value_col_keywords)
    if value_col is None:
        value_col = cols[1]

    if date_col is None:
        raise ValueError(f"❌ 找不到日期列: {cols}")

    if value_col is None:
        raise ValueError(f"❌ 找不到数值列: {cols}")

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["value"] = pd.to_numeric(df[value_col], errors="coerce")

    df = df[["date", "value"]].dropna()

    return df


def load_green_bond_index(path):

    df = pd.read_csv(path)

    # 日期列
    if "Trddt" in df.columns:
        df["date"] = pd.to_datetime(df["Trddt"])
    else:
        raise ValueError("❌ 找不到日期列")

    # 收盘价
    price_col = None
    for c in df.columns:
        if c.lower() in ["clsindex", "close", "price"]:
            price_col = c
            break

    if price_col is None:
        raise ValueError(f"❌ 找不到价格列: {df.columns}")

    df["price"] = pd.to_numeric(df[price_col], errors="coerce")

    df = df.sort_values("date")

    # ⭐收益率（核心）
    df["green_bond_yield"] = df["price"].pct_change()

    # ⭐动量
    df["green_bond_momentum"] = df["green_bond_yield"].rolling(5).mean()

    # ⭐波动
    df["green_bond_volatility"] = df["green_bond_yield"].rolling(10).std()

    return df[[
        "date",
        "green_bond_yield",
        "green_bond_momentum",
        "green_bond_volatility"
    ]]


def load_index_from_folder(folder_path):
    import os
    import pandas as pd

    all_dfs = []

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            path = os.path.join(folder_path, file)
            df = pd.read_csv(path, encoding="utf-8-sig")
            all_dfs.append(df)

    if not all_dfs:
        raise ValueError(f"{folder_path} 没有CSV文件")

    df = pd.concat(all_dfs, ignore_index=True)

    date_col = None
    for c in df.columns:
        if "日期" in c or "date" in c.lower() or "trddt" in c.lower():
            date_col = c
            break

    if date_col is None:
        raise ValueError(f"❌ 找不到日期列: {df.columns}")

    # 假设有“收盘价”或“指数值”
    value_col = None
    for c in df.columns:
        if "收盘" in c or "指数" in c or "close" in c.lower() or "cls" in c.lower():
            value_col = c
            break

    if value_col is None:
        raise ValueError("找不到价格列")

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df[["date", value_col]].rename(columns={value_col: "price"})
    df = df.sort_values("date").drop_duplicates("date")

    return df

def load_nav_all_years(base_path):
    import os
    import pandas as pd

    all_dfs = []

    for folder in sorted(os.listdir(base_path)):
        folder_path = os.path.join(base_path, folder)

        if not os.path.isdir(folder_path):
            continue
        if "基金日净值" not in folder:
            continue

        for file in os.listdir(folder_path):
            if file.endswith(".csv"):
                file_path = os.path.join(folder_path, file)

                try:
                    df = pd.read_csv(file_path, encoding="utf-8-sig")
                    all_dfs.append(df)
                except Exception as e:
                    print(f"读取失败: {file_path} → {e}")

    if not all_dfs:
        raise ValueError("没有读取到任何净值数据")

    nav = pd.concat(all_dfs, ignore_index=True)

    print("NAV列名:", nav.columns.tolist())

    # 自动识别日期列
    date_col = None
    for c in nav.columns:
        if "日期" in c or "date" in c.lower():
            date_col = c
            break

    if date_col is None:
        raise ValueError(f"❌ 找不到日期列，当前列名: {list(nav.columns)}")

    nav["date"] = pd.to_datetime(nav[date_col], errors="coerce")
    nav = nav.sort_values("date")
    nav_col = None
    for c in nav.columns:
        if "净值" in c or "nav" in c.lower():
            nav_col = c
            break

    if nav_col is None:
        raise ValueError(f"❌ 找不到净值列: {nav.columns}")

    nav = nav.groupby("date", as_index=False).agg({
        nav_col: "mean"
    }).rename(columns={nav_col: "NAV"})

    return nav

def load_esg_flow(data_root):
    import os
    import pandas as pd

    # ===== 自动找目录 =====
    def find_folder(root, keywords):
        for r, dirs, files in os.walk(root):
            for d in dirs:
                for k in keywords:
                    if k.lower() in d.lower():
                        return os.path.join(r, d)
        return None

    # ===== 递归读 CSV =====
    def load_all_csv(folder):
        if folder is None or not os.path.exists(folder):
            raise ValueError(f"❌ 目录不存在: {folder}")

        files = []
        for root, _, fs in os.walk(folder):
            for f in fs:
                if f.endswith(".csv"):
                    files.append(os.path.join(root, f))

        if not files:
            raise ValueError(f"❌ 目录下没有CSV: {folder}")

        df_list = []
        for f in files:
            df = pd.read_csv(f, encoding="utf-8-sig")
            df_list.append(df)

        return pd.concat(df_list, ignore_index=True)

    # ===== 找路径 =====
    share_path = find_folder(data_root, ["份额", "share"])
    nav_base_path = find_folder(data_root, ["净值", "nav"])

    print("[DEBUG] share_path:", share_path)
    print("[DEBUG] nav_path:", nav_base_path)

    if share_path is None:
        raise ValueError("❌ 没找到【份额变动】目录")

    if nav_base_path is None:
        raise ValueError("❌ 没找到【日净值】目录")

    # ===== 读取数据 =====
    share = load_all_csv(share_path)
    nav = load_nav_all_years(nav_base_path)

    print("share列名:", share.columns.tolist())

    # ===== 自动识别列 =====
    cols = share.columns

    def find_col(cols, keywords):
        for c in cols:
            for k in keywords:
                if k.lower() in c.lower():
                    return c
        return None

    start_col = find_col(cols, ["start", "begin"])
    end_col = find_col(cols, ["end"])
    purchase_col = find_col(cols, ["purchase", "buy"])
    redeem_col = find_col(cols, ["redeem", "redemption", "sell"])

    print("识别列：", start_col, end_col, purchase_col, redeem_col)

    if None in [start_col, end_col, purchase_col, redeem_col]:
        raise ValueError(f"❌ 无法识别关键列: {cols}")

    # ===== 重命名 =====
    share = share.rename(columns={
        start_col: "BeginDate",
        end_col: "EndDate",
        purchase_col: "Purchase",
        redeem_col: "Redeem"
    })

    share["BeginDate"] = pd.to_datetime(share["BeginDate"])
    share["EndDate"] = pd.to_datetime(share["EndDate"])

    share["ShareChange"] = share["Purchase"] - share["Redeem"]

    # ===== 展开成日频 =====
    df_daily = nav[["date"]].drop_duplicates().sort_values("date").copy()
    df_daily["ShareChange_daily"] = 0.0

    for _, row in share.iterrows():
        mask = (df_daily["date"] > row["BeginDate"]) & (df_daily["date"] <= row["EndDate"])
        days = mask.sum()
        if days > 0:
            df_daily.loc[mask, "ShareChange_daily"] += row["ShareChange"] / days

    df = df_daily.merge(nav[["date", "NAV"]], on="date", how="left")
    df["esg_flow"] = df["ShareChange_daily"] * df["NAV"]

    return df[["date", "esg_flow"]]


def load_greenium(data_root):
    green_path = os.path.join(data_root, "绿色溢价", "930951(中证交易所绿色债券)")
    treasury_path = os.path.join(data_root, "绿色溢价", "中证10年期国债指数930916")

    green = load_index_from_folder(green_path)
    treasury = load_index_from_folder(treasury_path)

    # 合并
    df = pd.merge(green, treasury, on="date", how="inner", suffixes=("_green", "_treasury"))

    # 计算收益率
    df["ret_green"] = df["price_green"].pct_change()
    df["ret_treasury"] = df["price_treasury"].pct_change()

    df["green_bond_momentum"] = df["price_green"].pct_change().rolling(5).mean()
    df["green_bond_volatility"] = df["price_green"].pct_change().rolling(10).std()

    df["greenium"] = df["ret_green"] - df["ret_treasury"]

    # 新增：目标变量
    df["green_bond_yield"] = df["ret_green"]

    # 清理第一行 NaN
    df = df.dropna(subset=["greenium", "green_bond_yield"])

    return df[[
        "date",
        "greenium",
        "green_bond_yield",
        "green_bond_momentum",
        "green_bond_volatility"
    ]]


def load_treasury_10y(source1_path, source2_path=None):

    s1 = pd.read_csv(source1_path)
    s1 = _to_datetime(s1, "observation_date")

    col = None
    for c in s1.columns:
        if "yield" in c.lower():
            col = c
            break

    if col is None:
        raise ValueError(f"❌ 找不到收益率列: {s1.columns}")

    s1["treasury_10y"] = pd.to_numeric(s1[col], errors="coerce")

    s1 = s1.rename(columns={"observation_date": "date"})
    s1 = s1[["date", "treasury_10y"]]

    if source2_path is None:
        return s1

    s2 = pd.read_csv(source2_path, sep="\t")
    s2["date"] = pd.to_datetime(s2["Date"], errors="coerce")
    s2["treasury_10y"] = pd.to_numeric(s2["Price"], errors="coerce")
    s2 = s2[["date", "treasury_10y"]]

    df = s1.merge(s2, on="date", how="outer", suffixes=("", "_s2"))
    df["treasury_10y"] = df["treasury_10y"].fillna(df["treasury_10y_s2"])

    return df[["date", "treasury_10y"]]


def load_oil(data_root, pred_path=None):
    wti_path = os.path.join(data_root, "raw_data", "WTI_futuresprice.csv")

    root = Path(__file__).resolve().parent

    if pred_path is None:
        try:
            pred_path = _latest_file("prediction_results.csv", str(root))
        except:
            print("⚠️ 未找到 oil prediction，跳过")
            return pd.DataFrame()

    pred = pd.read_csv(pred_path)
    pred["date"] = pd.to_datetime(pred["Date_target"])
    pred = pred.rename(columns={"GRU_Pred_P_t_plus_H": "oil_price_pred"})
    pred = pred[["date", "oil_price_pred"]]

    wti = pd.read_csv(wti_path)

    if "Date" not in wti.columns:
        wti.rename(columns={wti.columns[0]: "Date"}, inplace=True)

    wti["date"] = pd.to_datetime(wti["Date"], errors="coerce")

    price_col = None
    for c in wti.columns:
        if c.lower() in ["closeprice", "price", "close"]:
            price_col = c
            break

    if price_col is None:
        price_col = [c for c in wti.columns if c != "Date"][0]

    wti["price"] = pd.to_numeric(wti[price_col], errors="coerce")
    wti = wti.dropna(subset=["price"]).sort_values("date")

    wti["ret"] = np.log(wti["price"] / wti["price"].shift(1))
    wti["oil_volatility"] = wti["ret"].rolling(20).std().shift(1)

    return pd.merge_asof(
        pred.sort_values("date"),
        wti[["date", "oil_volatility"]].sort_values("date"),
        on="date",
        direction="backward",
        tolerance=pd.Timedelta("7D")
    )

def load_macro(new_date_dir="new_data"):

    root = Path(__file__).resolve().parent
    new_date_dir = root / new_date_dir

    data = []

    for file in new_date_dir.glob("*.xlsx"):
        xls = pd.ExcelFile(file)

        for sheet in xls.sheet_names:
            if "readme" in sheet.lower():
                continue

            df = pd.read_excel(file, sheet_name=sheet)

            if "observation_date" not in df.columns:
                continue

            value_col = [c for c in df.columns if c != "observation_date"][0]

            tmp = df[["observation_date", value_col]].copy()
            tmp.rename(columns={"observation_date": "date"}, inplace=True)
            tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")

            if "DFEDTARU" in value_col:
                tmp.rename(columns={value_col: "fed_rate_exp"}, inplace=True)
            elif "ECBMRRFR" in value_col:
                tmp.rename(columns={value_col: "ecb_rate_exp"}, inplace=True)
            elif "IRLTLT01DEM156N" in value_col:
                tmp.rename(columns={value_col: "treasury_10y"}, inplace=True)
            else:
                continue

            data.append(tmp)

    if not data:
        return pd.DataFrame()

    df = data[0]
    for d in data[1:]:
        df = df.merge(d, on="date", how="outer")

    return df



def build_dataset(data_root):

    data_root = normalize_root(data_root)
    
    # ===== 1 基础数据 =====
    esg = load_esg_flow(data_root)

    def find_green_folder(root):
        for d in os.listdir(root):
            if "绿" in d and "溢价" in d:
                return os.path.join(root, d)
        raise ValueError("❌ 找不到绿色溢价目录")

    green_bond_folder = find_green_folder(data_root)

    def find_subfolder(base, keyword):
        for d in os.listdir(base):
            if keyword in d:
                return os.path.join(base, d)
        raise ValueError(f"找不到 {keyword}")

    green_path = find_subfolder(green_bond_folder, "930951")
    treasury_path = find_subfolder(green_bond_folder, "国债")

    print("[DEBUG] green_path:", green_path)
    print("[DEBUG] treasury_path:", treasury_path)

    green = load_index_from_folder(green_path)
    treasury = load_index_from_folder(treasury_path)

    # 合并逻辑（和你原来的 load_greenium 一样）
    df = pd.merge(green, treasury, on="date", how="inner", suffixes=("_green", "_treasury"))

    df["ret_green"] = df["price_green"].pct_change()
    df["ret_treasury"] = df["price_treasury"].pct_change()

    df["green_bond_momentum"] = df["price_green"].pct_change().rolling(5).mean()
    df["green_bond_volatility"] = df["price_green"].pct_change().rolling(10).std()

    df["greenium"] = df["ret_green"] - df["ret_treasury"]
    df["green_bond_yield"] = df["ret_green"]

    df = df.dropna(subset=["greenium", "green_bond_yield"])

    green_bond = df[[
        "date",
        "greenium",
        "green_bond_yield",
        "green_bond_momentum",
        "green_bond_volatility"
    ]]

    df = esg.merge(green_bond, on="date", how="inner")


    # ===== 2 Oil =====
    try:
        oil = load_oil(data_root)

        if not oil.empty:
            df = df.merge(oil, on="date", how="left")

        print("✅ oil ok")
    except Exception as e:
        print("⚠️ oil失败:", e)

    # ===== 自动宏观数据 =====
    try:
        macro = load_macro_folder(os.path.join(data_root, "new_data"))

        if not macro.empty:
            df = df.merge(macro, on="date", how="left")
            print("✅ 宏观数据自动加载完成")

    except Exception as e:
        print("⚠️ 宏观数据失败:", e)

    for col in ["fed_rate_exp", "ecb_rate_exp", "inflation_expectation"]:
        if col not in df.columns:
            df[col] = np.nan

        # 统一处理（无论是否存在）
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].ffill()
    # ===== 4 Treasury（补充）=====
    try:
        treasury = load_treasury_10y(
            os.path.join(data_root, "raw_data", "US10Y_Yield.csv"),
            None
        )
        df = df.merge(treasury, on="date", how="left")
        print("✅ treasury ok")
    except Exception as e:
        print("⚠️ treasury失败:", e)

    # ===== 5 排序 + 填充 =====
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    df = df.ffill()

    CORE_COLS = ["green_bond_yield"]

    df = df.dropna(subset=[c for c in CORE_COLS if c in df.columns])

    return df

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=str, required=True)
    parser.add_argument("--output-csv", type=str, required=True)

    args = parser.parse_args()

    print("🚀 使用数据目录:", args.data_root)

    df = build_dataset(data_root=args.data_root)

    out_dir = os.path.dirname(args.output_csv)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    df.to_csv(args.output_csv, index=False)

    print(f"✅ 数据已保存到: {args.output_csv}")