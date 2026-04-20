import argparse
import ast
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, roc_auc_score
from tensorflow.keras.callbacks import CSVLogger, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import Concatenate, Conv1D, Dense, Dropout, GRU, GaussianNoise, Input
from tensorflow.keras.losses import Huber
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

try:
    import optuna
except Exception:
    optuna = None

# ===== 与 rework_oil_price_prediction.py 对齐的关键超参 =====
DIRECTION_LOSS_LAMBDA = 0.35
MULTITASK_CLS_WEIGHT = 0.4
USE_CNN_FRONT = True
DROPOUT_GRU_STACK = 0.22
RECURRENT_DROPOUT_GRU = 0.14
GAUSSIAN_NOISE_INPUT = 0.05
TRAIN_SEQ_AUG_COPIES = 4
TRAIN_SEQ_AUG_NOISE_STD = 0.09
TRAIN_SEQ_AUG_SEED = 42
LEARNING_RATE = 3e-3

_huber_loss = Huber(delta=1.0)


def _csv_cell_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return bool(v)


def load_params_from_csv(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path, nrows=1)
    if df.empty:
        raise ValueError(f"空 CSV: {csv_path}")
    row = df.iloc[0]

    def tup(key: str):
        v = row[key]
        return ast.literal_eval(str(v).strip())

    return {
        "units_5": tup("units_5"),
        "units_20": tup("units_20"),
        "units_60": tup("units_60"),
        "dense_units": tup("dense_units"),
        "dropout": float(row["dropout"]),
        "learning_rate": float(row["learning_rate"]),
        "recurrent_dropout": float(row["recurrent_dropout"]),
        "input_noise_std": float(row["input_noise_std"]),
        "use_cnn_front": _csv_cell_bool(row["use_cnn_front"]),
        "cls_weight": float(row["cls_weight"]),
        "direction_lambda": float(row["direction_lambda"]),
        "huber_delta": float(row["huber_delta"]),
        "aug_copies": int(row["aug_copies"]),
        "aug_noise_std": float(row["aug_noise_std"]),
        "aug_seed": int(row["aug_seed"]),
        "batch_size": int(row["batch_size"]),
    }


def load_sample_count(base_path: Path) -> int:
    csv_path = base_path / "raw_data" / "WTI_futuresprice.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"找不到文件: {csv_path}")
    df = pd.read_csv(csv_path)
    n = int(len(df))
    if n <= 10:
        raise ValueError(f"样本量过小: {n}")
    return n


def direction_aware_huber_loss_fn(y_true, y_pred):
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


class OptunaPruningCallback(tf.keras.callbacks.Callback):
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
):
    if n_extra_copies <= 0:
        return X5, X20, X60, y_reg, y_cls
    xs5 = [np.asarray(X5, dtype=np.float32)]
    xs20 = [np.asarray(X20, dtype=np.float32)]
    xs60 = [np.asarray(X60, dtype=np.float32)]
    yr_list = [np.asarray(y_reg, dtype=np.float32)]
    yc_list = [np.asarray(y_cls, dtype=np.float32)]
    for _ in range(int(n_extra_copies)):
        n5 = rng.normal(0.0, noise_std, X5.shape).astype(np.float32)
        n20 = rng.normal(0.0, noise_std, X20.shape).astype(np.float32)
        n60 = rng.normal(0.0, noise_std, X60.shape).astype(np.float32)
        a5 = X5.astype(np.float32) + n5
        a20 = X20.astype(np.float32) + n20
        a60 = X60.astype(np.float32) + n60
        if clip01:
            a5 = np.clip(a5, 0.0, 1.0)
            a20 = np.clip(a20, 0.0, 1.0)
            a60 = np.clip(a60, 0.0, 1.0)
        xs5.append(a5)
        xs20.append(a20)
        xs60.append(a60)
        yr_list.append(np.asarray(y_reg, dtype=np.float32).copy())
        yc_list.append(np.asarray(y_cls, dtype=np.float32).copy())
    return (
        np.concatenate(xs5, axis=0),
        np.concatenate(xs20, axis=0),
        np.concatenate(xs60, axis=0),
        np.concatenate(yr_list, axis=0),
        np.concatenate(yc_list, axis=0),
    )


def _stack_gru(x, units_list, kwargs):
    n = len(units_list)
    out = x
    for i, u in enumerate(units_list):
        out = GRU(int(u), return_sequences=(i < n - 1), **kwargs)(out)
    return out


