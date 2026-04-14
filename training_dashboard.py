import csv
import os
import sys
import time
from datetime import datetime
from typing import Any


TRAIN_LOG_PATH = "training_log.csv"
PREDICTION_PATH = "prediction_results.csv"
REFRESH_SECONDS = 3


def _clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []


def _latest_training_metrics(rows: list[dict[str, str]]) -> dict[str, Any] | None:
    if not rows:
        return None
    last = rows[-1]
    epoch = last.get("epoch")
    if epoch is None or epoch == "":
        epoch = str(len(rows) - 1)
    loss = _safe_float(last.get("loss"))
    val_loss = _safe_float(last.get("val_loss"))
    return {
        "epoch": epoch,
        "loss": loss,
        "val_loss": val_loss,
        "num_rows": len(rows),
    }


def _prediction_summary(rows: list[dict[str, str]]) -> dict[str, Any] | None:
    if not rows:
        return None
    last = rows[-1]

    date_target = last.get("Date_target", "N/A")
    actual_price = _safe_float(last.get("Actual_P_t_plus_H"))
    pred_price = _safe_float(
        last.get("GRU_Pred_P_t_plus_H") or
        last.get("Predicted_Price")
    )
    actual_return = _safe_float(last.get("Actual_Return"))
    pred_return = _safe_float(last.get("GRU_Pred_Return"))

    return {
        "date_target": date_target,
        "actual_price": actual_price,
        "pred_price": pred_price,
        "actual_return": actual_return,
        "pred_return": pred_return,
        "num_rows": len(rows),
    }


def run_console_dashboard(auto_refresh: bool = True, refresh_seconds: int = REFRESH_SECONDS) -> None:
    while True:
        train_rows = _read_csv_rows(TRAIN_LOG_PATH)
        pred_rows = _read_csv_rows(PREDICTION_PATH)

        train_metrics = _latest_training_metrics(train_rows)
        pred_metrics = _prediction_summary(pred_rows)

        _clear_console()
        print("Oil Price Training Dashboard (Console Fallback)")
        print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        if train_metrics is None:
            print(f"[Training] Waiting for {TRAIN_LOG_PATH} ...")
        else:
            print("[Training]")
            print(f"Rows: {train_metrics['num_rows']}")
            print(f"Latest epoch: {train_metrics['epoch']}")
            print(f"Latest loss: {train_metrics['loss']}")
            print(f"Latest val_loss: {train_metrics['val_loss']}")

        print("-" * 60)

        if pred_metrics is None:
            print(f"[Prediction] Waiting for {PREDICTION_PATH} ...")
        else:
            print("[Prediction]")
            print(f"Rows: {pred_metrics['num_rows']}")
            print(f"Latest target date: {pred_metrics['date_target']}")
            print(f"Actual price: {pred_metrics['actual_price']}")
            print(f"GRU predicted price: {pred_metrics['pred_price']}")
            print(f"Actual return: {pred_metrics['actual_return']}")
            print(f"GRU predicted return: {pred_metrics['pred_return']}")

        if not auto_refresh:
            break
        time.sleep(refresh_seconds)


def run_streamlit_dashboard() -> None:
    import numpy as np
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="Oil Price Training Dashboard", layout="wide")
    st.title("Oil Price Training Dashboard")
    st.markdown(
        "Left: real-time `train/val loss`. Right: final prediction comparison after training."
    )

    @st.cache_data(ttl=5.0)
    def load_training_log(path: str = TRAIN_LOG_PATH) -> pd.DataFrame | None:
        try:
            return pd.read_csv(path)
        except FileNotFoundError:
            return None

    @st.cache_data(ttl=5.0)
    def load_prediction_results(path: str = PREDICTION_PATH) -> pd.DataFrame | None:
        try:
            return pd.read_csv(path, parse_dates=["Date_base", "Date_target"])
        except FileNotFoundError:
            return None

    auto_refresh = st.sidebar.checkbox("Auto refresh (every 3 seconds)", value=True)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Training: Train / Val Loss")
        placeholder_loss = st.empty()

    with col2:
        st.subheader("Final Prediction: Price and Return")
        placeholder_price = st.empty()
        placeholder_return = st.empty()

    def render_loss() -> None:
        df_log = load_training_log()
        if df_log is None or df_log.empty:
            placeholder_loss.info(f"Cannot find `{TRAIN_LOG_PATH}` in current directory.")
            return
        if "epoch" not in df_log.columns:
            df_log.insert(0, "epoch", np.arange(len(df_log)))

        chart_data = df_log[["epoch", "loss"]].rename(columns={"loss": "train_loss"})
        if "val_loss" in df_log.columns:
            chart_data["val_loss"] = df_log["val_loss"]

        placeholder_loss.line_chart(chart_data.set_index("epoch"))

    def render_predictions() -> None:
        df_pred = load_prediction_results()
        if df_pred is None or df_pred.empty:
            placeholder_price.info(f"Cannot find `{PREDICTION_PATH}` in current directory.")
            return

        placeholder_price.markdown("**Price: Actual vs GRU Predicted**")
        if {"Date_target", "Actual_P_t_plus_H", "GRU_Pred_P_t_plus_H"}.issubset(df_pred.columns):
            df_price = df_pred[["Date_target", "Actual_P_t_plus_H", "GRU_Pred_P_t_plus_H"]].copy()
            df_price = df_price.set_index("Date_target")
            df_price.columns = ["Actual_Price", "GRU_Pred_Price"]
            placeholder_price.line_chart(df_price)
        else:
            placeholder_price.info("Missing required price columns in prediction CSV.")

        if {"Actual_Return", "GRU_Pred_Return", "Date_target"}.issubset(df_pred.columns):
            placeholder_return.markdown("**Return: Actual vs GRU Predicted**")
            df_ret = df_pred[["Date_target", "Actual_Return", "GRU_Pred_Return"]].copy()
            df_ret = df_ret.set_index("Date_target")
            placeholder_return.line_chart(df_ret)
        else:
            placeholder_return.info("Return columns not found: Actual_Return / GRU_Pred_Return.")

    while True:
        render_loss()
        render_predictions()

        if auto_refresh:
            time.sleep(REFRESH_SECONDS)
            st.rerun()


def main() -> None:
    try:
        import streamlit  # noqa: F401
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            run_streamlit_dashboard()
            return
    except ModuleNotFoundError:
        pass
    except Exception:
        # Any streamlit runtime edge case should still leave the dashboard usable.
        pass

    auto_refresh = "--once" not in sys.argv
    if "--streamlit-only" in sys.argv:
        print("Streamlit runtime is not active. Launch with: streamlit run training_dashboard.py")
        return
    run_console_dashboard(auto_refresh=auto_refresh, refresh_seconds=REFRESH_SECONDS)


if __name__ == "__main__":
    main()
