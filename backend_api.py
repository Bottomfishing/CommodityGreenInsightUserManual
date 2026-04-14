import io
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse


APP_DIR = Path(__file__).resolve().parent
WEB_RUNS_DIR = APP_DIR / "web_runs"
SCRIPT_NAME = "oil_price_prediction_main_0309.py"
NE_SCRIPT_NAME = "run_new_energy_forecast_integrated_0325.py"
BOND_SCRIPT_NAME = "predict_bond_from_gru.py"
PIPELINE_SCRIPT_NAME = "Data_Pipeline.py"
DEFAULT_BOND_DATA_CSV = APP_DIR / "bond_date" / "data.csv"
DEFAULT_BOND_ZIP = APP_DIR / "bond_data.zip"
DEFAULT_BOND_DIR = APP_DIR / "bond_data"
GLOBAL_LOCK_PATH = APP_DIR / ".app_global_job.lock"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
AI_BASE_URL = os.environ.get("YIBU_BASE_URL", "https://yibuapi.com/v1")
AI_API_KEY = os.environ.get("YIBU_API_KEY", "")
AI_MODEL = os.environ.get("YIBU_MODEL", "gpt-4o")

_GLOBAL_MUTEX = threading.Lock()
_PROCESS_POOL: dict[str, subprocess.Popen[str]] = {}


app = FastAPI(
    title="大宗绿测后端 API",
    version="2.0.0",
    description=(
        "将原 Streamlit 功能拆分为后端接口：油价训练、训练监控、结果预览、"
        "新能源整合预测、绿债预测、AI报告与下载导出。"
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_json_extract_content(data: dict[str, Any]) -> str | None:
    try:
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None


def _call_chat_completion(messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 2048) -> str:
    if not AI_API_KEY:
        raise RuntimeError("未配置 YIBU_API_KEY，无法调用 AI。")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
    }
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{AI_BASE_URL}/chat/completions", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        raise RuntimeError(f"AI 请求失败: {exc}") from exc
    content = _safe_json_extract_content(data)
    if not content:
        raise RuntimeError(f"AI 响应解析失败: {str(data)[:400]}")
    return str(content)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "message": "大宗绿测后端服务已启动",
        "docs": "/docs",
        "health": "/health",
        "api_example": "/api/oil/runs",
    }


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text or "")