def build_model(
    n_features: int = 15,
    w_short: int = 5,
    w_mid: int = 20,
    w_long: int = 60,
    units_5=(48,),
    units_20=(96,),
    units_60=(128,),
    dense_units=(128, 64),
    dropout: float = DROPOUT_GRU_STACK,
    learning_rate: float = LEARNING_RATE,
    recurrent_dropout: float = RECURRENT_DROPOUT_GRU,
    input_noise_std: float = GAUSSIAN_NOISE_INPUT,
    use_cnn_front: bool = USE_CNN_FRONT,
    cls_weight: float = MULTITASK_CLS_WEIGHT,
    direction_lambda: float = DIRECTION_LOSS_LAMBDA,
    huber_delta: float = 1.0,
) -> Model:
    """
    与 rework_oil_price_prediction.py 对齐的主干：
    三路窗口(5/20/60) + 可选 Conv1D 前端 + GRU 融合 + 双头输出。
    """
    kwargs = dict(
        activation="tanh",
        recurrent_activation="sigmoid",
        recurrent_dropout=float(recurrent_dropout),
        reset_after=True,
    )
    inp5 = Input(shape=(w_short, n_features), name="in5")
    inp20 = Input(shape=(w_mid, n_features), name="in20")
    inp60 = Input(shape=(w_long, n_features), name="in60")
    if float(input_noise_std) > 0:
        x5 = GaussianNoise(float(input_noise_std), name="noise5")(inp5)
        x20 = GaussianNoise(float(input_noise_std), name="noise20")(inp20)
        x60 = GaussianNoise(float(input_noise_std), name="noise60")(inp60)
    else:
        x5, x20, x60 = inp5, inp20, inp60

    if use_cnn_front:
        c = Conv1D(32, 3, padding="same", activation="relu")(x60)
        c = Conv1D(32, 3, padding="same", activation="relu")(c)
        g60 = _stack_gru(c, units_60, kwargs)
    else:
        g60 = _stack_gru(x60, units_60, kwargs)
    g5 = _stack_gru(x5, units_5, kwargs)
    g20 = _stack_gru(x20, units_20, kwargs)
    merged = Concatenate()([g5, g20, g60])

    d = Dense(int(dense_units[0]), activation="relu")(merged)
    d = Dropout(float(dropout))(d)
    d = Dense(int(dense_units[1]), activation="relu")(d)
    d = Dropout(float(dropout))(d)

    reg_head = Dense(1, activation="linear", name="reg_head")(d)
    cls_head = Dense(1, activation="sigmoid", name="cls_head")(d)

    model = Model(inputs=[inp5, inp20, inp60], outputs=[reg_head, cls_head])
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss={"reg_head": make_direction_aware_huber_loss(direction_lambda, huber_delta), "cls_head": "binary_crossentropy"},
        loss_weights={"reg_head": 1.0, "cls_head": float(cls_weight)},
        metrics={"cls_head": ["accuracy"]},
    )
    return model


def split_time_series_arrays(
    X: np.ndarray, y_reg: np.ndarray, y_cls: np.ndarray, train_ratio=0.7, val_ratio=0.15
):
    n = len(X)
    i_train = int(n * train_ratio)
    i_val = int(n * (train_ratio + val_ratio))
    return (
        (X[:i_train], y_reg[:i_train], y_cls[:i_train]),
        (X[i_train:i_val], y_reg[i_train:i_val], y_cls[i_train:i_val]),
        (X[i_val:], y_reg[i_val:], y_cls[i_val:]),
    )


def create_multiscale_sequences(
    X: np.ndarray,
    y_reg: np.ndarray,
    y_cls: np.ndarray,
    w_short: int = 5,
    w_mid: int = 20,
    w_long: int = 60,
):
    X5, X20, X60, yr, yc = [], [], [], [], []
    for i in range(w_long, len(X) + 1):
        X5.append(X[i - w_short : i])
        X20.append(X[i - w_mid : i])
        X60.append(X[i - w_long : i])
        yr.append(y_reg[i - 1])
        yc.append(y_cls[i - 1])
    return (
        np.asarray(X5, dtype=np.float32),
        np.asarray(X20, dtype=np.float32),
        np.asarray(X60, dtype=np.float32),
        np.asarray(yr, dtype=np.float32),
        np.asarray(yc, dtype=np.float32),
    )


