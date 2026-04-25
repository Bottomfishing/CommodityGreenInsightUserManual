
"""
多变量油价预测主函数（按时间序列最佳实践重构）
整合 raw_data 和 能源基本面与下游产业 数据
使用 LSTM 和 GRU 模型进行预测
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor

import tensorflow as tf
import os
import random
import argparse
from pathlib import Path
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, CSVLogger
from tensorflow.keras.losses import Huber

from scipy.stats import spearmanr, zscore, kurtosis as scipy_kurtosis
from scipy.stats.mstats import winsorize

# 尝试导入 LightGBM，如果没有则用 RandomForest
try:
    import lightgbm as lgb
    USE_LIGHTGBM = True
except ImportError:
    USE_LIGHTGBM = False

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
LOOKBACK_L = 30   # 1日预测用较短窗口更敏感，60/90 可做对比
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
TARGET_COL = 'WTI_Price_t_plus_H'  # 预测目标列名，需在特征选择前创建


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
            for d in [1, 3, 5]:
                df[f'{price_col}_Momentum_{d}d'] = df[f'{price_col}_Return'].rolling(d).sum().shift(1)
        
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
        def _add_market_block(col: str, prefix: str):
            if col not in df.columns:
                return
            s = pd.to_numeric(df[col], errors='coerce').astype(float)
            eps = 1e-8
            # 原始水平（后续在 _ensure_causality 里会统一对 Level 做 shift）
            df[f'{prefix}_Level'] = s
            # 一阶/二阶变化与收益
            df[f'{prefix}_Change'] = s.diff()
            df[f'{prefix}_Diff2'] = s.diff().diff().shift(1)
            df[f'{prefix}_Return'] = np.log((s + eps) / (s.shift(1) + eps))
            # 多尺度滞后、动量、波动、均值、zscore、分位数
            for lag in [1, 2, 3, 5, 10, 20]:
                df[f'{prefix}_Lag{lag}'] = s.shift(lag)
            for w in [5, 10, 20, 60]:
                roll_mean = s.rolling(w).mean()
                roll_std = s.rolling(w).std()
                df[f'{prefix}_MA_{w}'] = roll_mean.shift(1)
                df[f'{prefix}_Std_{w}'] = roll_std.shift(1)
                df[f'{prefix}_Z_{w}'] = ((s - roll_mean) / (roll_std + eps)).shift(1)
                df[f'{prefix}_Momentum_{w}'] = df[f'{prefix}_Return'].rolling(w).sum().shift(1)
            for w in [20, 60]:
                df[f'{prefix}_Percentile_{w}'] = s.rolling(w).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == w else np.nan
                ).shift(1)

        # 2.1 金融市场核心因子（完整版）
        _add_market_block('DXY', 'DXY')
        _add_market_block('SP500', 'SP500')
        _add_market_block('VIX', 'VIX')
        _add_market_block('US10Y', 'US10Y')
        _add_market_block('OVX', 'OVX')

        # 2.2 跨因子相对强弱与价差（保持因果）
        if all(c in df.columns for c in ['OVX', 'VIX']):
            eps = 1e-8
            df['OVX_VIX_Ratio'] = (df['OVX'] / (df['VIX'] + eps)).shift(1)
            df['OVX_VIX_Spread'] = (df['OVX'] - df['VIX']).shift(1)
            df['OVX_VIX_Ratio_Change'] = df['OVX_VIX_Ratio'].diff().shift(1)
        if all(c in df.columns for c in ['SP500', 'DXY']):
            eps = 1e-8
            df['SP500_DXY_Ratio'] = (df['SP500'] / (df['DXY'] + eps)).shift(1)
            df['SP500_DXY_Ratio_Change'] = df['SP500_DXY_Ratio'].diff().shift(1)
        if all(c in df.columns for c in ['US10Y', 'DXY']):
            df['US10Y_DXY_Cross'] = (df['US10Y'].diff() * df['DXY'].pct_change()).shift(1)
        if all(c in df.columns for c in ['SP500_Return', 'DXY_Return']):
            for w in [20, 60]:
                df[f'SP500_DXY_Corr_{w}'] = df['SP500_Return'].rolling(w).corr(
                    df['DXY_Return']
                ).shift(1)

        # 2.3 实际利率（若有通胀预期）
        if 'US10Y' in df.columns and 'Inflation_Exp' in df.columns:
            real_rate = (df['US10Y'] - df['Inflation_Exp']).astype(float)
            df['Real_Rate'] = real_rate.shift(1)
            df['Real_Rate_Change'] = real_rate.diff().shift(1)
            for w in [5, 20, 60]:
                rr_mean = real_rate.rolling(w).mean()
                rr_std = real_rate.rolling(w).std()
                df[f'Real_Rate_Z_{w}'] = ((real_rate - rr_mean) / (rr_std + 1e-8)).shift(1)
        
        return df
    
    def _add_fundamental_features(self, df):
        """添加基本面特征"""
        def _add_fund_block(col: str, prefix: str, windows: list[int]):
            if col not in df.columns:
                return
            s = pd.to_numeric(df[col], errors='coerce').astype(float)
            eps = 1e-8
            df[f'{prefix}_Level'] = s
            df[f'{prefix}_Change'] = s.diff()
            df[f'{prefix}_Diff2'] = s.diff().diff().shift(1)
            df[f'{prefix}_PctChange'] = s.pct_change()
            for lag in [1, 2, 3, 5, 10, 20, 28]:
                df[f'{prefix}_Lag{lag}'] = s.shift(lag)
            for w in windows:
                roll_mean = s.rolling(w).mean()
                roll_std = s.rolling(w).std()
                df[f'{prefix}_MA_{w}'] = roll_mean.shift(1)
                df[f'{prefix}_Std_{w}'] = roll_std.shift(1)
                df[f'{prefix}_Z_{w}'] = ((s - roll_mean) / (roll_std + eps)).shift(1)
                df[f'{prefix}_Momentum_{w}'] = s.diff(w).shift(1)
                if w >= 5:
                    df[f'{prefix}_Trend_{w}'] = s.rolling(w).apply(
                        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == w else np.nan
                    ).shift(1)
            for w in [20, 60]:
                df[f'{prefix}_Percentile_{w}'] = s.rolling(w).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == w else np.nan
                ).shift(1)

        # 3.1 库存 / 产量 / 钻井数完整特征
        _add_fund_block('Stocks', 'Stocks', [5, 10, 20, 60])
        _add_fund_block('Production', 'Production', [5, 10, 20, 60])
        _add_fund_block('Rigs', 'Rigs', [5, 10, 20, 28, 60])
        if 'Rigs' in df.columns:
            # 与原版保持兼容命名
            df['Rigs_Momentum_4w'] = df['Rigs'].diff(28).shift(1)

        # 3.2 供需平衡特征（若有 Demand）
        if all(col in df.columns for col in ['Production', 'Demand']):
            eps = 1e-8
            bal = (df['Production'] - df['Demand']).astype(float)
            ratio = (df['Production'] / (df['Demand'] + eps)).astype(float)
            df['Supply_Demand_Balance'] = bal.shift(1)
            df['Supply_Demand_Ratio'] = ratio.shift(1)
            df['Supply_Demand_Balance_Change'] = bal.diff().shift(1)
            df['Supply_Demand_Ratio_Change'] = ratio.diff().shift(1)
            for w in [5, 20, 60]:
                b_mean = bal.rolling(w).mean()
                b_std = bal.rolling(w).std()
                df[f'Supply_Demand_Balance_Z_{w}'] = ((bal - b_mean) / (b_std + eps)).shift(1)
                df[f'Supply_Demand_Balance_Momentum_{w}'] = bal.diff(w).shift(1)
        
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
        def _add_sent_block(col: str, prefix: str):
            if col not in df.columns:
                return
            s = pd.to_numeric(df[col], errors='coerce').astype(float)
            eps = 1e-8
            # 保留原始命名兼容
            df[f'{prefix}_Trend'] = s
            df[f'{prefix}_Change'] = s.diff()
            for lag in [1, 2, 3, 5, 10, 20]:
                df[f'{prefix}_Lag{lag}'] = s.shift(lag)
            for w in [5, 10, 20, 60]:
                roll_mean = s.rolling(w).mean()
                roll_std = s.rolling(w).std()
                df[f'{prefix}_MA_{w}'] = roll_mean.shift(1)
                df[f'{prefix}_Std_{w}'] = roll_std.shift(1)
                df[f'{prefix}_Z_{w}'] = ((s - roll_mean) / (roll_std + eps)).shift(1)
                df[f'{prefix}_Momentum_{w}'] = s.pct_change(w).shift(1)
            for w in [20, 60]:
                df[f'{prefix}_Percentile_{w}'] = s.rolling(w).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) == w else np.nan
                ).shift(1)

        # 8.1 Google Trends 情绪（raw_data/情绪指标/oil price.csv & gas price.csv）
        if 'Oil_Trends' in df.columns:
            _add_sent_block('Oil_Trends', 'Oil_Search')
        if 'Gas_Trends' in df.columns:
            _add_sent_block('Gas_Trends', 'Gas_Search')

        # 8.1b 油气情绪相对指标
        if all(col in df.columns for col in ['Oil_Trends', 'Gas_Trends']):
            eps = 1e-8
            ratio = (df['Oil_Trends'] / (df['Gas_Trends'] + eps)).astype(float)
            spread = (df['Oil_Trends'] - df['Gas_Trends']).astype(float)
            df['Oil_Gas_Search_Ratio'] = ratio.shift(1)
            df['Oil_Gas_Search_Spread'] = spread.shift(1)
            df['Oil_Gas_Search_Ratio_Change'] = ratio.diff().shift(1)
            for w in [5, 20, 60]:
                r_mean = ratio.rolling(w).mean()
                r_std = ratio.rolling(w).std()
                df[f'Oil_Gas_Search_Ratio_Z_{w}'] = ((ratio - r_mean) / (r_std + eps)).shift(1)
                df[f'Oil_Gas_Search_Ratio_Momentum_{w}'] = ratio.pct_change(w).shift(1)
                df[f'Oil_Gas_Search_Corr_{w}'] = df['Oil_Trends'].rolling(w).corr(
                    df['Gas_Trends']
                ).shift(1)
        
        # 8.2 新闻情绪（如果有新闻数据）
        if 'News_Sentiment' in df.columns:
            s = pd.to_numeric(df['News_Sentiment'], errors='coerce').astype(float)
            df['News_Sentiment_Score'] = s.shift(1)
            df['News_Sentiment_Change'] = s.diff().shift(1)
            df['News_Sentiment_Momentum'] = s.rolling(5).mean().shift(1)
        
        # 8.3 社交媒体情绪（如果有Twitter数据）
        if 'Twitter_Sentiment' in df.columns:
            s = pd.to_numeric(df['Twitter_Sentiment'], errors='coerce').astype(float)
            df['Social_Media_Sentiment'] = s.shift(1)
            df['Social_Media_Change'] = s.diff().shift(1)
            df['Social_Media_Volatility'] = s.rolling(5).std().shift(1)
        
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
        level_cols = [c for c in df.columns if c.endswith('_Level')]
        cols_need_shift = level_cols + [
            'Basis', 'Market_Structure',
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


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 创建示例数据（实际使用时替换为真实数据）
    dates = pd.date_range('2010-01-01', '2023-12-31', freq='D')
    n_days = len(dates)
    
    example_data = pd.DataFrame({
        'Date': dates,
        'WTI_Futures': np.random.randn(n_days).cumsum() + 70,  # 模拟油价
        'WTI_Spot': np.random.randn(n_days).cumsum() + 69,
        'DXY': np.random.randn(n_days).cumsum() + 90,
        'SP500': np.random.randn(n_days).cumsum() + 3000,
        'VIX': np.abs(np.random.randn(n_days)) * 10 + 15,
        'OVX': np.abs(np.random.randn(n_days)) * 5 + 25,
        'US10Y': np.random.randn(n_days) * 0.5 + 3.0,
        'Stocks': np.random.randn(n_days).cumsum() + 500,
        'Production': np.random.randn(n_days).cumsum() + 12000,
        'Oil_Trends': np.random.rand(n_days) * 100,
        'Gas_Trends': np.random.rand(n_days) * 100,
        'Brent': np.random.randn(n_days).cumsum() + 75,  # Brent价格
    })
    
    example_data = example_data.set_index('Date')
    
    # 初始化特征工程器（类名为 FeatureEngineer）
    feature_engineer = FeatureEngineer(lookback_windows=[5, 10, 20, 60])
    
    # 创建所有特征
    data_with_features = feature_engineer.create_all_features(
        example_data, 
        target_price_col='WTI_Futures'
    )
    
    # 获取特征分类
    categories = feature_engineer.get_feature_categories(data_with_features)
    
    # 显示结果
    print(f"\n原始数据形状: {example_data.shape}")
    print(f"特征工程后数据形状: {data_with_features.shape}")
    print(f"新增特征数量: {data_with_features.shape[1] - example_data.shape[1]}")
    
    # 查看前几行
    print("\n前5行数据（部分列）:")
    cols_to_show = ['WTI_Futures', 'WTI_Futures_Return', 'DXY_Return', 
                    'Stocks_Change', 'RSI_14', 'Volatility_20d', 'Month']
    available_cols = [c for c in cols_to_show if c in data_with_features.columns]
    print(data_with_features[available_cols].head())


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
        重要：target_col 必须与模型预测目标一致（如 WTI_Price_t_plus_H），
        否则会选出与当前价格相关但与未来价格无关的特征，导致欠拟合。
        
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


class OilPricePredictor:
    def __init__(self, timesteps=LOOKBACK_L, horizon=HORIZON_H):
        self.timesteps = timesteps
        self.horizon = horizon
    
    def create_target_price(self, data, price_col='WTI_Futures', target_col='WTI_Price_t_plus_H'):
        """创建目标：未来价格 y_t = P_{t+h}（直接在价格上回归）"""
        if price_col not in data.columns:
            return data
        data = data.copy()
        data[target_col] = data[price_col].shift(-self.horizon)
        return data
    
    def prepare_data(self, data_train, data_val, data_test, feature_cols, target_col='WTI_Return'):
        """准备序列数据"""
        # 只保留建模所需列，并确保没有 NaN（前面已做 ffill + dropna，这里再兜底一次）
        needed_cols = list(dict.fromkeys(feature_cols + [target_col, 'WTI_Futures']))
        data_train = data_train[needed_cols].dropna().copy()
        data_val = data_val[needed_cols].dropna().copy()
        data_test = data_test[needed_cols].dropna().copy()

        # 提取特征和目标
        X_train = data_train[feature_cols].values
        y_train = data_train[target_col].values
        X_val = data_val[feature_cols].values
        y_val = data_val[target_col].values
        X_test = data_test[feature_cols].values
        y_test = data_test[target_col].values
        
        # scaler 只 fit 在 Train
        scaler_X = MinMaxScaler(feature_range=(0, 1))
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_val_scaled = scaler_X.transform(X_val)
        X_test_scaled = scaler_X.transform(X_test)
        y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1))
        y_val_scaled = scaler_y.transform(y_val.reshape(-1, 1))
        y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1))
        
        # 构造序列（Train / Val）
        X_train_seq, y_train_seq = self._create_sequences(X_train_scaled, y_train_scaled)
        X_val_seq, y_val_seq = self._create_sequences(X_val_scaled, y_val_scaled)
        
        # 测试序列：只使用测试集自身的历史（不跨越 Train/Val 边界）
        X_test_seq, y_test_seq = self._create_sequences(X_test_scaled, y_test_scaled)
        
        # 保存原始价格用于评估（还原收益到价格）
        # 注意：序列创建时考虑了 horizon，所以价格也需要相应调整
        price_train = data_train['WTI_Futures'].values[self.timesteps:]
        price_val = data_val['WTI_Futures'].values[self.timesteps:]
        
        # 测试集：仅基于 data_test 的价格对齐 base / target
        # price_test[k] 的索引与 X_test_scaled 的行一一对应
        price_test = data_test[['WTI_Futures']].iloc[:, 0].values
        test_index = data_test.index

        # 与 _create_sequences 中相同的 i 范围
        i_start = self.timesteps
        i_end = len(X_test_scaled) - self.horizon + 1
        indices = np.arange(i_start, i_end)  # 窗口右端索引 i，对应时刻 t = i-1

        base_idx = indices - 1
        target_idx = base_idx + self.horizon

        price_test_base = price_test[base_idx]
        price_test_target = price_test[target_idx]
        date_test_base = test_index[base_idx]
        date_test_target = test_index[target_idx]
        
        return {
            'X_train': X_train_seq, 'y_train': y_train_seq,
            'X_val': X_val_seq, 'y_val': y_val_seq,
            'X_test': X_test_seq, 'y_test': y_test_seq,
            'scaler_X': scaler_X, 'scaler_y': scaler_y,
            'price_train': price_train, 'price_val': price_val, 
            'price_test_base': price_test_base, 'price_test_target': price_test_target,
            'date_test_base': date_test_base, 'date_test_target': date_test_target,
            'feature_cols': feature_cols
        }

    def _create_sequences(self, X, y):
        """创建序列（考虑 horizon）"""
        X_seq, y_seq = [], []
        # 重要：y 已经在 create_target_return 中定义为 return[t] = log(P[t+h]/P[t])
        # 因此当窗口为 X[i-timesteps : i]（末端时刻 t=i-1）时，标签应取 y[t]=y[i-1]
        # 不要再额外把 y 往未来推 (h-1)，否则会造成“平移预测”的假象
        # 同时：只生成那些确实存在 P[t+h] 的样本（避免样本数与 base/target price 不一致）
        # t = i-1，因此需要 i-1+h < len(y)  =>  i <= len(y) - h
        for i in range(self.timesteps, len(X) - self.horizon + 1):
            X_seq.append(X[i - self.timesteps:i])
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

    def build_gru_model(self, input_shape, units=[256, 128, 64], dropout=0.08, learning_rate=3e-3):
        model = Sequential()
        for i, unit in enumerate(units):
            return_sequences = (i < len(units) - 1)

            if i == 0:
                model.add(GRU(
                    units=unit,
                    return_sequences=return_sequences,
                    activation='tanh',
                    recurrent_activation='sigmoid',
                    recurrent_dropout=0.0,
                    reset_after=True,
                    input_shape=input_shape
                ))
            else:
                model.add(GRU(
                    units=unit,
                    return_sequences=return_sequences,
                    activation='tanh',
                    recurrent_activation='sigmoid',
                    recurrent_dropout=0.0,
                    reset_after=True
                ))

            model.add(Dropout(dropout))

        model.add(Dense(64, activation='relu'))
        model.add(Dropout(dropout))
        model.add(Dense(32, activation='relu'))
        model.add(Dropout(dropout))
        model.add(Dense(1))

        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss=Huber(),
            metrics=['mae']
        )

        return model

    def train_model(self, model, X_train, y_train, X_val, y_val,
                    epochs=200, batch_size=32, verbose=1,
                    log_path='training_log.csv'):
        """训练模型：更多 epoch、早停防过拟合、学习率衰减，以更好拟合"""
        callbacks = [
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=15, min_lr=1e-7, verbose=1),
            CSVLogger(log_path, append=False)
        ]
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose,
            shuffle=False
        )
        return history

    def predict(self, model, X_test):
        """预测（返回归一化后的值）"""
        return model.predict(X_test)
    
    def predict_price(self, pred_price_scaled, scaler_y):
        """将归一化后的价格预测还原为实际价格"""
        return scaler_y.inverse_transform(pred_price_scaled.reshape(-1, 1)).flatten()
    
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


def main(base_path='.', top_n=RF_TOP_N_DEFAULT, output_dir='.', no_plots=False,
         cutoff_date=None, forecast_steps=0, epochs: int = 200):
    print("=" * 80)
    print("多变量油价预测系统（按时间序列最佳实践）")
    print("=" * 80)

    output_dir = output_dir or '.'
    os.makedirs(output_dir, exist_ok=True)
    show_plots = not no_plots

    def out_path(filename: str) -> str:
        return os.path.join(output_dir, filename)
    
    # Step 0: 加载数据
    loader = OilPriceDataLoader(base_path=base_path)
    data = loader.load_all_data()
    
    # Step 1: 特征工程（严格因果）
    feature_engineer = FeatureEngineer()
    data_features = feature_engineer.create_all_features(data, target_price_col='WTI_Futures')

    # Step 1.5: 先创建未来价格目标（必须在特征选择之前，以便 RF 按与未来价格的相关性选特征）
    predictor = OilPricePredictor(timesteps=LOOKBACK_L, horizon=HORIZON_H)
    data_features = predictor.create_target_price(
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

    # Step 4: 只用 Train 做特征选择
    try:
        n = int(top_n)
    except Exception:
        n = int(RF_TOP_N_DEFAULT)

    data_train_sel, data_val_sel, data_test_sel, feature_cols = \
        preprocessor.rf_feature_selection_top_n(
            data_train,
            data_val,
            data_test,
            target_col=TARGET_COL,
            top_n=int(n)
        )

    # Step 4.1: 只在 Train 上计算 winsorize
    data_train_sel = preprocessor.winsorize_outliers(data_train_sel, lower=0.01, upper=0.99)

    # Step 4.2: dropna
    data_train_sel = data_train_sel.dropna().copy()
    data_val_sel = data_val_sel.dropna().copy()
    data_test_sel = data_test_sel.dropna().copy()
    print(f"\n数据清洗后: Train={len(data_train_sel)}, Val={len(data_val_sel)}, Test={len(data_test_sel)}")

    all_feature_cols = data_train_sel.columns.tolist()  # 保留当前所有列（已是筛选后的特征集）
    full_train = data_train_sel[all_feature_cols].copy()
    full_train['Split'] = 'train'
    full_val = data_val_sel[all_feature_cols].copy()
    full_val['Split'] = 'val'
    full_test = data_test_sel[all_feature_cols].copy()
    full_test['Split'] = 'test'
    full_all = pd.concat([full_train, full_val, full_test]).sort_index()
    full_all.reset_index(inplace=True)
    full_all.rename(columns={'index': 'Date'}, inplace=True)
    full_all.to_csv(out_path('all_features_data.csv'), index=False)
    print(f"\n已保存所有特征总表到 {out_path('all_features_data.csv')}，行数={len(full_all)}，列数={full_all.shape[1]}")

    # 此时已经完成：
    # - 整段缺失值处理
    # - 随机森林 Top-N 特征选择
    # - 整段 Z-score 删除异常值
    # - 日期切分 + 创建未来价格目标
    #
    # 因此可以直接把当前的数据视为“已筛选&清洗”的最终输入
    data_train_filtered = data_train_sel
    data_val_filtered = data_val_sel
    data_test_filtered = data_test_sel
    final_features = feature_cols
    print(f"\n最终特征数: {len(final_features)}")

    # Step 5: 导出给模型使用的特征工程总表（含 Train/Val/Test 标记）
    cols_for_model = list(dict.fromkeys(final_features + [TARGET_COL, 'WTI_Futures']))
    model_train = data_train_filtered[cols_for_model].dropna().copy()
    model_train['Split'] = 'train'
    model_val = data_val_filtered[cols_for_model].dropna().copy()
    model_val['Split'] = 'val'
    model_test = data_test_filtered[cols_for_model].dropna().copy()
    model_test['Split'] = 'test'
    model_all = pd.concat([model_train, model_val, model_test]).sort_index()
    model_all.reset_index(inplace=True)
    model_all.rename(columns={'index': 'Date'}, inplace=True)
    model_all.to_csv(out_path('model_input_data.csv'), index=False)
    print(f"\n已保存模型输入总表到 {out_path('model_input_data.csv')}，行数={len(model_all)}，列数={model_all.shape[1]}")

    # Step 8: 准备序列数据
    data_dict = predictor.prepare_data(
        data_train_filtered, data_val_filtered, data_test_filtered,
        final_features, target_col=TARGET_COL
    )

    input_shape = (predictor.timesteps, data_dict['X_train'].shape[2])

    # Step 9: 训练模型（目前只保留 GRU，LSTM 暂时注释掉）
    # print("\n训练LSTM...")
    # lstm_model = predictor.build_lstm_model(input_shape, learning_rate=1e-3)
    # predictor.train_model(
    #     lstm_model, data_dict['X_train'], data_dict['y_train'],
    #     data_dict['X_val'], data_dict['y_val']
    # )

    print("\n训练GRU...")
    gru_model = predictor.build_gru_model(input_shape, units=[256, 128, 64], dropout=0.05, learning_rate=3e-3)
    predictor.train_model(
        gru_model, data_dict['X_train'], data_dict['y_train'],
        data_dict['X_val'], data_dict['y_val'],
        epochs=int(max(1, int(epochs or 200))), batch_size=32,
        log_path=out_path('training_log.csv')
    )

    # Step 10: 预测和评估
    # 预测目标（归一化后的未来价格），目前只用 GRU
    gru_pred_price_scaled = predictor.predict(gru_model, data_dict['X_test']).flatten()

    # 使用 prepare_data 中已经对齐好的价格
    test_base_prices = data_dict['price_test_base']
    test_target_prices = data_dict['price_test_target']
    test_base_dates = data_dict['date_test_base']
    test_target_dates = data_dict['date_test_target']

    # 确保长度匹配
    min_len = min(len(gru_pred_price_scaled), len(test_base_prices), len(test_target_prices), len(data_dict['y_test']))
    gru_pred_price_scaled = gru_pred_price_scaled[:min_len]
    test_base_prices = test_base_prices[:min_len]
    test_target_prices = test_target_prices[:min_len]
    test_base_dates = test_base_dates[:min_len]
    test_target_dates = test_target_dates[:min_len]
    y_test_price_scaled = data_dict['y_test'][:min_len]

    # 还原为价格（GRU）
    gru_pred_price = predictor.predict_price(
        gru_pred_price_scaled, data_dict['scaler_y']
    )

    # 为了继续输出/画“收益曲线”（方便检查是否仍贴 0），用价格反推出收益：
    # r_t = log(P_{t+h}/P_t)
    y_test_return = np.log(test_target_prices / test_base_prices)
    gru_pred_return = np.log(gru_pred_price / test_base_prices)

    # Baseline：随机游走（未来价格=当前价格 => return=0）
    baseline_pred_price = test_base_prices.copy()
    baseline_pred_return = np.log(baseline_pred_price / test_base_prices)  # 全 0

    # 评估（在价格上）
    y_test_price = test_target_prices
    # predictor.evaluate(y_test_price, lstm_pred_price, 'LSTM')
    metrics = predictor.evaluate(y_test_price, gru_pred_price, 'GRU')


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
    if metrics['R2'] >= 0.8:
        print(f"  [达标] 模型 R2={metrics['R2']:.4f} >= 0.8")
    else:
        print(f"  [未达标] 模型 R2={metrics['R2']:.4f} < 0.8，建议：增大 RF Top-N、增加训练 epoch 或检查数据")

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
        plt.title(f"Top-{top_k} 驱动因子（RF importance vs 未来价格目标）")
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
        report_lines.append(f"- 预测步长：H={HORIZON_H}（天），窗口：LOOKBACK={LOOKBACK_L}")
        report_lines.append(f"- 特征选择：RandomForest Top-N={int(n)}")
        report_lines.append("")
        report_lines.append("## 1. 预测效果（Test）")
        report_lines.append(f"- MAE：{metrics['MAE']:.4f}")
        report_lines.append(f"- RMSE：{metrics['RMSE']:.4f}")
        report_lines.append(f"- MAPE：{metrics['MAPE']:.2f}%")
        report_lines.append(f"- R2：{metrics['R2']:.4f}")
        report_lines.append(f"- 方向预测准确率（排除平盘）：{direction_accuracy:.4f}")
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
    gru_model.save(out_path('gru_model.h5'))
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
                feats = predictor.create_target_price(feats, price_col='WTI_Futures', target_col=TARGET_COL)
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
                if x_df.tail(predictor.timesteps).isna().any().any():
                    print("[警告] 实盘预测窗口仍存在 NaN，无法继续递推。")
                    break
                if len(x_df) < predictor.timesteps:
                    print("[警告] 实盘预测窗口不足（特征行数过少）。")
                    break

                x_window = x_df.iloc[-predictor.timesteps:].values
                x_scaled = scaler_X.transform(x_window)
                X_seq = x_scaled.reshape(1, predictor.timesteps, len(selected_features))

                pred_scaled = float(predictor.predict(gru_model, X_seq).flatten()[0])
                pred_price = float(predictor.predict_price(np.array([pred_scaled]), scaler_y)[0])

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
    parser.add_argument("--output-dir", default=".", help="输出目录（csv/png/h5/log 都写到这里）")
    parser.add_argument("--no-plots", action="store_true", help="不弹出图窗（适合 Web/服务器运行）")
    parser.add_argument("--cutoff-date", default=None, help="实盘预测的截止日期（YYYY-MM-DD）；默认使用数据最后一天")
    parser.add_argument("--forecast-steps", type=int, default=0, help="实盘预测：递推预测未来 N 天（0=不生成）")
    parser.add_argument("--epochs", type=int, default=200, help="训练轮数（epochs），默认 200")
    args = parser.parse_args()

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
        output_dir=args.output_dir,
        no_plots=args.no_plots,
        cutoff_date=args.cutoff_date,
        forecast_steps=args.forecast_steps,
        epochs=int(max(1, int(args.epochs or 200)))
    )