def _pid_alive(pid: int) -> bool:
    try:
        p = int(pid)
    except Exception:
        return False
    if p <= 0:
        return False
    if os.name == "nt":
        try:
            res = subprocess.run(
                ["tasklist", "/FI", f"PID eq {p}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            out = (res.stdout or "").strip()
            if not out:
                return False
            first = out.splitlines()[0].strip() if out.splitlines() else ""
            if first.upper().startswith("INFO:"):
                return False
            return str(p) in out
        except Exception:
            return True
    try:
        os.kill(p, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return True


def _read_global_lock() -> dict[str, Any] | None:
    try:
        if not GLOBAL_LOCK_PATH.is_file():
            return None
        raw = GLOBAL_LOCK_PATH.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _write_global_lock(pid: int, run_id: str, output_dir: str) -> None:
    payload = {
        "pid": int(pid),
        "kind": "oil",
        "run_id": run_id,
        "output_dir": str(Path(output_dir).resolve()),
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    GLOBAL_LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _clear_global_lock_if_pid(pid: int | None) -> None:
    try:
        p = int(pid) if pid is not None else 0
    except Exception:
        p = 0
    if p <= 0:
        return
    data = _read_global_lock()
    if not data:
        return
    try:
        lock_pid = int(data.get("pid", -1))
    except Exception:
        lock_pid = -1
    if lock_pid != p:
        return
    try:
        GLOBAL_LOCK_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def _global_busy() -> dict[str, Any] | None:
    lock = _read_global_lock()
    if not lock:
        return None
    pid = int(lock.get("pid", 0) or 0)
    if pid <= 0:
        try:
            GLOBAL_LOCK_PATH.unlink(missing_ok=True)
        except Exception:
            pass
        return None
    if _pid_alive(pid):
        return lock
    try:
        GLOBAL_LOCK_PATH.unlink(missing_ok=True)
    except Exception:
        pass
    return None


def _extract_zip_to_dir(zip_bytes: bytes, target_dir: Path) -> None:
    def _fix_name(name: str) -> str:
        try:
            fixed = name.encode("cp437").decode("gbk")
            if any(ch in fixed for ch in ["能源", "基本面", "下游", "产业", "原油", "供需", "地缘"]):
                return fixed
        except Exception:
            pass
        return name

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            fixed_name = _fix_name(info.filename).replace("\\", "/")
            dest = target_dir / fixed_name
            if info.filename.endswith("/") or fixed_name.endswith("/"):
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)


def _find_data_root(extracted_dir: Path) -> Path:
    raw_a = extracted_dir / "raw_data"
    energy_a = extracted_dir / "能源基本面与下游产业"
    if raw_a.is_dir() and energy_a.is_dir():
        return extracted_dir
    children = [p for p in extracted_dir.iterdir() if p.is_dir()]
    if len(children) == 1:
        raw_b = children[0] / "raw_data"
        energy_b = children[0] / "能源基本面与下游产业"
        if raw_b.is_dir() and energy_b.is_dir():
            return children[0]
    for root, dirs, _ in os.walk(extracted_dir):
        if "raw_data" in dirs and "能源基本面与下游产业" in dirs:
            return Path(root)
    return extracted_dir


def _validate_data_root(data_root: Path) -> tuple[bool, str]:
    raw_dir = data_root / "raw_data"
    energy_dir = data_root / "能源基本面与下游产业"
    if not raw_dir.is_dir() or not energy_dir.is_dir():
        return False, "未找到 raw_data/ 与 能源基本面与下游产业/ 目录"
    required = raw_dir / "WTI_futuresprice.csv"
    if not required.is_file():
        return False, "缺少 raw_data/WTI_futuresprice.csv"
    return True, "OK"


def _file_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False}
    try:
        return {
            "exists": True,
            "size": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
    except Exception:
        return {"exists": True}


def _list_run_dirs() -> list[Path]:
    if not WEB_RUNS_DIR.is_dir():
        return []
    runs = [p for p in WEB_RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("run_")]
    return sorted(runs, key=lambda x: x.name, reverse=True)


def _read_csv_preview(path: Path, rows: int = 50) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "columns": [], "rows": []}
    df = pd.read_csv(path).head(rows)
    return {"exists": True, "columns": df.columns.tolist(), "rows": df.to_dict(orient="records")}


def _start_background_cmd(
    cmd: list[str],
    *,
    output_dir: Path,
    log_filename: str,
    started_marker_filename: str,
    lock_kind: str,
    lock_run_id: str,
) -> tuple[int, str]:
    with _GLOBAL_MUTEX:
        busy = _global_busy()
        if busy:
            raise HTTPException(status_code=409, detail=f"当前已有任务运行中: {busy.get('output_dir', '')}")
        output_dir.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            cmd,
            cwd=str(APP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
        _PROCESS_POOL[lock_run_id] = proc
        _write_global_lock(proc.pid, run_id=lock_run_id, output_dir=str(output_dir.resolve()))
        lock = _read_global_lock() or {}
        lock["kind"] = lock_kind
        GLOBAL_LOCK_PATH.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")

    log_path = output_dir / log_filename
    marker_path = output_dir / started_marker_filename
    marker_path.write_text(
        f"started_at={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\npid={proc.pid}\n",
        encoding="utf-8",
    )

    def _pump() -> None:
        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(f"[backend:{lock_kind}] started_at={datetime.now().isoformat()} pid={proc.pid}\n")
                if proc.stdout is not None:
                    for line in proc.stdout:
                        f.write(_strip_ansi(line))
                        f.flush()
        finally:
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            _clear_global_lock_if_pid(proc.pid)

    threading.Thread(target=_pump, daemon=True).start()
    return proc.pid, str(output_dir.resolve())


def _generate_enterprise_bank_ai_report(run_dir: Path, force: bool = False) -> str | None:
    report_md = run_dir / "bank_team_report.md"
    ai_md = run_dir / "bank_team_report_ai.md"
    if not report_md.is_file():
        return None
    if not force and ai_md.is_file() and ai_md.stat().st_mtime >= report_md.stat().st_mtime:
        return ai_md.read_text(encoding="utf-8", errors="replace")
    base_text = report_md.read_text(encoding="utf-8", errors="replace")
    ctx = ""
    pred_csv = run_dir / "prediction_results.csv"
    if pred_csv.is_file():
        try:
            df = pd.read_csv(pred_csv)
            if not df.empty and "GRU_Pred_Return" in df.columns:
                ctx = f"样本数={len(df)}; 预测收益均值={float(df['GRU_Pred_Return'].mean()):.6f}"
        except Exception:
            ctx = ""

    sys_prompt = (
        "你是油价预测与风险分析专家。"
        "请基于输入的模型报告，为企业银行团队生成执行摘要。"
        "用中文输出 Markdown，包含：核心结论、风险关注点、跟踪指标、合规提示。"
        "不得编造报告中不存在的数据。"
    )
    user_prompt = f"【模型报告】\n{base_text}\n\n【数据摘要】\n{ctx or '无'}"
    answer = _call_chat_completion(
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.25,
        max_tokens=2800,
    ).strip()
    if not answer:
        return None
    ai_md.write_text(answer + "\n", encoding="utf-8")
    return answer


def _tail_text(path: Path, max_lines: int = 200) -> str:
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(_strip_ansi(x) for x in lines[-max_lines:])
    except Exception:
        return ""


def _parse_keras_loss_from_run_log(run_log_path: Path) -> pd.DataFrame | None:
    if not run_log_path.is_file():
        return None
    try:
        lines = run_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None
    epoch_re = re.compile(r"^Epoch\s+(\d+)\s*/\s*(\d+)\s*$")
    loss_re = re.compile(r"(?:^|\s)loss:\s*([0-9]*\.?[0-9]+)(?:\s|$)")
    val_loss_re = re.compile(r"(?:^|\s)val_loss:\s*([0-9]*\.?[0-9]+)(?:\s|$)")
    rows: list[dict[str, Any]] = []
    current_epoch: int | None = None
    for line in lines:
        s = _strip_ansi(line).strip()
        m_epoch = epoch_re.match(s)
        if m_epoch:
            current_epoch = int(m_epoch.group(1))
            continue
        if current_epoch is None or "loss" not in s:
            continue
        m_loss = loss_re.search(s)
        if not m_loss:
            continue
        try:
            loss_val = float(m_loss.group(1))
        except Exception:
            continue
        v = None
        m_v = val_loss_re.search(s)
        if m_v:
            try:
                v = float(m_v.group(1))
            except Exception:
                v = None
        rows.append({"epoch": current_epoch, "loss": loss_val, "val_loss": v})
        current_epoch = None
    if not rows:
        return None
    df = pd.DataFrame(rows).drop_duplicates(subset=["epoch"], keep="last").sort_values("epoch")
    return df


def _file_recently_updated(path: Path, seconds: int = 30) -> bool:
    try:
        return path.is_file() and (datetime.now().timestamp() - path.stat().st_mtime) <= seconds
    except Exception:
        return False


def _run_dir_is_recently_started(run_dir: Path, seconds: int = 120) -> bool:
    return _file_recently_updated(run_dir / "run.started", seconds=seconds)


def _pick_most_recent_active_run_dir(run_dirs: list[Path]) -> Path | None:
    best: Path | None = None
    best_mtime = -1.0
    for d in run_dirs:
        p_started = d / "run.started"
        p_log = d / "run.log"
        p = p_started if p_started.is_file() else (p_log if p_log.is_file() else None)
        if p is None:
            continue
        try:
            m = p.stat().st_mtime
            if m > best_mtime:
                best_mtime = m
                best = d.resolve()
        except Exception:
            continue
    return best


def _run_status(run_dir: Path) -> dict[str, Any]:
    run_id = run_dir.name
    proc = _PROCESS_POOL.get(run_id)
    code = proc.poll() if proc is not None else None
    lock = _global_busy()
    if lock and Path(lock.get("output_dir", "")).resolve() == run_dir.resolve():
        status = "running"
    elif code == 0:
        status = "success"
    elif code is None and (run_dir / "run.log").is_file() and (run_dir / "prediction_results.csv").is_file():
        status = "likely_success"
    elif code is not None and code != 0:
        status = "failed"
    else:
        status = "unknown"
    return {
        "run_id": run_id,
        "status": status,
        "return_code": code,
        "output_dir": str(run_dir.resolve()),
        "started_marker_exists": (run_dir / "run.started").is_file(),
        "prediction_exists": (run_dir / "prediction_results.csv").is_file(),
        "oil_pred_exists": (run_dir / "oil_pred.csv").is_file(),
        "run_log_exists": (run_dir / "run.log").is_file(),
    }


def _terminate_pid_tree(pid: int | None) -> None:
    if not pid:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "time": datetime.now().isoformat()}


@app.get("/api/system/status", summary="系统状态")
def get_system_status() -> dict[str, Any]:
    busy = _global_busy()
    runs = _list_run_dirs()
    return {
        "global_busy": bool(busy),
        "global_lock": busy,
        "run_count": len(runs),
        "latest_run_id": runs[0].name if runs else None,
    }


@app.get("/api/oil/monitor/resolve", summary="解析训练监控目录")
def resolve_monitor_dir(
    mode: str = Query("latest", description="running|active_by_log|selected|latest|manual"),
    selected_run_id: str | None = Query(None),
    manual_dir: str | None = Query(None),
) -> dict[str, Any]:
    run_dirs = _list_run_dirs()
    running_lock = _global_busy()
    running_dir = Path(str(running_lock.get("output_dir"))) if running_lock else None
    active_dir = _pick_most_recent_active_run_dir(run_dirs)
    latest_dir = run_dirs[0].resolve() if run_dirs else None
    selected_dir = (WEB_RUNS_DIR / selected_run_id).resolve() if selected_run_id else None
    manual_path = Path(manual_dir).resolve() if manual_dir else None

    monitor_dir: Path | None = None
    if mode == "running":
        monitor_dir = running_dir
    elif mode == "active_by_log":
        monitor_dir = active_dir
    elif mode == "selected":
        monitor_dir = selected_dir if selected_dir and selected_dir.is_dir() else None
    elif mode == "manual":
        monitor_dir = manual_path if manual_path and manual_path.is_dir() else None
    else:
        monitor_dir = latest_dir

    return {
        "mode": mode,
        "monitor_dir": str(monitor_dir) if monitor_dir else None,
        "running_dir": str(running_dir) if running_dir else None,
        "active_by_log_dir": str(active_dir) if active_dir else None,
        "latest_dir": str(latest_dir) if latest_dir else None,
    }


@app.post("/api/oil/runs")
async def create_oil_run(
    zip_file: UploadFile = File(...),
    top_n: int = Form(10),
    epochs: int = Form(200),
    forecast_steps: int = Form(1),
    cutoff_date: str | None = Form(None),
    enable_early_stopping: bool = Form(True),
    auto_bond_after_oil: bool = Form(False),
) -> dict[str, Any]:
    if not zip_file.filename or not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 zip 数据包")
    if top_n < 5 or top_n > 200:
        raise HTTPException(status_code=400, detail="top_n 必须在 5~200")
    if epochs < 1 or epochs > 2000:
        raise HTTPException(status_code=400, detail="epochs 必须在 1~2000")
    if forecast_steps < 0 or forecast_steps > 90:
        raise HTTPException(status_code=400, detail="forecast_steps 必须在 0~90")

    with _GLOBAL_MUTEX:
        busy = _global_busy()
        if busy:
            raise HTTPException(
                status_code=409,
                detail=f"当前已有任务运行中: {busy.get('output_dir', '')}",
            )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"run_{ts}_top{top_n}"
        run_dir = WEB_RUNS_DIR / run_id
        data_dir = run_dir / "_data"
        run_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        try:
            zip_bytes = await zip_file.read()
            _extract_zip_to_dir(zip_bytes, data_dir)
            data_root = _find_data_root(data_dir)
            ok, msg = _validate_data_root(data_root)
            if not ok:
                raise HTTPException(status_code=400, detail=msg)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"解压或校验失败: {exc}") from exc

        cmd = [
            "python",
            "-u",
            SCRIPT_NAME,
            "--base-path",
            str(data_root.resolve()),
            "--top-n",
            str(int(top_n)),
            "--epochs",
            str(int(epochs)),
            "--output-dir",
            str(run_dir.resolve()),
            "--no-plots",
        ]
        if not enable_early_stopping:
            cmd.append("--disable-early-stopping")
        if cutoff_date:
            cmd.extend(["--cutoff-date", cutoff_date])
        if int(forecast_steps) > 0:
            cmd.extend(["--forecast-steps", str(int(forecast_steps))])

        log_path = run_dir / "run.log"
        started_path = run_dir / "run.started"
        started_path.write_text(
            "\n".join(
                [
                    f"started_at={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"top_n={top_n}",
                    f"epochs={epochs}",
                    f"forecast_steps={forecast_steps}",
                    f"cutoff_date={cutoff_date or ''}",
                ]
            ),
            encoding="utf-8",
        )

        proc = subprocess.Popen(
            cmd,
            cwd=str(APP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
        _PROCESS_POOL[run_id] = proc
        _write_global_lock(proc.pid, run_id=run_id, output_dir=str(run_dir.resolve()))

        def _pump() -> None:
            try:
                with open(log_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(f"[backend] started_at={datetime.now().isoformat()} pid={proc.pid}\n")
                    if proc.stdout is not None:
                        for line in proc.stdout:
                            f.write(_strip_ansi(line))
                            f.flush()
            finally:
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                _clear_global_lock_if_pid(proc.pid)
                # 与 streamlit 行为对齐：油价成功后可自动触发绿债预测
                try:
                    if bool(auto_bond_after_oil) and proc.returncode == 0:
                        oil_pred = run_dir / "oil_pred.csv"
                        if oil_pred.is_file():
                            data_csv_to_use = DEFAULT_BOND_DATA_CSV
                            if DEFAULT_BOND_ZIP.is_file():
                                auto_data_dir = run_dir / "_auto_bond_data"
                                auto_data_dir.mkdir(parents=True, exist_ok=True)
                                _extract_zip_to_dir(DEFAULT_BOND_ZIP.read_bytes(), auto_data_dir)
                                data_root = _find_data_root(auto_data_dir)
                                pipeline_script = APP_DIR / PIPELINE_SCRIPT_NAME
                                if pipeline_script.is_file():
                                    processed_csv_path = run_dir / "auto_bond_processed.csv"
                                    res = subprocess.run(
                                        [
                                            "python",
                                            "-u",
                                            str(pipeline_script),
                                            "--data-root",
                                            str(data_root),
                                            "--output-csv",
                                            str(processed_csv_path),
                                        ],
                                        capture_output=True,
                                        text=True,
                                    )
                                    if res.returncode == 0 and processed_csv_path.is_file():
                                        data_csv_to_use = processed_csv_path
                            elif DEFAULT_BOND_DIR.is_dir():
                                data_root = _find_data_root(DEFAULT_BOND_DIR)
                                pipeline_script = APP_DIR / PIPELINE_SCRIPT_NAME
                                if pipeline_script.is_file():
                                    processed_csv_path = run_dir / "auto_bond_processed.csv"
                                    res = subprocess.run(
                                        [
                                            "python",
                                            "-u",
                                            str(pipeline_script),
                                            "--data-root",
                                            str(data_root),
                                            "--output-csv",
                                            str(processed_csv_path),
                                        ],
                                        capture_output=True,
                                        text=True,
                                    )
                                    if res.returncode == 0 and processed_csv_path.is_file():
                                        data_csv_to_use = processed_csv_path
                            if (APP_DIR / BOND_SCRIPT_NAME).is_file() and data_csv_to_use.is_file():
                                bond_out = run_dir / "bond_integrated_output"
                                bond_cmd = [
                                    "python",
                                    "-u",
                                    str((APP_DIR / BOND_SCRIPT_NAME).resolve()),
                                    "--data-csv",
                                    str(data_csv_to_use.resolve()),
                                    "--oil-pred-csv",
                                    str(oil_pred.resolve()),
                                    "--out-dir",
                                    str(bond_out.resolve()),
                                    "--output-csv",
                                    "bond_forecast_with_confidence.csv",
                                ]
                                _start_background_cmd(
                                    bond_cmd,
                                    output_dir=bond_out,
                                    log_filename="bond_run.log",
                                    started_marker_filename="bond_run.started",
                                    lock_kind="bond",
                                    lock_run_id=f"bond:auto:{run_id}",
                                )
                except Exception:
                    pass

        threading.Thread(target=_pump, daemon=True).start()

    return {
        "message": "任务已启动",
        "run_id": run_id,
        "pid": proc.pid,
        "output_dir": str(run_dir.resolve()),
    }


@app.get("/api/oil/runs")
def list_oil_runs(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
    if not WEB_RUNS_DIR.is_dir():
        return {"items": []}
    runs = [p for p in WEB_RUNS_DIR.iterdir() if p.is_dir() and p.name.startswith("run_")]
    runs = sorted(runs, key=lambda x: x.name, reverse=True)[:limit]
    return {"items": [_run_status(r) for r in runs]}


@app.get("/api/oil/runs/{run_id}")
def get_oil_run(run_id: str) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    payload = _run_status(run_dir)
    payload["files"] = sorted([p.name for p in run_dir.iterdir() if p.is_file()])
    return payload


@app.get("/api/oil/runs/{run_id}/overview", summary="结果总览", description="聚合训练监控、结果预览、下载页核心信息")
def get_oil_run_overview(run_id: str) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")

    key_files = [
        "run.log",
        "training_log.csv",
        "prediction_results.csv",
        "daily_predictions_vs_actual.csv",
        "future_forecast.csv",
        "bank_team_report.md",
        "bank_team_report_ai.md",
        "driver_factor_analysis.csv",
        "risk_signal_classification.csv",
        "backtest_metrics.csv",
        "backtest_results.csv",
        "oil_pred.csv",
    ]
    images = [
        "future_forecast.png",
        "gru_predictions.png",
        "gru_returns.png",
        "direction_confusion_matrix.png",
        "top_drivers_spearman.png",
        "top_drivers_rf_importance.png",
        "backtest_nav_curve.png",
    ]
    return {
        "run_id": run_id,
        "status": _run_status(run_dir),
        "file_status": {name: _file_status(run_dir / name) for name in key_files},
        "images": [n for n in images if (run_dir / n).is_file()],
    }


@app.get("/api/oil/runs/{run_id}/training-dashboard", summary="训练监控图表数据")
def get_training_dashboard_data(run_id: str, rows: int = Query(2000, ge=10, le=20000)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    log_csv = run_dir / "training_log.csv"
    run_log = run_dir / "run.log"
    pred_csv = run_dir / "prediction_results.csv"

    loss_rows: list[dict[str, Any]] = []
    if log_csv.is_file():
        try:
            df = pd.read_csv(log_csv).head(rows)
            if "epoch" not in df.columns:
                df.insert(0, "epoch", list(range(len(df))))
            cols = [c for c in ["epoch", "loss", "val_loss"] if c in df.columns]
            loss_rows = df[cols].to_dict(orient="records")
        except Exception:
            loss_rows = []
    if not loss_rows:
        df_loss = _parse_keras_loss_from_run_log(run_log)
        if df_loss is not None and not df_loss.empty:
            loss_rows = df_loss.head(rows).to_dict(orient="records")

    price_rows: list[dict[str, Any]] = []
    return_rows: list[dict[str, Any]] = []
    if pred_csv.is_file():
        try:
            dfp = pd.read_csv(pred_csv).head(rows)
            if {"Date_target", "Actual_P_t_plus_H", "GRU_Pred_P_t_plus_H"}.issubset(dfp.columns):
                price_rows = dfp[["Date_target", "Actual_P_t_plus_H", "GRU_Pred_P_t_plus_H"]].to_dict(orient="records")
            if {"Date_target", "Actual_Return", "GRU_Pred_Return"}.issubset(dfp.columns):
                return_rows = dfp[["Date_target", "Actual_Return", "GRU_Pred_Return"]].to_dict(orient="records")
        except Exception:
            pass

    run_log_active = _file_recently_updated(run_log, seconds=30)
    started_fresh = _run_dir_is_recently_started(run_dir, seconds=120)
    return {
        "run_id": run_id,
        "loss_series": loss_rows,
        "price_series": price_rows,
        "return_series": return_rows,
        "run_log_tail": _tail_text(run_log, max_lines=120),
        "is_log_active": run_log_active,
        "is_recently_started": started_fresh,
    }


@app.get("/api/oil/runs/{run_id}/log")
def get_oil_run_log(run_id: str, lines: int = Query(200, ge=20, le=2000)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    content = _tail_text(run_dir / "run.log", max_lines=lines)
    return {"run_id": run_id, "log_tail": content}


@app.get("/api/oil/runs/{run_id}/prediction-preview")
def get_prediction_preview(run_id: str, rows: int = Query(30, ge=1, le=500)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    pred_csv = run_dir / "prediction_results.csv"
    if not pred_csv.is_file():
        raise HTTPException(status_code=404, detail="prediction_results.csv 尚未生成")
    try:
        df = pd.read_csv(pred_csv).head(rows)
        return {"run_id": run_id, "columns": df.columns.tolist(), "rows": df.to_dict(orient="records")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取 prediction_results.csv 失败: {exc}") from exc


@app.get("/api/oil/runs/{run_id}/csv-preview", summary="预览指定 CSV")
def get_csv_preview(
    run_id: str,
    name: str = Query(..., description="文件名，例如 prediction_results.csv"),
    rows: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    target = (run_dir / name).resolve()
    if target.parent != run_dir.resolve():
        raise HTTPException(status_code=400, detail="仅允许读取当前 run 目录下的文件")
    if target.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="仅支持 CSV 预览")
    try:
        return {"run_id": run_id, "file": name, **_read_csv_preview(target, rows=rows)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取 CSV 失败: {exc}") from exc


@app.post("/api/oil/runs/{run_id}/stop")
def stop_oil_run(run_id: str) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")

    proc = _PROCESS_POOL.get(run_id)
    pid: int | None = None
    if proc is not None:
        pid = proc.pid
    if not pid:
        lock = _read_global_lock()
        if lock and lock.get("run_id") == run_id:
            pid = int(lock.get("pid", 0) or 0)
    if not pid:
        raise HTTPException(status_code=409, detail="未找到可停止的运行进程")

    _terminate_pid_tree(pid)
    _clear_global_lock_if_pid(pid)
    return {"message": "已发送停止信号", "run_id": run_id, "pid": pid}


@app.get("/api/oil/runs/{run_id}/files")
def get_oil_run_files(run_id: str) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    files = []
    for p in sorted(run_dir.iterdir(), key=lambda x: x.name):
        if p.is_file():
            files.append({"name": p.name, "size": p.stat().st_size})
    return {"run_id": run_id, "files": files}


@app.get("/api/oil/runs/{run_id}/download", summary="下载 run 目录文件")
def download_oil_run_file(run_id: str, name: str = Query(..., description="文件名")) -> FileResponse:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    target = (run_dir / name).resolve()
    if target.parent != run_dir.resolve():
        raise HTTPException(status_code=400, detail="非法路径")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=str(target), filename=target.name, media_type="application/octet-stream")


@app.get("/api/oil/runs/{run_id}/export.zip", summary="导出 run 目录为 zip")
def export_oil_run_zip(run_id: str) -> StreamingResponse:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in run_dir.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(run_dir))
    mem.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="{run_id}.zip"'}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)


@app.post("/api/oil/runs/{run_id}/new-energy", summary="启动新能源整合预测")
async def start_new_energy_run(
    run_id: str,
    ne_zip_file: UploadFile = File(..., description="新能源数据 zip"),
    series: str = Form("new_energy"),
    conf_level: float = Form(0.95),
    scale_oil_return: float = Form(100.0),
    make_viz: bool = Form(True),
    rebuild_returns: bool = Form(False),
) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    oil_pred_csv = run_dir / "prediction_results.csv"
    if not oil_pred_csv.is_file():
        raise HTTPException(status_code=400, detail="缺少 prediction_results.csv，请先完成油价预测")
    if not ne_zip_file.filename or not ne_zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="ne_zip_file 必须是 zip")
    script_path = APP_DIR / NE_SCRIPT_NAME
    if not script_path.is_file():
        raise HTTPException(status_code=500, detail=f"找不到脚本: {NE_SCRIPT_NAME}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ne_run_dir = run_dir / "new_energy_runs" / f"new_energy_{ts}"
    ne_data_dir = ne_run_dir / "_data"
    ne_data_dir.mkdir(parents=True, exist_ok=True)
    _extract_zip_to_dir(await ne_zip_file.read(), ne_data_dir)

    cmd = [
        "python",
        "-u",
        str(script_path),
        "--oil-pred-csv",
        str(oil_pred_csv.resolve()),
        "--series",
        series,
        "--conf-level",
        str(float(conf_level)),
        "--scale-oil-return",
        str(float(scale_oil_return)),
        "--out-dir",
        str(ne_run_dir.resolve()),
        "--desktop-base",
        str(ne_data_dir.resolve()),
    ]
    if rebuild_returns:
        cmd.append("--rebuild-returns")
    if make_viz:
        cmd.append("--make-viz")

    ne_task_id = f"new_energy:{run_id}:{ne_run_dir.name}"
    pid, out_dir = _start_background_cmd(
        cmd,
        output_dir=ne_run_dir,
        log_filename="new_energy_run.log",
        started_marker_filename="new_energy_run.started",
        lock_kind="new_energy",
        lock_run_id=ne_task_id,
    )
    return {"message": "新能源整合预测已启动", "run_id": run_id, "pid": pid, "new_energy_output_dir": out_dir}


@app.get("/api/oil/runs/{run_id}/new-energy/latest", summary="查看最近一次新能源整合预测结果")
def get_latest_new_energy_result(run_id: str, rows: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    ne_root = run_dir / "new_energy_runs"
    if not ne_root.is_dir():
        raise HTTPException(status_code=404, detail="还没有新能源运行记录")
    candidates = [p for p in ne_root.iterdir() if p.is_dir() and p.name.startswith("new_energy_")]
    if not candidates:
        raise HTTPException(status_code=404, detail="还没有新能源运行记录")
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest = candidates[0]
    log_text = _tail_text(latest / "new_energy_run.log", max_lines=200)
    csv_candidates = list(latest.glob("*.csv"))
    preview = _read_csv_preview(csv_candidates[0], rows=rows) if csv_candidates else {"exists": False, "rows": []}
    images = [p.name for p in latest.glob("*.png")]
    return {
        "run_id": run_id,
        "latest_dir": str(latest.resolve()),
        "log_tail": log_text,
        "images": images,
        "csv_preview": preview,
    }


@app.post("/api/oil/runs/{run_id}/bond", summary="启动绿债预测")
async def start_bond_run(
    run_id: str,
    bond_zip_file: UploadFile | None = File(default=None, description="可选：上传绿债数据 zip"),
) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    oil_pred = run_dir / "oil_pred.csv"
    if not oil_pred.is_file():
        raise HTTPException(status_code=400, detail="缺少 oil_pred.csv，请先完成油价预测")
    bond_script = APP_DIR / BOND_SCRIPT_NAME
    if not bond_script.is_file():
        raise HTTPException(status_code=500, detail=f"找不到脚本: {BOND_SCRIPT_NAME}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bond_run_dir = run_dir / "bond_user_runs" / f"bond_{ts}"
    bond_run_dir.mkdir(parents=True, exist_ok=True)
    processed_csv_path = bond_run_dir / "processed.csv"
    data_csv_to_use = DEFAULT_BOND_DATA_CSV

    data_root: Path | None = None
    if bond_zip_file is not None:
        bond_data_dir = bond_run_dir / "_data"
        bond_data_dir.mkdir(parents=True, exist_ok=True)
        _extract_zip_to_dir(await bond_zip_file.read(), bond_data_dir)
        data_root = _find_data_root(bond_data_dir)
    elif DEFAULT_BOND_ZIP.is_file():
        bond_data_dir = bond_run_dir / "_data"
        bond_data_dir.mkdir(parents=True, exist_ok=True)
        _extract_zip_to_dir(DEFAULT_BOND_ZIP.read_bytes(), bond_data_dir)
        data_root = _find_data_root(bond_data_dir)
    elif DEFAULT_BOND_DIR.is_dir():
        data_root = _find_data_root(DEFAULT_BOND_DIR)

    if data_root is not None:
        pipeline_script = APP_DIR / PIPELINE_SCRIPT_NAME
        if not pipeline_script.is_file():
            raise HTTPException(status_code=500, detail=f"找不到脚本: {PIPELINE_SCRIPT_NAME}")
        result = subprocess.run(
            ["python", "-u", str(pipeline_script), "--data-root", str(data_root), "--output-csv", str(processed_csv_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Data_Pipeline 运行失败\n{result.stdout}\n{result.stderr}")
        data_csv_to_use = processed_csv_path

    if not data_csv_to_use.is_file():
        raise HTTPException(status_code=500, detail=f"绿债数据文件不存在: {data_csv_to_use}")

    bond_out = bond_run_dir / "bond_integrated_output"
    cmd = [
        "python",
        "-u",
        str(bond_script),
        "--data-csv",
        str(data_csv_to_use.resolve()),
        "--oil-pred-csv",
        str(oil_pred.resolve()),
        "--out-dir",
        str(bond_out.resolve()),
        "--output-csv",
        "bond_forecast_with_confidence.csv",
    ]
    bond_task_id = f"bond:{run_id}:{bond_run_dir.name}"
    pid, out_dir = _start_background_cmd(
        cmd,
        output_dir=bond_out,
        log_filename="bond_run.log",
        started_marker_filename="bond_run.started",
        lock_kind="bond",
        lock_run_id=bond_task_id,
    )
    return {"message": "绿债预测已启动", "run_id": run_id, "pid": pid, "bond_output_dir": out_dir}


@app.get("/api/oil/runs/{run_id}/bond/latest", summary="查看最近一次绿债预测结果")
def get_latest_bond_result(run_id: str, rows: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    candidates: list[Path] = []
    default_out = APP_DIR / "bond_integrated_output"
    if default_out.is_dir():
        candidates.append(default_out)
    run_out = run_dir / "bond_integrated_output"
    if run_out.is_dir():
        candidates.append(run_out)
    user_root = run_dir / "bond_user_runs"
    if user_root.is_dir():
        for p in user_root.iterdir():
            out = p / "bond_integrated_output"
            if out.is_dir():
                candidates.append(out)
    if not candidates:
        raise HTTPException(status_code=404, detail="未找到绿债输出目录")
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    chosen = None
    for p in candidates:
        if (p / "bond_forecast_with_confidence.csv").is_file():
            chosen = p
            break
    if chosen is None:
        raise HTTPException(status_code=404, detail="未找到 bond_forecast_with_confidence.csv")
    csv_path = chosen / "bond_forecast_with_confidence.csv"
    preview = _read_csv_preview(csv_path, rows=rows)
    imgs = [x.name for x in chosen.glob("*.png")]
    return {"run_id": run_id, "bond_output_dir": str(chosen.resolve()), "csv_preview": preview, "images": imgs}


@app.get("/api/oil/runs/{run_id}/analytics", summary="结果页统计指标聚合")
def get_run_analytics(run_id: str) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")

    out: dict[str, Any] = {"run_id": run_id}

    driver_csv = run_dir / "driver_factor_analysis.csv"
    if driver_csv.is_file():
        try:
            df_driver = pd.read_csv(driver_csv)
            cols = [c for c in ["feature", "spearman_corr_with_return", "rf_importance", "spearman_pvalue"] if c in df_driver.columns]
            out["driver_top20"] = df_driver[cols].head(20).to_dict(orient="records")
        except Exception:
            out["driver_top20"] = []

    risk_csv = run_dir / "risk_signal_classification.csv"
    if risk_csv.is_file():
        try:
            df_risk = pd.read_csv(risk_csv)
            risk_part: dict[str, Any] = {"sample": df_risk.head(50).to_dict(orient="records")}
            if "RiskLevel" in df_risk.columns:
                risk_part["risk_level_counts"] = df_risk["RiskLevel"].value_counts(dropna=False).to_dict()
            if "Signal" in df_risk.columns:
                risk_part["signal_counts"] = df_risk["Signal"].value_counts(dropna=False).to_dict()
            if "TrueDirection" in df_risk.columns and "PredDirection" in df_risk.columns:
                risk_part["direction_accuracy"] = float((df_risk["TrueDirection"] == df_risk["PredDirection"]).mean())
            out["risk"] = risk_part
        except Exception:
            out["risk"] = {}

    bt_metrics_csv = run_dir / "backtest_metrics.csv"
    if bt_metrics_csv.is_file():
        try:
            df_m = pd.read_csv(bt_metrics_csv)
            out["backtest_metrics"] = df_m.iloc[0].to_dict() if not df_m.empty else {}
        except Exception:
            out["backtest_metrics"] = {}
    bt_csv = run_dir / "backtest_results.csv"
    if bt_csv.is_file():
        try:
            df_bt = pd.read_csv(bt_csv)
            out["backtest_tail50"] = df_bt.tail(50).to_dict(orient="records")
        except Exception:
            out["backtest_tail50"] = []

    future_csv = run_dir / "future_forecast.csv"
    if future_csv.is_file():
        try:
            df_future = pd.read_csv(future_csv)
            out["future_forecast"] = df_future.to_dict(orient="records")
            if not df_future.empty:
                out["next_day_forecast"] = df_future.iloc[0].to_dict()
        except Exception:
            out["future_forecast"] = []

    report_md = run_dir / "bank_team_report.md"
    report_ai_md = run_dir / "bank_team_report_ai.md"
    if report_ai_md.is_file():
        out["bank_report_ai"] = report_ai_md.read_text(encoding="utf-8", errors="replace")
    elif report_md.is_file():
        out["bank_report_draft"] = report_md.read_text(encoding="utf-8", errors="replace")

    return out


@app.post("/api/oil/runs/{run_id}/ai-report", summary="生成企业银行团队 AI 报告")
def build_ai_report(run_id: str, force: bool = Query(False)) -> dict[str, Any]:
    run_dir = WEB_RUNS_DIR / run_id
    if not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    try:
        body = _generate_enterprise_bank_ai_report(run_dir.resolve(), force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 报告生成失败: {exc}") from exc
    if not body:
        raise HTTPException(status_code=404, detail="未生成 AI 报告，请确认 bank_team_report.md 是否存在")
    return {"run_id": run_id, "content": body}


@app.post("/api/ai/chat", summary="AI 专家问答")
def ai_chat(
    mode: str = Query("oil", description="oil 或 new_energy"),
    prompt: str = Query(..., description="用户问题"),
    run_id: str | None = Query(None, description="可选：油价 run_id，用于注入上下文"),
) -> dict[str, Any]:
    mode = (mode or "").strip().lower()
    if mode not in {"oil", "new_energy"}:
        raise HTTPException(status_code=400, detail="mode 仅支持 oil / new_energy")
    context = ""
    if mode == "oil" and run_id:
        run_dir = WEB_RUNS_DIR / run_id
        pred_csv = run_dir / "prediction_results.csv"
        if pred_csv.is_file():
            df = pd.read_csv(pred_csv)
            if not df.empty and "GRU_Pred_Return" in df.columns:
                context = f"最近样本数={len(df)}, 预测收益均值={float(df['GRU_Pred_Return'].mean()):.6f}"
    if mode == "new_energy":
        ne_root = APP_DIR / "new_energy_integrated_outputs"
        if ne_root.is_dir():
            cands = list(ne_root.glob("new_energy_forecast_*_conf*.csv"))
            if cands:
                df = pd.read_csv(cands[0])
                if not df.empty and "NewEnergy_Sigma" in df.columns:
                    context = f"新能源Sigma均值={float(df['NewEnergy_Sigma'].mean()):.6f}"

    sys_prompt = (
        "你是油价预测与风险分析专家。先给结论，再给依据与可执行建议。"
        if mode == "oil"
        else "你是新能源风险分析专家。先给结论，再解释Sigma与风险等级。"
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": sys_prompt}]
    if context:
        messages.append({"role": "user", "content": f"可用数据摘要：{context}"})
    messages.append({"role": "user", "content": prompt})
    try:
        answer = _call_chat_completion(messages)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {exc}") from exc
    return {"mode": mode, "answer": answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend_api:app", host="0.0.0.0", port=8000, reload=True)