def main():
    parser = argparse.ArgumentParser(description="纯噪声二分类 sanity test")
    parser.add_argument(
        "--base-path",
        default=r".\web_runs\run_20260413_144847_top10\_data\OilData",
        help="参考数据目录（用于读取样本数）",
    )
    parser.add_argument("--features", type=int, default=15, help="特征数，默认 15")
    parser.add_argument("--w-short", type=int, default=5, help="短窗口")
    parser.add_argument("--w-mid", type=int, default=20, help="中窗口")
    parser.add_argument("--w-long", type=int, default=60, help="长窗口")
    parser.add_argument("--epochs", type=int, default=60, help="训练轮数")
    parser.add_argument("--optuna-trials", type=int, default=30, help="Optuna 搜索 trial 数，0=不搜索")
    parser.add_argument("--optuna-epochs", type=int, default=100, help="Optuna 每个 trial 的最大训练轮数")
    parser.add_argument("--optuna-timeout", type=int, default=0, help="Optuna 超时秒数，0=不限时")
    parser.add_argument(
        "--params-csv",
        default=None,
        help="从 CSV（如 noise_optuna_best_params.csv）加载超参并直接训练，跳过 Optuna",
    )
    parser.add_argument("--batch-size", type=int, default=32, help="batch size")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--no-plots", action="store_true", help="不弹出图窗，仅保存 loss 图")
    parser.add_argument("--disable-early-stopping", action="store_true", help="关闭 EarlyStopping")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    tf.random.set_seed(args.seed)

    n_samples = load_sample_count(Path(args.base_path))
    n_features = int(args.features)

    w_short = int(args.w_short)
    w_mid = int(args.w_mid)
    w_long = int(args.w_long)
    if not (w_short < w_mid < w_long):
        raise ValueError("窗口要求: w_short < w_mid < w_long")

    # 纯高斯噪声特征 + 随机二分类标签（0/1）
    X = rng.normal(loc=0.0, scale=1.0, size=(n_samples, n_features)).astype(np.float32)
    y_cls = rng.integers(low=0, high=2, size=n_samples).astype(np.float32)

    # 线性头目标用同一标签的浮点形式，仅用于满足“双头”结构
    y_reg = y_cls.copy()

    (X_train, y_reg_train, y_cls_train), (X_val, y_reg_val, y_cls_val), (X_test, y_reg_test, y_cls_test) = split_time_series_arrays(
        X, y_reg, y_cls, train_ratio=0.7, val_ratio=0.15
    )
    X5_tr, X20_tr, X60_tr, yr_tr, yc_tr = create_multiscale_sequences(
        X_train, y_reg_train, y_cls_train, w_short, w_mid, w_long
    )
    X5_va, X20_va, X60_va, yr_va, yc_va = create_multiscale_sequences(
        X_val, y_reg_val, y_cls_val, w_short, w_mid, w_long
    )
    X5_te, X20_te, X60_te, yr_te, yc_te = create_multiscale_sequences(
        X_test, y_reg_test, y_cls_test, w_short, w_mid, w_long
    )

    base_train = (X5_tr, X20_tr, X60_tr, yr_tr, yc_tr)
    base_val = (X5_va, X20_va, X60_va, yr_va, yc_va)

    def train_with_params(params: dict, epochs: int, csv_log: str, trial=None):
        X5b, X20b, X60b, yrb, ycb = base_train
        n_orig_local = int(len(yrb))
        aug_copies = int(params.get("aug_copies", TRAIN_SEQ_AUG_COPIES))
        aug_noise = float(params.get("aug_noise_std", TRAIN_SEQ_AUG_NOISE_STD))
        if aug_copies > 0:
            aug_rng = np.random.default_rng(int(params.get("aug_seed", TRAIN_SEQ_AUG_SEED)))
            X5b, X20b, X60b, yrb, ycb = augment_train_sequences(
                X5b, X20b, X60b, yrb, ycb, aug_copies, aug_noise, aug_rng, clip01=True
            )

        model = build_model(
            n_features=n_features,
            w_short=w_short,
            w_mid=w_mid,
            w_long=w_long,
            units_5=params["units_5"],
            units_20=params["units_20"],
            units_60=params["units_60"],
            dense_units=params["dense_units"],
            dropout=float(params["dropout"]),
            learning_rate=float(params["learning_rate"]),
            recurrent_dropout=float(params["recurrent_dropout"]),
            input_noise_std=float(params["input_noise_std"]),
            use_cnn_front=bool(params["use_cnn_front"]),
            cls_weight=float(params["cls_weight"]),
            direction_lambda=float(params["direction_lambda"]),
            huber_delta=float(params["huber_delta"]),
        )
        callbacks = [
            ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=15, min_lr=1e-7, verbose=0 if trial else 1
            )
        ]
        if not args.disable_early_stopping:
            callbacks.append(EarlyStopping(monitor="val_loss", patience=12, restore_best_weights=True, verbose=0 if trial else 1))
        if trial is not None:
            callbacks.append(OptunaPruningCallback(trial, monitor="val_loss"))
        if csv_log:
            callbacks.append(CSVLogger(csv_log, append=False))

        history_local = model.fit(
            [X5b, X20b, X60b],
            {"reg_head": yrb, "cls_head": ycb},
            validation_data=([base_val[0], base_val[1], base_val[2]], {"reg_head": base_val[3], "cls_head": base_val[4]}),
            epochs=int(epochs),
            batch_size=int(params["batch_size"]),
            callbacks=callbacks,
            verbose=0 if trial else 1,
            shuffle=bool(aug_copies > 0),
        )
        best_val = float(np.min(history_local.history.get("val_loss", [1e9])))
        return model, history_local, best_val, n_orig_local, len(yrb)

    def default_params():
        return {
            "units_5": (48,),
            "units_20": (96,),
            "units_60": (128,),
            "dense_units": (128, 64),
            "dropout": DROPOUT_GRU_STACK,
            "learning_rate": LEARNING_RATE,
            "recurrent_dropout": RECURRENT_DROPOUT_GRU,
            "input_noise_std": GAUSSIAN_NOISE_INPUT,
            "use_cnn_front": USE_CNN_FRONT,
            "cls_weight": MULTITASK_CLS_WEIGHT,
            "direction_lambda": DIRECTION_LOSS_LAMBDA,
            "huber_delta": 1.0,
            "aug_copies": TRAIN_SEQ_AUG_COPIES,
            "aug_noise_std": TRAIN_SEQ_AUG_NOISE_STD,
            "aug_seed": TRAIN_SEQ_AUG_SEED,
            "batch_size": int(args.batch_size),
        }

    best_params = default_params()
    if args.params_csv:
        pcsv = Path(args.params_csv)
        if not pcsv.is_file():
            raise FileNotFoundError(f"找不到参数文件: {pcsv.resolve()}")
        best_params = load_params_from_csv(pcsv)
        print(f"已从 CSV 加载超参: {pcsv.resolve()}")
    elif int(args.optuna_trials) > 0:
        if optuna is None:
            raise ImportError("未安装 optuna，请先 pip install optuna")

        unit_choices = [16, 24, 32, 48, 64, 96, 128]

        def sample_units(trial, prefix, n_layers):
            vals = []
            for i in range(int(n_layers)):
                vals.append(trial.suggest_categorical(f"{prefix}_u{i+1}", unit_choices))
            return tuple(vals)

        def objective(trial):
            nl5 = trial.suggest_int("num_layers_5", 1, 3)
            nl20 = trial.suggest_int("num_layers_20", 1, 3)
            nl60 = trial.suggest_int("num_layers_60", 1, 3)
            p = {
                "units_5": sample_units(trial, "b5", nl5),
                "units_20": sample_units(trial, "b20", nl20),
                "units_60": sample_units(trial, "b60", nl60),
                "dense_units": (
                    trial.suggest_int("dense1", 64, 256, step=32),
                    trial.suggest_int("dense2", 32, 128, step=16),
                ),
                "dropout": trial.suggest_float("dropout", 0.10, 0.50),
                "learning_rate": trial.suggest_float("learning_rate", 1e-4, 5e-3, log=True),
                "recurrent_dropout": trial.suggest_float("recurrent_dropout", 0.0, 0.30),
                "input_noise_std": trial.suggest_float("input_noise_std", 0.0, 0.15),
                "use_cnn_front": trial.suggest_categorical("use_cnn_front", [True, False]),
                "cls_weight": trial.suggest_float("cls_weight", 0.1, 1.2),
                "direction_lambda": trial.suggest_float("direction_lambda", 0.0, 0.9),
                "huber_delta": trial.suggest_float("huber_delta", 0.3, 2.0),
                "aug_copies": trial.suggest_int("aug_copies", 0, 6),
                "aug_noise_std": trial.suggest_float("aug_noise_std", 0.02, 0.16),
                "aug_seed": int(args.seed),
                "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64]),
            }
            _, _, best_val_loss, _, _ = train_with_params(
                p, epochs=int(args.optuna_epochs), csv_log="", trial=trial
            )
            return best_val_loss

        pruner = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        study = optuna.create_study(direction="minimize", pruner=pruner, study_name="noise_binary_gru_tune")
        print(f"开始 Optuna 搜索: trials={args.optuna_trials}, optuna_epochs={args.optuna_epochs}")
        study.optimize(
            objective,
            n_trials=int(args.optuna_trials),
            timeout=None if int(args.optuna_timeout) <= 0 else int(args.optuna_timeout),
            show_progress_bar=False,
        )
        bt = study.best_trial
        print(f"Optuna 最优 val_loss={bt.value:.6f}, trial={bt.number}")
        # 重建 best_params（含 tuple 结构）
        best_params = {
            "units_5": tuple(bt.params[f"b5_u{i+1}"] for i in range(bt.params["num_layers_5"])),
            "units_20": tuple(bt.params[f"b20_u{i+1}"] for i in range(bt.params["num_layers_20"])),
            "units_60": tuple(bt.params[f"b60_u{i+1}"] for i in range(bt.params["num_layers_60"])),
            "dense_units": (bt.params["dense1"], bt.params["dense2"]),
            "dropout": bt.params["dropout"],
            "learning_rate": bt.params["learning_rate"],
            "recurrent_dropout": bt.params["recurrent_dropout"],
            "input_noise_std": bt.params["input_noise_std"],
            "use_cnn_front": bt.params["use_cnn_front"],
            "cls_weight": bt.params["cls_weight"],
            "direction_lambda": bt.params["direction_lambda"],
            "huber_delta": bt.params["huber_delta"],
            "aug_copies": bt.params["aug_copies"],
            "aug_noise_std": bt.params["aug_noise_std"],
            "aug_seed": int(args.seed),
            "batch_size": bt.params["batch_size"],
        }
        pd.DataFrame([{"best_val_loss": bt.value, **best_params}]).to_csv(
            "noise_optuna_best_params.csv", index=False, encoding="utf-8-sig"
        )
        print("已保存最优参数到 noise_optuna_best_params.csv")

    model, history, _, n_orig, n_aug = train_with_params(
        best_params, epochs=int(args.epochs), csv_log="noise_training_log.csv", trial=None
    )
    print(f"样本数: {n_samples}, 特征数: {n_features}, 窗口: {w_short}/{w_mid}/{w_long}")
    print(
        f"划分(序列后): train={n_aug}, val={len(yr_va)}, test={len(yr_te)}, "
        f"label1占比={y_cls.mean():.3f}"
    )
    print(
        f"训练序列增强: {n_orig} -> {n_aug} "
        f"(+{best_params['aug_copies']} 份噪声副本, noise_std={best_params['aug_noise_std']})"
    )

    # 训练/验证总 loss 曲线
    hist_df = pd.DataFrame(history.history)
    if "loss" in hist_df.columns and "val_loss" in hist_df.columns:
        plt.figure(figsize=(10, 5))
        plt.plot(hist_df["loss"].values, label="Train loss", color="#2563eb")
        plt.plot(hist_df["val_loss"].values, label="Val loss", color="#ea580c")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title("Noise Test - Train / Val Loss")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        loss_fig = Path("noise_loss_curve_train_val.png")
        plt.savefig(loss_fig, dpi=150, bbox_inches="tight")
        print(f"已保存 loss 曲线: {loss_fig.resolve()}")
        if args.no_plots:
            plt.close()
        else:
            plt.show()

    reg_pred, cls_pred = model.predict([X5_te, X20_te, X60_te], verbose=0)
    cls_prob = cls_pred.flatten()
    cls_hat = (cls_prob >= 0.5).astype(np.float32)
    acc = accuracy_score(yc_te, cls_hat)
    try:
        auc = roc_auc_score(yc_te, cls_prob)
    except Exception:
        auc = float("nan")

    print("\n===== 噪声数据集测试结果 =====")
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test ROC-AUC : {auc:.4f}")
    print("注：纯噪声任务理论上应接近随机猜测（Accuracy≈0.5, AUC≈0.5）。")

    out = pd.DataFrame(
        {
            "y_true": yc_te.astype(int),
            "cls_prob": cls_prob,
            "cls_pred": cls_hat.astype(int),
            "reg_pred": reg_pred.flatten(),
        }
    )
    out_path = Path("noise_test_predictions.csv")
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"已保存预测明细: {out_path.resolve()}")

    hist_path = Path("noise_test_history.csv")
    hist_df.to_csv(hist_path, index=False, encoding="utf-8-sig")
    print(f"已保存训练日志: {hist_path.resolve()}")


if __name__ == "__main__":
    main()
