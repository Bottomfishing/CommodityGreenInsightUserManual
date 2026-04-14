"""
大宗绿测 · 油价预测平台 v2.0
重设计版：专业金融风格，清晰的侧边栏与主区域布局
"""
import base64
import html
import io
import json
import os
import sys
import time
import threading
import traceback
import zipfile
import shutil
import subprocess
import errno
import re
import signal
from datetime import datetime
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

from ai_expert_panel import (
    generate_enterprise_bank_ai_report,
    render_ai_expert_panel,
    render_ai_newbie_guide_panel,
)


APP_TITLE = "大宗绿测"
SCRIPT_NAME = "oil_price_prediction_main_0309.py"
NE_SCRIPT_NAME = "run_new_energy_forecast_integrated_0325.py"
BOND_SCRIPT_NAME = "predict_bond_from_gru.py"
USER_MANUAL_PDF_NAME = "【中文】用户手册.pdf"
_DEFAULT_BOND_DATA_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "bond_date", "data.csv"))
_DEFAULT_BOND_ZIP = os.path.abspath(os.path.join(os.path.dirname(__file__), "bond_data.zip"))
_DEFAULT_BOND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "bond_data"))

# 单机部署：全站互斥后台任务（不依赖 MySQL）。多副本/多台机需共享存储或数据库锁。
_APP_DIR_ABS = os.path.dirname(os.path.abspath(__file__))
_GLOBAL_JOB_LOCK_PATH = os.path.join(_APP_DIR_ABS, ".app_global_job.lock")
_GLOBAL_JOB_MUTEX = threading.Lock()

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

# 侧栏「用户手册」通过 iframe 内 JS 创建 Blob URL，在访问者本机浏览器新标签页打开；过大则仅提示。
_USER_MANUAL_BROWSER_OPEN_MAX_BYTES = 5 * 1024 * 1024


def _sidebar_pdf_open_new_tab_in_visitor_browser(pdf_path: Path) -> None:
    """在访客浏览器新标签页打开 PDF（不经过服务器本机默认程序）。"""
    try:
        sz = pdf_path.stat().st_size
    except OSError as e:
        st.sidebar.warning(f"无法读取手册：{e}")
        return
    if sz > _USER_MANUAL_BROWSER_OPEN_MAX_BYTES:
        st.sidebar.warning(
            f"手册约 {max(1, sz // (1024 * 1024))} MB，超过浏览器内打开上限（5MB）。"
            " 请将手册放到可访问的网址并设置环境变量 `USER_MANUAL_URL`。"
        )
        return
    try:
        raw = pdf_path.read_bytes()
    except OSError as e:
        st.sidebar.warning(f"无法读取手册：{e}")
        return
    b64_json = json.dumps(base64.standard_b64encode(raw).decode("ascii"))
    # components.html 默认画在主区，必须包在 st.sidebar 上下文中才会进左栏
    with st.sidebar:
        components.html(
            f"""<!DOCTYPE html><html><body style="margin:0;font-family:sans-serif;">
<button type="button" id="open-manual-pdf" style="width:100%;padding:0.5rem 0.75rem;border-radius:0.5rem;
background:linear-gradient(180deg,#fafafa,#f0f0f0);border:1px solid #d0d5dd;cursor:pointer;font-size:14px;">
用户手册
</button>
<script>
const b64 = {b64_json};
document.getElementById("open-manual-pdf").addEventListener("click", function () {{
  try {{
    const bin = atob(b64);
    const len = bin.length;
    const arr = new Uint8Array(len);
    for (let i = 0; i < len; i++) arr[i] = bin.charCodeAt(i);
    const blob = new Blob([arr], {{ type: "application/pdf" }});
    const url = URL.createObjectURL(blob);
    const w = window.open(url, "_blank");
    if (!w) alert("请允许本站弹出窗口。");
  }} catch (e) {{
    alert("打开失败：" + e);
  }}
}});
</script>
</body></html>""",
            height=58,
            scrolling=False,
        )


def _markdown_to_html_fragment(md: str) -> str:
    """将 Markdown 转为 HTML，供与 forecast-card 同壳的局部展示（避免多段 st 组件无法包进同一 div）。"""
    if not md:
        return ""
    try:
        import markdown as md_pkg

        try:
            return md_pkg.markdown(
                md,
                extensions=["extra", "sane_lists", "tables", "nl2br"],
            )
        except Exception:
            return md_pkg.markdown(md)
    except Exception:
        return "<pre>" + html.escape(md) + "</pre>"


def _render_bank_report_forecast_card(*, label: str, body_markdown: str) -> None:
    """与「实盘预测」大卡相同的渐变顶条与圆角容器，用于企业银行报告正文。"""
    inner = _markdown_to_html_fragment(body_markdown)
    st.markdown(
        f'<div class="forecast-card forecast-card--report">'
        f'<div class="forecast-lbl">{html.escape(label)}</div>'
        f'<div class="fc-prose">{inner}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _strip_ansi(s: str) -> str:
    if not s:
        return s
    return _ANSI_ESCAPE_RE.sub("", s)


def _extract_zip_to_dir(zip_bytes: bytes, target_dir: str) -> None:
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
            orig_name = info.filename
            fixed_name = _fix_name(orig_name)
            fixed_name = fixed_name.replace("\\", "/")
            dest_path = os.path.join(target_dir, fixed_name)
            if orig_name.endswith("/") or fixed_name.endswith("/"):
                os.makedirs(dest_path, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(info) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)


def _find_data_root(extracted_dir: str) -> str:
    raw_a = os.path.join(extracted_dir, "raw_data")
    energy_a = os.path.join(extracted_dir, "能源基本面与下游产业")
    if os.path.isdir(raw_a) and os.path.isdir(energy_a):
        return extracted_dir
    children = [os.path.join(extracted_dir, n) for n in os.listdir(extracted_dir)]
    children = [p for p in children if os.path.isdir(p)]
    if len(children) == 1:
        raw_b = os.path.join(children[0], "raw_data")
        energy_b = os.path.join(children[0], "能源基本面与下游产业")
        if os.path.isdir(raw_b) and os.path.isdir(energy_b):
            return children[0]
    best = None
    for root, dirs, _files in os.walk(extracted_dir):
        if "raw_data" in dirs and "能源基本面与下游产业" in dirs:
            best = root
            break
    return best or extracted_dir


def _summarize_dir(path: str, max_items: int = 120) -> str:
    lines: list[str] = []
    count = 0
    for root, dirs, files in os.walk(path):
        rel_root = os.path.relpath(root, path)
        rel_root = "." if rel_root == "." else rel_root
        lines.append(f"{rel_root}/")
        for d in sorted(dirs):
            lines.append(f"  [D] {d}/")
            count += 1
            if count >= max_items:
                return "\n".join(lines + ["...（已截断）"])
        for f in sorted(files):
            lines.append(f"  [F] {f}")
            count += 1
            if count >= max_items:
                return "\n".join(lines + ["...（已截断）"])
    return "\n".join(lines)


def _tail_text_file(path: str, max_lines: int = 400) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return "\n".join(_strip_ansi(x) for x in lines[-max_lines:])
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def _file_status(path: str) -> str:
    try:
        if not os.path.isfile(path):
            return "不存在"
        mtime = os.path.getmtime(path)
        size = os.path.getsize(path)
        return f"存在（{size} bytes，更新：{datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')}）"
    except Exception:
        return "状态未知"


def _file_recently_updated(path: str, seconds: int = 30) -> bool:
    try:
        if not os.path.isfile(path):
            return False
        return (time.time() - os.path.getmtime(path)) <= seconds
    except Exception:
        return False


def _run_dir_is_recently_started(run_dir: str, seconds: int = 120) -> bool:
    try:
        marker = os.path.join(run_dir, "run.started")
        if not os.path.isfile(marker):
            return False
        return (time.time() - os.path.getmtime(marker)) <= seconds
    except Exception:
        return False


def _parse_keras_loss_from_run_log(run_log_path: str) -> pd.DataFrame | None:
    try:
        if not os.path.isfile(run_log_path):
            return None
        with open(run_log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except Exception:
        return None
    epoch_re = re.compile(r"^Epoch\s+(\d+)\s*/\s*(\d+)\s*$")
    loss_re = re.compile(r"(?:^|\s)loss:\s*([0-9]*\.?[0-9]+)(?:\s|$)")
    val_loss_re = re.compile(r"(?:^|\s)val_loss:\s*([0-9]*\.?[0-9]+)(?:\s|$)")
    rows: list[dict] = []
    current_epoch: int | None = None
    for line in lines:
        s = _strip_ansi(line).strip()
        m_epoch = epoch_re.match(s)
        if m_epoch:
            current_epoch = int(m_epoch.group(1))
            continue
        if current_epoch is None:
            continue
        if "loss" not in s:
            continue
        m_loss = loss_re.search(s)
        if not m_loss:
            continue
        try:
            loss_val = float(m_loss.group(1))
        except Exception:
            continue
        v = None
        m_vloss = val_loss_re.search(s)
        if m_vloss:
            try:
                v = float(m_vloss.group(1))
            except Exception:
                v = None
        rows.append({"epoch": current_epoch, "loss": loss_val, "val_loss": v})
        current_epoch = None
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["epoch"], keep="last").sort_values("epoch")
    return df


def _validate_data_root(data_root: str) -> tuple[bool, str]:
    raw_dir = os.path.join(data_root, "raw_data")
    energy_dir = os.path.join(data_root, "能源基本面与下游产业")
    if not os.path.isdir(raw_dir) or not os.path.isdir(energy_dir):
        return False, "未在 zip 中找到同时存在的 `raw_data/` 和 `能源基本面与下游产业/` 目录。"
    required = os.path.join(raw_dir, "WTI_futuresprice.csv")
    if not os.path.isfile(required):
        return False, "缺少必需文件：`raw_data/WTI_futuresprice.csv`（请检查文件名是否一致、是否被放进了别的子目录）。"
    return True, "OK"


def _pid_alive(pid: int) -> bool:
    """判断本机是否存在该 PID 的进程（用于清理陈旧锁）。"""
    try:
        p = int(pid)
    except Exception:
        return False
    if p <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32.SetLastError(0)
            h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, wintypes.DWORD(p))
            if h:
                kernel32.CloseHandle(h)
                return True
            err = kernel32.GetLastError()
            if err == 5:
                return True
            if err == 87:
                return False
            return True
        except Exception:
            pass
        try:
            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {p}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            out = (r.stdout or "").strip()
            if not out:
                return False
            first = out.splitlines()[0].strip() if out.splitlines() else ""
            if first.upper().startswith("INFO:"):
                return False
            if "无法访问" in out or "Access is denied" in out:
                return True
            return str(p) in out
        except Exception:
            return True
    try:
        os.kill(p, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as e:
        return e.errno != errno.ESRCH


def _read_global_job_lock() -> dict | None:
    try:
        if not os.path.isfile(_GLOBAL_JOB_LOCK_PATH):
            return None
        with open(_GLOBAL_JOB_LOCK_PATH, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _clear_global_job_lock_if_pid(pid: int | None) -> None:
    try:
        exp = int(pid) if pid is not None else 0
    except Exception:
        exp = 0
    if exp <= 0:
        return
    data = _read_global_job_lock()
    if not data:
        return
    try:
        lock_pid = int(data.get("pid", -1))
    except Exception:
        lock_pid = -1
    if lock_pid != exp:
        return
    try:
        os.remove(_GLOBAL_JOB_LOCK_PATH)
    except OSError:
        pass


def _global_job_busy_message() -> str | None:
    """若锁存在且 PID 仍存活则返回说明；否则返回 None（并清理死锁）。"""
    data = _read_global_job_lock()
    if not data:
        return None
    try:
        pid = int(data.get("pid", 0))
    except Exception:
        pid = 0
    kind = str(data.get("kind", "") or "").strip()
    out_dir = str(data.get("output_dir", "") or "").strip()
    started = str(data.get("started_at", "") or "").strip()
    if pid <= 0:
        try:
            os.remove(_GLOBAL_JOB_LOCK_PATH)
        except OSError:
            pass
        return None
    if not _pid_alive(pid):
        try:
            os.remove(_GLOBAL_JOB_LOCK_PATH)
        except OSError:
            pass
        return None
    parts = [f"后台任务占用中（{kind or 'job'}），请等待结束后再试。"]
    if out_dir:
        parts.append(f"输出目录：`{out_dir}`")
    if started:
        parts.append(f"开始时间：{started}")
    parts.append(f"PID：{pid}")
    return " ".join(parts)


def _write_global_job_lock(pid: int, kind: str, output_dir: str) -> None:
    payload = {
        "pid": int(pid),
        "kind": str(kind),
        "output_dir": os.path.abspath(output_dir),
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        fd = os.open(_GLOBAL_JOB_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError(_global_job_busy_message() or "后台任务占用中，请稍后再试。")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False))
        f.flush()
        os.fsync(f.fileno())


def _local_session_owns_lock_pid(pid: int) -> bool:
    for key in ("run_proc", "bond_proc", "new_energy_proc"):
        proc = st.session_state.get(key)
        if not _is_proc_alive(proc):
            continue
        try:
            if int(getattr(proc, "pid", 0) or 0) == int(pid):
                return True
        except Exception:
            pass
    return False


def _other_session_holds_global_job() -> bool:
    """其它浏览器/会话占用全局锁（本 session 无对应 Popen 对象）。"""
    data = _read_global_job_lock()
    if not data:
        return False
    try:
        pid = int(data.get("pid", 0))
    except Exception:
        return False
    if pid <= 0 or not _pid_alive(pid):
        return False
    return not _local_session_owns_lock_pid(pid)


def _task_status_presentation() -> dict[str, str]:
    """侧栏与 Hero 共用：他人占用 / 运行中 / 空闲。"""
    other = _other_session_holds_global_job()
    busy = _global_job_busy_message() is not None
    if other:
        return {
            "sidebar_text": "他人占用",
            "sidebar_dot": "active",
            "sidebar_val_cls": "amber",
            "hero_kpi": "● 他人占用",
            "hero_kpi_cls": "amber",
        }
    if busy:
        return {
            "sidebar_text": "运行中",
            "sidebar_dot": "active",
            "sidebar_val_cls": "green",
            "hero_kpi": "● 运行中",
            "hero_kpi_cls": "green",
        }
    return {
        "sidebar_text": "空闲",
        "sidebar_dot": "idle",
        "sidebar_val_cls": "amber",
        "hero_kpi": "○ 空闲",
        "hero_kpi_cls": "amber",
    }


def _hero_global_job_dir() -> str:
    if _is_proc_alive(st.session_state.get("run_proc")):
        return str(st.session_state.get("run_output_dir", "") or "")
    data = _read_global_job_lock()
    if data and _pid_alive(int(data.get("pid", 0) or 0)):
        return str(data.get("output_dir", "") or "")
    return ""


def _hero_global_job_started_at() -> str:
    if _is_proc_alive(st.session_state.get("run_proc")):
        return str(st.session_state.get("run_started_at", "") or "—") or "—"
    data = _read_global_job_lock()
    if data and _pid_alive(int(data.get("pid", 0) or 0)):
        return str(data.get("started_at", "") or "—") or "—"
    return "—"


def _terminate_pid_tree(pid: int | None) -> None:
    try:
        p = int(pid) if pid is not None else 0
    except Exception:
        p = 0
    if p <= 0:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(p), "/T", "/F"], capture_output=True, text=True)
    else:
        try:
            os.kill(p, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception:
            pass


def _start_background_run(base_path: str, top_n: int, output_dir: str,
                          cutoff_date: str | None = None, forecast_steps: int = 0, epochs: int = 200,
                          enable_early_stopping: bool = True) -> None:
    existing = st.session_state.get("run_proc")
    if _is_proc_alive(existing):
        return
    cmd = [
        sys.executable, "-u", SCRIPT_NAME,
        "--base-path", base_path,
        "--top-n", str(int(top_n)),
        "--epochs", str(int(epochs)),
        "--output-dir", output_dir,
        "--no-plots",
    ]
    if not enable_early_stopping:
        cmd += ["--disable-early-stopping"]
    if cutoff_date:
        cmd += ["--cutoff-date", str(cutoff_date)]
    try:
        forecast_steps = int(forecast_steps or 0)
    except Exception:
        forecast_steps = 0
    if forecast_steps > 0:
        cmd += ["--forecast-steps", str(int(forecast_steps))]
    proc: subprocess.Popen | None = None
    with _GLOBAL_JOB_MUTEX:
        busy = _global_job_busy_message()
        if busy:
            raise RuntimeError(busy)
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
        try:
            _write_global_job_lock(int(proc.pid), "oil", output_dir)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
            raise
    assert proc is not None
    st.session_state["run_proc"] = proc
    st.session_state["run_output_dir"] = os.path.abspath(output_dir)
    st.session_state["run_started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["run_returncode"] = None
    log_path = os.path.join(output_dir, "run.log")
    started_marker = os.path.join(output_dir, "run.started")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        with open(started_marker, "w", encoding="utf-8") as f:
            f.write(f"started_at={st.session_state['run_started_at']}\n")
            f.write(f"base_path={base_path}\n")
            f.write(f"top_n={int(top_n)}\n")
            f.write(f"epochs={int(max(1, int(epochs or 200)))}\n")
            f.write(f"early_stopping={bool(enable_early_stopping)}\n")
            f.write(f"pid={getattr(proc, 'pid', '')}\n")
    except Exception:
        pass
    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"[web] started_at={st.session_state['run_started_at']} pid={getattr(proc, 'pid', '')}\n")
            f.flush()
    except Exception:
        pass

    def _pump():
        child_pid = getattr(proc, "pid", None)
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                if proc.stdout is not None:
                    for line in proc.stdout:
                        f.write(_strip_ansi(line))
                        f.flush()
        finally:
            try:
                proc.wait()
            except Exception:
                pass
            _clear_global_job_lock_if_pid(child_pid)

    t = threading.Thread(target=_pump, daemon=True)
    st.session_state["run_thread"] = t
    t.start()


def _start_background_cmd(cmd: list[str], output_dir: str, log_filename: str,
                          started_marker_filename: str, session_state_prefix: str) -> None:
    proc_key = f"{session_state_prefix}_proc"
    if _is_proc_alive(st.session_state.get(proc_key)):
        return
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    proc: subprocess.Popen | None = None
    with _GLOBAL_JOB_MUTEX:
        busy = _global_job_busy_message()
        if busy:
            raise RuntimeError(busy)
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
        try:
            _write_global_job_lock(int(proc.pid), session_state_prefix, abs_output_dir)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
            raise
    assert proc is not None
    st.session_state[proc_key] = proc
    st.session_state[f"{session_state_prefix}_output_dir"] = abs_output_dir
    st.session_state[f"{session_state_prefix}_started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state[f"{session_state_prefix}_returncode"] = None
    log_path = os.path.join(abs_output_dir, log_filename)
    started_marker = os.path.join(abs_output_dir, started_marker_filename)
    try:
        with open(started_marker, "w", encoding="utf-8") as f:
            f.write(f"started_at={st.session_state[f'{session_state_prefix}_started_at']}\n")
            f.write(f"pid={getattr(proc, 'pid', '')}\n")
    except Exception:
        pass
    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"[web:{session_state_prefix}] started_at={st.session_state[f'{session_state_prefix}_started_at']} pid={getattr(proc, 'pid', '')}\n")
            f.flush()
    except Exception:
        pass

    def _pump() -> None:
        child_pid = getattr(proc, "pid", None)
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                if proc.stdout is not None:
                    for line in proc.stdout:
                        f.write(_strip_ansi(line))
                        f.flush()
        finally:
            try:
                proc.wait()
            except Exception:
                pass
            _clear_global_job_lock_if_pid(child_pid)

    t = threading.Thread(target=_pump, daemon=True)
    st.session_state[f"{session_state_prefix}_thread"] = t
    t.start()


def _bond_feature_table_ready() -> bool:
    return os.path.isfile(_DEFAULT_BOND_DATA_CSV)


def _maybe_start_auto_bond() -> None:
    if not st.session_state.get("auto_bond_after_oil"):
        return
    run_dir = st.session_state.get("run_output_dir")
    if not run_dir or not isinstance(run_dir, str) or not os.path.isdir(run_dir):
        return
    oil_proc = st.session_state.get("run_proc")
    if _is_proc_alive(oil_proc):
        return
    rc = _get_proc_returncode(oil_proc)
    if rc is not None and rc != 0:
        return
    oil_pred = os.path.join(run_dir, "oil_pred.csv")
    if not os.path.isfile(oil_pred):
        return
    if not (_bond_feature_table_ready() or os.path.isfile(_DEFAULT_BOND_ZIP) or os.path.isdir(_DEFAULT_BOND_DIR)):
        return
    flag = os.path.join(run_dir, "bond_auto_started.flag")
    if os.path.isfile(flag):
        return
    if _is_proc_alive(st.session_state.get("bond_proc")):
        return
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), BOND_SCRIPT_NAME))
    if not os.path.isfile(script_path):
        return
    bond_out = os.path.abspath(os.path.join(run_dir, "bond_integrated_output"))
    cmd = [
        sys.executable, "-u", script_path,
        "--data-csv", _DEFAULT_BOND_DATA_CSV,
        "--oil-pred-csv", os.path.abspath(oil_pred),
        "--out-dir", bond_out,
        "--output-csv", "bond_forecast_with_confidence.csv",
    ]
    try:
        _start_background_cmd(cmd=cmd, output_dir=bond_out, log_filename="bond_run.log",
                              started_marker_filename="bond_run.started", session_state_prefix="bond")
    except RuntimeError:
        return
    try:
        with open(flag, "w", encoding="utf-8") as f:
            f.write(f"started_at={datetime.now().isoformat()}\n")
    except Exception:
        pass


def _is_proc_alive(proc: subprocess.Popen | None) -> bool:
    return proc is not None and proc.poll() is None


def _get_proc_returncode(proc: subprocess.Popen | None) -> int | None:
    if proc is None:
        return None
    try:
        return proc.poll()
    except Exception:
        return None


@st.cache_data(ttl=1.0)
def _read_csv_safe(path: str, parse_dates: list[str] | None = None) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _list_run_dirs(root: str = "web_runs") -> list[str]:
    if not os.path.isdir(root):
        return []
    dirs = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isdir(p) and name.startswith("run_"):
            dirs.append(p)
    return sorted(dirs, reverse=True)


def _pick_most_recent_active_run_dir(run_dirs: list[str]) -> str | None:
    best = None
    best_mtime = -1.0
    for d in run_dirs:
        p_started = os.path.join(d, "run.started")
        p_log = os.path.join(d, "run.log")
        try:
            p = p_started if os.path.isfile(p_started) else (p_log if os.path.isfile(p_log) else None)
            if p is None:
                continue
            m = os.path.getmtime(p)
            if m > best_mtime:
                best_mtime = m
                best = os.path.abspath(d)
        except Exception:
            continue
    return best


def _render_training_dashboard(run_dir: str, auto_refresh: bool, refresh_seconds: int) -> None:
    st.markdown("下面的图表来自本次输出目录中的 `training_log.csv` 与 `prediction_results.csv`。")
    log_csv_path = os.path.join(run_dir, "training_log.csv")
    run_log_path = os.path.join(run_dir, "run.log")
    df_log = _read_csv_safe(log_csv_path)
    df_pred = _read_csv_safe(os.path.join(run_dir, "prediction_results.csv"), parse_dates=["Date_base", "Date_target"])

    st.subheader("训练过程：Train / Val Loss")
    if df_log is None or df_log.empty:
        df_from_log = _parse_keras_loss_from_run_log(run_log_path)
        if df_from_log is None or df_from_log.empty:
            st.info("还没有找到可用的训练曲线数据：`training_log.csv` 为空，且 `run.log` 尚未解析到 loss。")
        else:
            st.caption("当前使用 `run.log` 解析的 loss/val_loss（用于训练中实时监控）。")
            chart = df_from_log[["epoch", "loss"]].rename(columns={"loss": "train_loss"}).set_index("epoch")
            if "val_loss" in df_from_log.columns and df_from_log["val_loss"].notna().any():
                chart["val_loss"] = df_from_log["val_loss"]
            st.line_chart(chart)
    else:
        if "epoch" not in df_log.columns:
            df_log.insert(0, "epoch", range(len(df_log)))
        chart = df_log[["epoch", "loss"]].rename(columns={"loss": "train_loss"}).set_index("epoch")
        if "val_loss" in df_log.columns:
            chart["val_loss"] = df_log["val_loss"]
        st.line_chart(chart)

    st.subheader("最终预测效果：价格对比")
    if df_pred is None or df_pred.empty:
        st.info("还没有找到 `prediction_results.csv`（训练未结束或未写出）。")
    else:
        st.markdown("**价格对比：Actual vs Pred（按 Date_target）**")
        df_price = df_pred[["Date_target", "Actual_P_t_plus_H", "GRU_Pred_P_t_plus_H"]].copy()
        df_price = df_price.set_index("Date_target")
        df_price.columns = ["Actual_Price", "GRU_Pred_Price"]
        st.line_chart(df_price)

    st.subheader("最终预测效果：收益对比")
    if df_pred is None or df_pred.empty:
        st.info("还没有找到 `prediction_results.csv`（训练未结束或未写出）。")
    else:
        if "Actual_Return" in df_pred.columns and "GRU_Pred_Return" in df_pred.columns:
            st.markdown("**收益对比：Actual_Return vs GRU_Pred_Return**")
            df_ret = df_pred[["Date_target", "Actual_Return", "GRU_Pred_Return"]].copy()
            df_ret = df_ret.set_index("Date_target")
            df_ret.columns = ["Actual_Return", "GRU_Pred_Return"]
            st.line_chart(df_ret)
        else:
            st.info("`prediction_results.csv` 中未找到收益列（Actual_Return / GRU_Pred_Return）。")

    if auto_refresh:
        st.caption(f"自动刷新已开启：每 {refresh_seconds} 秒刷新一次（用于训练进行中时查看曲线）。")
        time.sleep(refresh_seconds)
        st.rerun()


# ======================================================================
# 样式注入
# ======================================================================
def _inject_styles() -> None:
    st.markdown(r"""
<style>
/* CSS 变量：亮色主题 */
:root {
  --brand: #0080bf;
  --brand-dark: #006a9e;
  --accent: #00a3e0;
  --primary-color: #0080bf;
  --secondary-background-color: #e6f4fb;
  --brand-soft: #e6f4fb;
  --text-main: #1a2332;
  --text-sub: #5a6478;
  --text-muted: #94a3b8;
  --border: #e2e8f0;
  --bg-page: #f0f4f8;
  --bg-card: #ffffff;
  --ok: #16a34a;
  --warn: #d97706;
  --danger: #2563eb;
  --shadow: 0 2px 8px rgba(0,0,0,.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,.10);
  --font: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --mono: "Cascadia Code", "JetBrains Mono", Consolas, "Courier New", monospace;
}

/* 暗色 CSS 变量必须挂在 :is(html[data-theme="dark"],html[data-st-theme="dark"]) 上，不能写 .foo :root（无法匹配） */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) {
  --brand: #38bdf8;
  --brand-dark: #0ea5e9;
  --accent: #7dd3fc;
  --primary-color: #38bdf8;
  --secondary-background-color: rgba(56,189,248,.12);
  --brand-soft: rgba(56,189,248,.12);
  --text-main: #f1f5f9;
  --text-sub: #94a3b8;
  --text-muted: #64748b;
  --border: rgba(255,255,255,.1);
  --bg-page: #000000;
  --bg-card: #1e293b;
  --ok: #34d399;
  --warn: #fbbf24;
  --danger: #60a5fa;
  --shadow: 0 2px 8px rgba(0,0,0,.3);
  --shadow-md: 0 4px 16px rgba(0,0,0,.4);
}

html, body, .stApp { font-family: var(--font); }
.stApp { background: var(--bg-page); }
.block-container { padding: 1.2rem 1.5rem 2rem !important; }

/* 纯黑底：覆盖 Streamlit 多层容器（仅暗色主题） */
:is(html[data-theme="dark"],html[data-st-theme="dark"]),
:is(html[data-theme="dark"],html[data-st-theme="dark"]) body {
  background: #000000 !important;
  color-scheme: dark;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stApp,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stAppViewContainer"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section.main,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) div.main {
  background: #000000 !important;
}
/* 1.56+ 主区块容器常单独设色，需与 stMain 同级覆盖 */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] > div,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stMainBlockContainer.block-container,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] .stMainBlockContainer {
  background-color: #000000 !important;
  background-image: none !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .block-container {
  background: transparent !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] .block-container {
  background-color: #000000 !important;
}

/* ═══════════════════════════════════════════════════════════════
   侧边栏 · 跟随 Streamlit 主题（html[data-theme]）
   亮色 → 白色系  |  暗色 → 深蓝黑系
   ═══════════════════════════════════════════════════════════════ */

/* ── 暗色主题：深蓝黑侧边栏 ── */
/* 外层 section + 内层 stSidebarContent（1.5x 主题色常写在子节点，权重需压过 emotion 主题） */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section[data-testid="stSidebar"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section.stSidebar,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] {
  background: #1a2a3a !important;
  background-color: #1a2a3a !important;
  border-right: 1px solid rgba(255,255,255,.06) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebarContent"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebarUserContent"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebarHeader"] {
  background-color: #1a2a3a !important;
  background-image: none !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-brand { padding: 1.1rem 0.6rem 0.5rem; text-align: center; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-brand-logo { display: flex; align-items: center; gap: 0.6rem; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-logo-icon { width: 64px; height: 64px; background: transparent !important; background-image: none !important; border-radius: 0; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebarContent"] .sidebar-logo-icon {
  background: transparent !important;
  background-image: none !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-logo-icon svg { width: 20px; height: 20px; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-logo-icon img { width: 60px; height: 60px; object-fit: contain; display: block; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-brand-name { font-size: 1rem; font-weight: 700; color: #fff !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-brand-sub { font-size: 0.65rem; color: rgba(255,255,255,.4) !important; margin-top: 1px; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-status { background: rgba(255,255,255,.04) !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 10px; padding: 0.5rem 0.7rem; margin: 0.3rem 0.5rem; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-status-row { display: flex; align-items: center; gap: 0.4rem; margin: 0.25rem 0; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-dot.idle { background: #6b7280; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-dot.active { background: #34d399; box-shadow: 0 0 5px rgba(52,211,153,.5); animation: pulse-green 2s infinite; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-dot.off { background: #374151; }
@keyframes pulse-green { 0%,100%{opacity:1} 50%{opacity:0.5} }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-lbl { font-size: 0.68rem; color: rgba(255,255,255,.4); flex: 1; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-val { font-size: 0.7rem; font-weight: 500; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-val.green { color: #34d399; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .status-val.amber { color: #fbbf24; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .sidebar-section-label { font-size: 0.68rem; font-weight: 600; color: rgba(255,255,255,.3); letter-spacing: 0.08em; text-transform: uppercase; margin: 0.7rem 0.5rem 0.25rem; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] { margin: 0.25rem 0.5rem !important; border: 1px solid rgba(255,255,255,.12) !important; border-radius: 10px !important; background: rgba(255,255,255,.04) !important; overflow: hidden; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] summary { color: rgba(255,255,255,.85) !important; font-size: 0.78rem !important; font-weight: 500 !important; padding: 0.55rem 0.75rem !important; cursor: pointer; list-style: none; display: flex; align-items: center; gap: 0.4rem; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] summary::-webkit-details-marker { display: none; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] > div { background: rgba(6,14,28,.98) !important; padding: 0.5rem 0.75rem 0.7rem !important; border-top: 1px solid rgba(255,255,255,.06) !important; color: rgba(255,255,255,.65) !important; font-size: 0.76rem !important; line-height: 1.7; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] p,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] li { color: rgba(255,255,255,.65) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] code { background: rgba(255,255,255,.1) !important; color: #93c5fd !important; padding: 0.1rem 0.35rem; border-radius: 4px; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] pre { background: rgba(0,0,0,.35) !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 6px !important; padding: 0.5rem !important; color: rgba(255,255,255,.75) !important; overflow-x: auto; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] table { color: rgba(255,255,255,.65) !important; width: 100%; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] th { background: rgba(255,255,255,.07) !important; color: #f0f6fa !important; font-weight: 600; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] details[data-testid="stExpander"] td { border-color: rgba(255,255,255,.06) !important; padding: 0.3rem 0.5rem !important; font-size: 0.74rem !important; }

/* ── 亮色主题：白色系侧边栏 ── */
:is(html[data-theme="light"],html[data-st-theme="light"]) section[data-testid="stSidebar"],
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] {
  background: #ffffff !important;
  background-color: #ffffff !important;
  border-right: 1px solid #e2e8f0 !important;
  box-shadow: 2px 0 8px rgba(0,0,0,.06) !important;
}
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebarContent"],
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebarUserContent"],
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebarHeader"] {
  background-color: #ffffff !important;
  background-image: none !important;
}
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-brand { padding: 1.1rem 0.6rem 0.5rem; text-align: center; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-brand-logo { display: flex; align-items: center; gap: 0.6rem; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-logo-icon { width: 64px; height: 64px; background: transparent; border-radius: 0; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-logo-icon svg { width: 20px; height: 20px; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-logo-icon img { width: 60px; height: 60px; object-fit: contain; display: block; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-brand-name { font-size: 1rem; font-weight: 700; color: #0080bf; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-brand-sub { font-size: 0.65rem; color: #94a3b8; margin-top: 1px; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-status { background: #f0f4f8; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.5rem 0.7rem; margin: 0.3rem 0.5rem; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-status-row { display: flex; align-items: center; gap: 0.4rem; margin: 0.25rem 0; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-dot.idle { background: #94a3b8; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-dot.active { background: #16a34a; box-shadow: 0 0 5px rgba(22,163,74,.5); animation: pulse-green-l 2s infinite; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-dot.off { background: #cbd5e1; }
@keyframes pulse-green-l { 0%,100%{opacity:1} 50%{opacity:0.5} }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-lbl { font-size: 0.68rem; color: #94a3b8; flex: 1; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-val { font-size: 0.7rem; font-weight: 500; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-val.green { color: #16a34a; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .status-val.amber { color: #d97706; }
:is(html[data-theme="light"],html[data-st-theme="light"]) .sidebar-section-label { font-size: 0.68rem; font-weight: 600; color: #94a3b8; letter-spacing: 0.08em; text-transform: uppercase; margin: 0.7rem 0.5rem 0.25rem; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] { margin: 0.25rem 0.5rem !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; background: #f8fafc !important; overflow: hidden; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] summary { color: #334155 !important; font-size: 0.78rem !important; font-weight: 500 !important; padding: 0.55rem 0.75rem !important; cursor: pointer; list-style: none; display: flex; align-items: center; gap: 0.4rem; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] summary::-webkit-details-marker { display: none; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] > div { background: #ffffff !important; padding: 0.5rem 0.75rem 0.7rem !important; border-top: 1px solid #e2e8f0 !important; color: #475569 !important; font-size: 0.76rem !important; line-height: 1.7; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] p,
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] li { color: #475569 !important; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] code { background: #e0f2fe !important; color: #0369a1 !important; padding: 0.1rem 0.35rem; border-radius: 4px; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] pre { background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; border-radius: 6px !important; padding: 0.5rem !important; color: #334155 !important; overflow-x: auto; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] table { color: #475569 !important; width: 100%; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] th { background: #f1f5f9 !important; color: #1e293b !important; font-weight: 600; }
:is(html[data-theme="light"],html[data-st-theme="light"]) [data-testid="stSidebar"] details[data-testid="stExpander"] td { border-color: #e2e8f0 !important; padding: 0.3rem 0.5rem !important; font-size: 0.74rem !important; }

/* ── 亮色主题：主区域通用样式 ── */
.hero { background: linear-gradient(135deg, #f8fbff 0%, #f1f5f9 58%, #e9eef5 100%); border-radius: 14px; padding: 2.1rem 2.2rem; margin-bottom: 0.9rem; color: var(--text-main); border: 1px solid #e2e8f0; position: relative; overflow: hidden; }
.hero::before { content: ""; position: absolute; right: -80px; top: -50px; width: 380px; height: 220px; border-radius: 50%; background: radial-gradient(circle at center, rgba(148,163,184,.18) 0%, rgba(148,163,184,.05) 48%, rgba(148,163,184,0) 72%); pointer-events: none; }
.hero::after { content: ""; position: absolute; right: 100px; top: 80px; width: 56px; height: 56px; border-radius: 50%; background: rgba(148,163,184,.16); pointer-events: none; }
.hero-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0 0 0.45rem; letter-spacing: .02em; }
.hero-sub { font-size: 0.95rem; color: #64748b; margin: 0 0 1.2rem; }
.hero-actions { display: flex; gap: 0.7rem; align-items: center; }
.hero-btn-primary { display: inline-block; background: linear-gradient(135deg, var(--brand) 0%, var(--accent) 100%); color: #fff !important; font-size: 0.92rem; font-weight: 700; padding: 0.56rem 1.25rem; border-radius: 8px; text-decoration: none; box-shadow: 0 6px 14px rgba(0,128,191,.22); }
.hero-btn-secondary { display: inline-block; background: #ffffff; color: var(--brand) !important; border: 1px solid #93c5fd; font-size: 0.9rem; font-weight: 700; padding: 0.54rem 1.2rem; border-radius: 8px; text-decoration: none; }
.pipeline-wrap { background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 0.85rem 1rem; margin: 0 0 1rem; box-shadow: 0 2px 8px rgba(15,23,42,.04); }
.hero-steps { display: flex; align-items: center; margin: 0; }
.hero-step-item { display: flex; flex-direction: column; align-items: center; flex: 0 0 auto; }
.hero-step-circle { width: 32px; height: 32px; border-radius: 50%; background: #f8fafc; border: 2px solid #cbd5e1; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; color: #64748b; margin-bottom: 0.25rem; }
.hero-step-circle.done { background: var(--ok); border-color: var(--ok); color: #fff; }
.hero-step-circle.active { background: var(--brand); border-color: var(--brand); color: #fff; box-shadow: 0 0 0 3px rgba(0,128,191,.25); }
.hero-step-circle.wait { background: #f8fafc; border-color: #cbd5e1; color: #94a3b8; }
.hero-step-lbl { font-size: 0.65rem; color: #94a3b8; text-align: center; }
.hero-step-lbl.done { color: #475569; }
.hero-step-lbl.active { color: #0f172a; font-weight: 600; }
.hero-connector { flex: 1; height: 2px; background: #dbe4ee; margin: 0 6px; margin-bottom: 1.1rem; }
.hero-connector.done { background: #9dd7f0; }
.kpi-row { display: flex; gap: 0.8rem; margin-bottom: 0.5rem; margin-top: 0.8rem; }
.kpi-card { flex: 1; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15); border-radius: 10px; padding: 0.7rem 1rem; }
.kpi-label { font-size: 0.68rem; color: rgba(255,255,255,.4); margin: 0 0 0.15rem; }
.kpi-value { font-size: 1.2rem; font-weight: 700; color: #fff; line-height: 1; margin: 0; }
.kpi-value.green { color: #34d399; }
.kpi-value.amber { color: #fbbf24; }
.kpi-value.blue { color: #93c5fd; }
.terminal-block { background: #0d1117; border: 1px solid rgba(255,255,255,.08); border-radius: 8px; padding: 0.8rem 1rem; font-family: var(--mono); font-size: 0.72rem; color: #c9d1d9; line-height: 1.6; max-height: 340px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; }
.terminal-block::-webkit-scrollbar { width: 4px; }
.terminal-block::-webkit-scrollbar-track { background: transparent; }
.terminal-block::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 2px; }
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; margin: 0.8rem 0; }
.metric-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 0.9rem 1rem; box-shadow: var(--shadow); transition: transform .15s, border-color .15s; }
.metric-card:hover { transform: translateY(-1px); border-color: var(--brand); box-shadow: var(--shadow-md); }
.metric-label { font-size: 0.7rem; color: var(--text-muted); margin: 0 0 0.3rem; }
.metric-value { font-size: 1.3rem; font-weight: 700; color: var(--text-main); margin: 0; line-height: 1; }
.metric-sub { font-size: 0.68rem; color: var(--text-muted); margin: 0.2rem 0 0; }
.forecast-card { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #ede9fe 100%); border: 1px solid #bae6fd; border-radius: 12px; padding: 1.2rem 1.5rem; margin: 0.6rem 0; position: relative; overflow: hidden; }
.forecast-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, var(--brand), var(--ok), #a78bfa); }
.forecast-lbl { font-size: 0.72rem; color: #0369a1; margin: 0 0 0.3rem; font-weight: 600; }
.forecast-val { font-size: 2rem; font-weight: 800; color: #0c4a6e; line-height: 1; margin: 0 0 0.3rem; }
.forecast-date { font-size: 0.72rem; color: #0891b2; margin: 0; }
.forecast-card--report .fc-prose { color: #1a2332; font-size: 0.9rem; line-height: 1.65; margin: 0; }
.forecast-card--report .fc-prose p { margin: 0.35rem 0; }
.forecast-card--report .fc-prose h1, .forecast-card--report .fc-prose h2, .forecast-card--report .fc-prose h3 { margin: 0.65rem 0 0.35rem; color: #0c4a6e; line-height: 1.35; }
.forecast-card--report .fc-prose ul, .forecast-card--report .fc-prose ol { margin: 0.35rem 0 0.35rem 1.1rem; padding: 0; }
.forecast-card--report .fc-prose pre { background: rgba(255,255,255,.55); border: 1px solid #bae6fd; border-radius: 8px; padding: 0.6rem 0.75rem; overflow-x: auto; font-size: 0.78rem; }
.forecast-card--report .fc-prose code { background: rgba(255,255,255,.5); padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.82em; }
.forecast-card--report .fc-prose table { border-collapse: collapse; width: 100%; font-size: 0.78rem; margin: 0.5rem 0; }
.forecast-card--report .fc-prose th, .forecast-card--report .fc-prose td { border: 1px solid #bae6fd; padding: 0.35rem 0.5rem; text-align: left; }
.forecast-card--report .fc-prose th { background: rgba(255,255,255,.45); }
.empty-state { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px dashed var(--border); border-radius: 12px; padding: 2.5rem 1rem; text-align: center; }
.empty-title { font-size: 1rem; font-weight: 600; color: var(--text-main); margin: 0 0 0.4rem; }
.empty-desc { font-size: 0.8rem; color: var(--text-muted); margin: 0; }
.section-title { font-size: 1rem; font-weight: 700; color: var(--text-main); border-left: 4px solid var(--brand); padding-left: 0.7rem; margin: 1.2rem 0 0.8rem; }

/* ── 统一原生控件主色（复选框/滑块）为品牌蓝，覆盖 Streamlit 默认红色 ── */
.stCheckbox input[type="checkbox"] { accent-color: var(--brand) !important; }
.stCheckbox [data-baseweb="checkbox"] input[type="checkbox"] { accent-color: var(--brand) !important; }
.stCheckbox [data-baseweb="checkbox"] > div {
  border-color: var(--brand) !important;
}
.stCheckbox [data-baseweb="checkbox"] [aria-checked="true"] > div {
  background-color: var(--brand) !important;
  border-color: var(--brand) !important;
}

.stSlider [data-baseweb="slider"] [role="slider"] {
  background: var(--brand) !important;
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 1px var(--brand) !important;
}
.stSlider [data-baseweb="slider"] [role="slider"]:focus,
.stSlider [data-baseweb="slider"] [role="slider"]:hover {
  background: var(--brand-dark) !important;
  border-color: var(--brand-dark) !important;
  box-shadow: 0 0 0 2px rgba(0, 128, 191, .25) !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMin"] {
  background: var(--brand) !important;
}
/* 更高优先级覆盖（处理 Streamlit/BaseWeb 内联或后置样式） */
[data-testid="stAppViewContainer"] .stCheckbox [data-baseweb="checkbox"] [aria-checked="true"] > div,
[data-testid="stAppViewContainer"] .stCheckbox [data-baseweb="checkbox"] [aria-checked="mixed"] > div {
  background-color: var(--brand) !important;
  border-color: var(--brand) !important;
}
[data-testid="stAppViewContainer"] .stCheckbox [data-baseweb="checkbox"] svg {
  fill: #ffffff !important;
}
[data-testid="stAppViewContainer"] .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"],
[data-testid="stAppViewContainer"] .stSlider [data-baseweb="slider"] [role="slider"] {
  background-color: var(--brand) !important;
  border-color: var(--brand) !important;
  color: #ffffff !important;
}
[data-testid="stAppViewContainer"] .stSlider [data-baseweb="slider"] [data-testid="stTickBarMin"],
[data-testid="stAppViewContainer"] .stSlider [data-baseweb="slider"] div[style*="background"] {
  background-color: var(--brand) !important;
}

/* ── 暗色：侧边栏内原生控件（不依赖系统浅色/深色，避免与 Streamlit 菜单主题冲突） ── */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] .stMarkdown,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] p,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] span,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] label {
  color: rgba(255,255,255,.85) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] .stSelectbox > div > div,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] .stSelectbox [data-testid="stSelectbox"] {
  color: #fff !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
  background: transparent !important;
}
/* 侧栏内 primary 按钮默认大块白底，用与主题一致的渐变压住 */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebar"] button[kind="primary"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stSidebarContent"] button[kind="primary"] {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
  color: #ffffff !important;
  border: none !important;
}

/* ── 暗色：主区域组件（原 prefers-color-scheme，现绑定 data-theme=dark） ── */
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .hero { background: linear-gradient(135deg, #f8fbff 0%, #f1f5f9 58%, #e9eef5 100%) !important; border-color: rgba(148,163,184,.35) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .kpi-card { background: rgba(255,255,255,.06) !important; border-color: rgba(255,255,255,.1) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stTabBar"] { background: #1e293b !important; border-bottom-color: rgba(255,255,255,.1) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) button[data-testid="stTab"] { color: #94a3b8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) button[data-testid="stTab"]:hover { color: #38bdf8 !important; background: rgba(56,189,248,.08) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) button[data-testid="stTab"][aria-selected="true"] { color: #38bdf8 !important; background: #1e293b !important; box-shadow: 0 -2px 0 0 #38bdf8 inset !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stTabPanel"] { background: #1e293b !important; border-color: rgba(255,255,255,.1) !important; border-top: none !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stButton > button[kind="primary"], :is(html[data-theme="dark"],html[data-st-theme="dark"]) div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important; color: #fff !important;
  box-shadow: 0 3px 10px rgba(14,165,233,.35) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stButton > button:not([kind="primary"]) {
  border-color: rgba(255,255,255,.15) !important; background: #1e293b !important; color: #f1f5f9 !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stButton > button:not([kind="primary"]):hover { border-color: #38bdf8 !important; color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] details[data-testid="stExpander"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section.main details[data-testid="stExpander"],
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .main details[data-testid="stExpander"] {
  border-color: rgba(255,255,255,.1) !important; background: #1e293b !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] details[data-testid="stExpander"] summary,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section.main details[data-testid="stExpander"] summary,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .main details[data-testid="stExpander"] summary { color: #f1f5f9 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stMain"] details[data-testid="stExpander"] > div,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) section.main details[data-testid="stExpander"] > div,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .main details[data-testid="stExpander"] > div { background: #162032 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stSelectbox > label, :is(html[data-theme="dark"],html[data-st-theme="dark"]) .stNumberInput > label, :is(html[data-theme="dark"],html[data-st-theme="dark"]) .stSlider > label { color: #94a3b8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stCheckbox > label { color: #f1f5f9 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stFileUploader"] > div:first-child {
  border-color: rgba(255,255,255,.15) !important; background: rgba(255,255,255,.03) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stFileUploader"] > div:first-child:hover { border-color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .metric-card { background: #1e293b !important; border-color: rgba(255,255,255,.1) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .metric-card:hover { border-color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .metric-label { color: #64748b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .metric-value { color: #f1f5f9 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card {
  background: linear-gradient(135deg, #0c1929 0%, #1e293b 60%, #1e1b4b 100%) !important;
  border-color: rgba(56,189,248,.2) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-lbl { color: #94a3b8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-val { color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-date { color: #64748b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose { color: #e2e8f0 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose h1,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose h2,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose h3 { color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose pre { background: rgba(0,0,0,.25) !important; border-color: rgba(56,189,248,.2) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose code { background: rgba(0,0,0,.3) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose th,
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose td { border-color: rgba(56,189,248,.2) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .forecast-card--report .fc-prose th { background: rgba(255,255,255,.06) !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .empty-state {
  background: linear-gradient(135deg, #1e293b 0%, #162032 100%) !important;
  border-color: rgba(255,255,255,.08) !important;
}
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .empty-title { color: #f1f5f9 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .empty-desc { color: #64748b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stDataFrame, :is(html[data-theme="dark"],html[data-st-theme="dark"]) [data-testid="stDataFrame"] { background: #1e293b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stAlert { background: #1e293b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .section-title { color: #f1f5f9 !important; border-bottom-color: #38bdf8 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stSubheader { color: #f1f5f9 !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .stCaption { color: #64748b !important; }
:is(html[data-theme="dark"],html[data-st-theme="dark"]) .terminal-block {
  background: #060b14 !important; border-color: rgba(255,255,255,.06) !important; color: #c9d1d9 !important;
}
</style>
""", unsafe_allow_html=True)


def _inject_streamlit_theme_bridge() -> None:
    """Streamlit 1.5x 主题由 Emotion 控制，<html> 上往往没有 data-theme；同步到 data-st-theme 供 CSS 使用。"""
    components.html(
        """
<!DOCTYPE html><html><body><script>
(function () {
  var W = window.parent;
  var doc = W.document;
  function pinStreamlitTheme() {
    var root = doc.documentElement;
    var sb = doc.querySelector('[data-testid="stSidebar"]');
    if (!sb) return;
    var cs = (W.getComputedStyle(sb).colorScheme || "").trim().toLowerCase();
    var dark = false;
    if (cs === "dark" || (cs && cs.split(/\\s+/).indexOf("dark") !== -1)) {
      dark = true;
    } else if (cs === "light" || (cs && cs.split(/\\s+/).indexOf("light") !== -1)) {
      dark = false;
    } else {
      var main = doc.querySelector('[data-testid="stMain"]');
      if (main) {
        var bg = W.getComputedStyle(main).backgroundColor;
        var m = bg.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
        if (m) {
          var lum = (0.2126 * (+m[1]) + 0.7152 * (+m[2]) + 0.0722 * (+m[3])) / 255;
          dark = lum < 0.42;
        }
      }
    }
    root.setAttribute("data-st-theme", dark ? "dark" : "light");
  }
  pinStreamlitTheme();
  if (!W.__streamlitThemeBridge) {
    W.__streamlitThemeBridge = true;
    setInterval(pinStreamlitTheme, 500);
    W.document.addEventListener("visibilitychange", function () {
      if (!W.document.hidden) pinStreamlitTheme();
    });
  }
})();
</script></body></html>
""",
        height=0,
    )


def _sidebar_logo_node() -> str:
    """优先使用本地品牌图标，缺失时回退到内置 SVG。"""
    logo_path = Path(__file__).resolve().parent / "assets" / "branding" / "logo_zrld.png"
    try:
        if logo_path.is_file():
            raw = logo_path.read_bytes()
            b64 = base64.standard_b64encode(raw).decode("ascii")
            return f'<img src="data:image/png;base64,{b64}" alt="大宗绿测图标" />'
    except Exception:
        pass
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>'
        '</svg>'
    )


# 页面构建
# ======================================================================
st.set_page_config(page_title=APP_TITLE, layout="wide")
_inject_styles()
_inject_streamlit_theme_bridge()


# ─── 侧边栏 ───────────────────────────────────────────────────
def _render_sidebar() -> str | None:
    """返回选中的 run 目录路径"""
    # 品牌区
    _logo_node = _sidebar_logo_node()
    st.sidebar.markdown(f"""
<div class="sidebar-brand">
  <div class="sidebar-brand-logo">
    <div class="sidebar-logo-icon">
      {_logo_node}
    </div>
    <div>
      <div class="sidebar-brand-name">大宗绿测</div>
      <div class="sidebar-brand-sub">油价预测与绿色金融平台</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # 状态卡片（含：本机全局锁，避免多用户同时跑后台任务）
    run_count = max(len(_list_run_dirs()) - 1, 0)
    _tstat = _task_status_presentation()
    st.sidebar.markdown(f"""
<div class="sidebar-status">
  <div class="sidebar-status-row">
    <div class="status-dot {_tstat["sidebar_dot"]}"></div>
    <div class="status-lbl">任务状态</div>
    <div class="status-val {_tstat["sidebar_val_cls"]}">{_tstat["sidebar_text"]}</div>
  </div>
  <div class="sidebar-status-row">
    <div class="status-dot off"></div>
    <div class="status-lbl">累计运行</div>
    <div class="status-val">{run_count} 次</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # 历史运行选择
    run_dirs = _list_run_dirs()
    run_options = ["（本次运行后自动出现）"] + [os.path.abspath(p) for p in run_dirs]

    running_dir_sidebar = _hero_global_job_dir()
    is_running_sidebar = _global_job_busy_message() is not None
    if is_running_sidebar and running_dir_sidebar:
        st.session_state["selected_run_dir"] = os.path.abspath(running_dir_sidebar)

    default_idx = 0
    if "selected_run_dir" in st.session_state:
        try:
            default_idx = run_options.index(st.session_state["selected_run_dir"])
        except Exception:
            default_idx = 0

    st.sidebar.markdown('<p class="sidebar-section-label">历史运行</p>', unsafe_allow_html=True)

    run_display_options = ["（本次运行后自动出现）"]
    for p in run_dirs:
        name = os.path.basename(p)
        has_pred = os.path.isfile(os.path.join(p, "prediction_results.csv"))
        prefix = "已生成 " if has_pred else "处理中 "
        run_display_options.append(f"{prefix}{name}")

    selected_display = st.sidebar.selectbox(
        "选择输出目录", run_display_options,
        index=default_idx,
        disabled=bool(is_running_sidebar and running_dir_sidebar),
        label_visibility="collapsed",
    )
    selected_run_dir = None
    if selected_display == "（本次运行后自动出现）":
        selected_run_dir = "（本次运行后自动出现）"
    else:
        idx = run_display_options.index(selected_display)
        selected_run_dir = run_options[idx]

    _app_dir = Path(__file__).resolve().parent
    _manual_pdf = _app_dir / USER_MANUAL_PDF_NAME
    if not _manual_pdf.is_file():
        _parent_manual = _app_dir.parent / USER_MANUAL_PDF_NAME
        if _parent_manual.is_file():
            _manual_pdf = _parent_manual
    if _manual_pdf.is_file():
        _manual_url = (os.environ.get("USER_MANUAL_URL") or "").strip()
        if _manual_url:
            st.sidebar.link_button(
                "用户手册",
                _manual_url,
                use_container_width=True,
                help="环境变量 USER_MANUAL_URL",
                key="sidebar_manual_http_link",
            )
        else:
            _sidebar_pdf_open_new_tab_in_visitor_browser(_manual_pdf)
    else:
        st.sidebar.info(
            f"请将 **`{USER_MANUAL_PDF_NAME}`** 放到 **`{_app_dir}`**（或上一级 **`{_app_dir.parent}`**）后刷新页面。"
        )

    with st.sidebar.expander("AI 助手"):
        render_ai_newbie_guide_panel()

    return selected_run_dir


selected_run_dir = _render_sidebar()
st.markdown('<div id="sidebar-manual-link"></div>', unsafe_allow_html=True)

# ─── 全局状态 ───────────────────────────────────────────────
run_count = max(len(_list_run_dirs()) - 1, 0)
running_now = _global_job_busy_message() is not None
_maybe_start_auto_bond()
_ts_main = _task_status_presentation()

# Hero 区域「用户手册」按钮目标：优先环境变量 URL，其次本地 PDF 文件 URI
_hero_manual_href = "#"
_manual_url_env = (os.environ.get("USER_MANUAL_URL") or "").strip()
if _manual_url_env:
    _hero_manual_href = _manual_url_env
else:
    _app_dir = Path(__file__).resolve().parent
    _manual_pdf = _app_dir / USER_MANUAL_PDF_NAME
    if not _manual_pdf.is_file():
        _parent_manual = _app_dir.parent / USER_MANUAL_PDF_NAME
        if _parent_manual.is_file():
            _manual_pdf = _parent_manual
    if _manual_pdf.is_file():
        try:
            _hero_manual_href = _manual_pdf.resolve().as_uri()
        except Exception:
            _hero_manual_href = "#"

# ─── 顶部导航（真实可点击 Tabs） ───────────────────────────────
tab_run, tab_monitor, tab_results, tab_download = st.tabs(
    ["运行", "训练监控", "结果预览", "下载/导出"]
)
if "enable_forecast" not in st.session_state:
    st.session_state["enable_forecast"] = True
if "forecast_steps" not in st.session_state:
    st.session_state["forecast_steps"] = 1
if "cutoff_date" not in st.session_state:
    st.session_state["cutoff_date"] = None

# ======================================================================
# Tab 1: 运行
# ======================================================================
with tab_run:
    st.markdown(f"""
<div class="hero">
  <h1 class="hero-title">大宗绿测 · 油价预测平台</h1>
  <p class="hero-sub">基于 GRU 的油价预测与绿色金融风险分析一体化工作台</p>
  <div class="hero-actions">
    <a class="hero-btn-primary" href="#task-config">立即开始</a>
    <a class="hero-btn-secondary" href="{_hero_manual_href}" target="_blank" rel="noopener noreferrer">用户手册</a>
  </div>
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">当前状态</div>
      <div class="kpi-value {_ts_main["hero_kpi_cls"]}">{_ts_main["hero_kpi"]}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">当前目录</div>
      <div class="kpi-value blue" style="font-size:1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{os.path.basename(_hero_global_job_dir()) if running_now else "—"}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">启动时间</div>
      <div class="kpi-value" style="font-size:0.95rem;">{_hero_global_job_started_at() if running_now else "—"}</div>
    </div>
  </div>
</div>
<div class="pipeline-wrap">
  <div class="hero-steps">
    <div class="hero-step-item">
      <div class="hero-step-circle {"done" if run_count > 0 else "wait"}">1</div>
      <div class="hero-step-lbl {"done" if run_count > 0 else ""}">上传数据</div>
    </div>
    <div class="hero-connector {"done" if run_count > 0 else ""}"></div>
    <div class="hero-step-item">
      <div class="hero-step-circle {"active" if run_count == 0 else ("done" if run_count > 0 else "wait")}">2</div>
      <div class="hero-step-lbl {"active" if run_count == 0 else ("done" if run_count > 0 else "")}">配置参数</div>
    </div>
    <div class="hero-connector"></div>
    <div class="hero-step-item">
      <div class="hero-step-circle wait">3</div>
      <div class="hero-step-lbl">训练监控</div>
    </div>
    <div class="hero-connector"></div>
    <div class="hero-step-item">
      <div class="hero-step-circle wait">4</div>
      <div class="hero-step-lbl">查看结果</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="kpi-card" style="background:white;border:1px solid var(--border);">
<div class="kpi-label" style="color:var(--text-sub);">累计运行次数</div>
<div class="kpi-value" style="color:var(--text-main);">{run_count}</div>
</div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card" style="background:white;border:1px solid var(--border);">
<div class="kpi-label" style="color:var(--text-sub);">当前任务</div>
<div class="kpi-value {_ts_main["hero_kpi_cls"]}" style="font-size:1rem;">{_ts_main["hero_kpi"]}</div>
</div>""", unsafe_allow_html=True)
    with k3:
        sel_text = os.path.basename(selected_run_dir) if selected_run_dir and selected_run_dir != "（本次运行后自动出现）" else "未选择"
        st.markdown(f"""<div class="kpi-card" style="background:white;border:1px solid var(--border);">
<div class="kpi-label" style="color:var(--text-sub);">当前目录</div>
<div class="kpi-value" style="color:var(--text-main);font-size:0.9rem;">{sel_text}</div>
</div>""", unsafe_allow_html=True)

    with st.expander("实盘预测（默认开启）", expanded=True):
        st.session_state["enable_forecast"] = st.checkbox(
            "训练完成后，递推预测未来 H 天", value=bool(st.session_state["enable_forecast"]),
        )
        if st.session_state["enable_forecast"]:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.session_state["cutoff_date"] = st.date_input(
                    "截止日期（默认：数据最后一天）", value=st.session_state.get("cutoff_date", None),
                )
            with c2:
                st.session_state["forecast_steps"] = st.number_input(
                    "预测未来天数 H", min_value=1, max_value=90,
                    value=int(st.session_state.get("forecast_steps", 1) or 1), step=1,
                )
        else:
            st.session_state["cutoff_date"] = None
            st.session_state["forecast_steps"] = 0

    st.markdown('<div id="task-config" class="section-title">任务配置与启动</div>', unsafe_allow_html=True)
    st.markdown("**① 上传标准zip包，系统自动识别目录结构并校验关键文件（必选）**")
    uploaded = st.file_uploader("", type=["zip"])
    st.markdown("**② 选择Top-N与实盘预测参数，兼顾速度、稳定性和可解释性**")
    top_n = st.slider("随机森林特征选择 Top‑N(推荐选择top-15)", min_value=5, max_value=200, value=10, step=1)
    st.markdown("**建模参数**")
    epochs = st.number_input("训练轮数 Epochs", min_value=1, max_value=2000, value=200, step=10)
    st.markdown("**③ 任务启动后可实时查看日志与训练曲线，异常可直接排查**")
    enable_early_stopping = st.checkbox("启用早停 EarlyStopping（推荐）", value=True)
    auto_bond = st.checkbox(
        "训练成功后自动运行绿债预测",
        value=bool(st.session_state.get("auto_bond_pref", False)),
        help="油价 zip 内无需包含绿债特征；脚本使用工程内 bond_date/data.csv，并用本次 oil_pred.csv 覆盖其中油价列。",
    )
    st.session_state["auto_bond_pref"] = auto_bond

    cutoff_date = st.session_state.get("cutoff_date")
    forecast_steps = int(st.session_state.get("forecast_steps") or 0)
    if not st.session_state.get("enable_forecast"):
        cutoff_date = None
        forecast_steps = 0
    cutoff_date = cutoff_date.isoformat() if cutoff_date else None

    col1, col2 = st.columns([1, 2])
    with col1:
        run_clicked = st.button(
            "④ 开始运行",
            type="primary",
            disabled=uploaded is None
            or (_global_job_busy_message() is not None)
            or _other_session_holds_global_job(),
        )
    with col2:
        st.caption("提示：训练可能较久。开始运行后可以切到「训练监控」实时看曲线。")

    running_proc = st.session_state.get("run_proc")
    is_running = _global_job_busy_message() is not None

    if is_running:
        _rd = _hero_global_job_dir()
        _st = _hero_global_job_started_at()
        st.info(f"当前有后台任务正在运行：输出目录 `{_rd}`（开始时间：{_st}）。")
        colx, coly = st.columns([1, 1])
        with colx:
            auto_refresh_log = st.checkbox("实时刷新日志（每 2 秒）", value=True)
        with coly:
            stop_clicked = st.button("停止当前任务", type="secondary")
        if stop_clicked:
            ap = None
            try:
                data = _read_global_job_lock()
                if data:
                    ap = int(data.get("pid", 0))
            except Exception:
                ap = None
            if _is_proc_alive(running_proc):
                try:
                    running_proc.terminate()
                except Exception:
                    pass
            elif ap:
                _terminate_pid_tree(ap)
            st.warning("已发送停止信号，稍等几秒后刷新页面查看状态。")

        run_dir = _hero_global_job_dir() or ""
        runlog_path = os.path.join(run_dir, "run.log") if run_dir else ""
        last_lines = _tail_text_file(runlog_path, max_lines=400)
        st.subheader("实时终端输出（最近 400 行）")
        st.markdown('<div class="terminal-block">' + last_lines + '</div>', unsafe_allow_html=True)
        if auto_refresh_log:
            time.sleep(2)
            st.rerun()
    else:
        prev_proc = st.session_state.get("run_proc")
        prev_dir = st.session_state.get("run_output_dir")
        if prev_proc is not None and prev_dir:
            rc = _get_proc_returncode(prev_proc)
            if rc is not None:
                if rc == 0:
                    st.success(f"上一次任务已结束（退出码 {rc}）。可以去「结果预览 / 下载」查看输出。")
                    _bank_md_run = os.path.join(prev_dir, "bank_team_report.md")
                    if os.path.isfile(_bank_md_run):
                        st.divider()
                        st.caption("与「结果预览」相同逻辑：写入 `bank_team_report_ai.md`，并优先展示大模型摘要。")
                        try:
                            with st.spinner("正在生成企业银行团队 AI 解读…"):
                                _ai_run = generate_enterprise_bank_ai_report(prev_dir, force=False)
                            if _ai_run and str(_ai_run).strip():
                                _render_bank_report_forecast_card(
                                    label="企业银行团队报告（AI 解读）",
                                    body_markdown=str(_ai_run).strip(),
                                )
                            else:
                                with open(_bank_md_run, "r", encoding="utf-8", errors="replace") as _bf:
                                    _draft_run = _bf.read()
                                _render_bank_report_forecast_card(
                                    label="企业银行团队报告（脚本底稿）",
                                    body_markdown=_draft_run,
                                )
                                st.caption("AI 解读暂不可用，已展示脚本底稿。可刷新页面或在「结果预览」重新打开本目录以再次尝试生成。")
                        except Exception as _e_run_bank:
                            st.warning(f"AI 解读失败：{_e_run_bank}")
                            with open(_bank_md_run, "r", encoding="utf-8", errors="replace") as _bf:
                                _render_bank_report_forecast_card(
                                    label="企业银行团队报告（脚本底稿）",
                                    body_markdown=_bf.read(),
                                )
                    else:
                        st.caption("本次输出目录尚未生成 `bank_team_report.md`（可能训练未跑完或报告段失败）。请查看下方 run.log 或「结果预览」页提示。")
                else:
                    st.error(f"上一次任务异常结束（退出码 {rc}）。请查看下面的 `run.log` 最后几行。")
                runlog_path = os.path.join(prev_dir, "run.log")
                tail = _tail_text_file(runlog_path, max_lines=80)
                if tail:
                    st.subheader("run.log（最后 80 行）")
                    st.markdown('<div class="terminal-block">' + tail + '</div>', unsafe_allow_html=True)

    if run_clicked:
        existing = st.session_state.get("run_proc")
        if _is_proc_alive(existing):
            st.error("当前已有任务正在运行。请先点击「停止当前任务」或等待其结束，再启动新一轮。")
            st.stop()
        busy = _global_job_busy_message()
        if busy:
            st.error(busy)
            st.stop()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.abspath(os.path.join("web_runs", f"run_{ts}_top{top_n}"))
        os.makedirs(run_dir, exist_ok=True)

        st.write("正在解压数据…")
        extracted_root = os.path.join(run_dir, "_data")
        try:
            if os.path.isdir(extracted_root):
                shutil.rmtree(extracted_root, ignore_errors=True)
            os.makedirs(extracted_root, exist_ok=True)
            _extract_zip_to_dir(uploaded.getvalue(), extracted_root)
            data_root = _find_data_root(extracted_root)
            st.caption(f"解压完成。识别到的数据根目录：`{data_root}`")
            ok, msg = _validate_data_root(data_root)
            if not ok:
                st.error("数据包结构不符合要求，无法开始运行。")
                st.markdown(f"**原因**：{msg}")
                st.markdown("**解压后的目录结构（节选）**：")
                st.code(_summarize_dir(extracted_root), language="text")
                st.stop()
        except Exception:
            err = traceback.format_exc()
            err_path = os.path.join(run_dir, "extract_error.log")
            try:
                with open(err_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(err)
            except Exception:
                pass
            st.error("解压失败。下面是完整报错（也已写入本次输出目录的 `extract_error.log`）。")
            st.code(err, language="text")
            st.caption(f"本次输出目录：{run_dir}")
            st.stop()

        st.write("正在启动训练任务…（后台运行，可切到「训练监控」实时看曲线）")
        try:
            st.session_state["auto_bond_after_oil"] = bool(st.session_state.get("auto_bond_pref", False))
            bond_flag = os.path.join(run_dir, "bond_auto_started.flag")
            if os.path.isfile(bond_flag):
                try:
                    os.remove(bond_flag)
                except Exception:
                    pass
            _start_background_run(
                base_path=data_root, top_n=top_n, output_dir=run_dir,
                cutoff_date=cutoff_date, forecast_steps=int(forecast_steps or 0),
                epochs=int(epochs), enable_early_stopping=bool(enable_early_stopping),
            )
            proc = st.session_state.get("run_proc")
            pid = getattr(proc, "pid", None)
            st.success(f"已启动后台进程{f'（PID {pid}）' if pid else ''}。")
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
        except Exception:
            err = traceback.format_exc()
            err_path = os.path.join(run_dir, "start_error.log")
            try:
                with open(err_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(err)
            except Exception:
                pass
            st.error("启动训练进程失败。下面是完整报错（也已写入 `start_error.log`）。")
            st.code(err, language="text")
            st.caption(f"本次输出目录：{run_dir}")
            st.stop()

        st.session_state["selected_run_dir"] = os.path.abspath(run_dir)
        st.success("任务已启动。请到「训练监控」查看训练曲线，或在本页查看实时日志。")
        st.caption(f"本次运行输出目录：{run_dir}")
        st.rerun()

# ======================================================================
# Tab 2: 训练监控
# ======================================================================
with tab_monitor:
    st.subheader("训练监控")
    running_proc = st.session_state.get("run_proc")
    is_running = _global_job_busy_message() is not None
    running_dir = _hero_global_job_dir()

    run_dirs = _list_run_dirs()
    latest_dir = os.path.abspath(run_dirs[0]) if run_dirs else None
    active_dir_by_log = _pick_most_recent_active_run_dir(run_dirs)

    monitor_mode_options = []
    if running_dir:
        monitor_mode_options.append("监控：当前正在运行的任务（推荐）")
    if active_dir_by_log:
        monitor_mode_options.append("监控：最近在更新的运行目录（按 run.log 判断）")
    monitor_mode_options += [
        "监控：左侧栏选择的输出目录",
        "监控：最近一次运行（web_runs 下最新）",
        "监控：手动输入输出目录路径",
    ]

    monitor_mode = st.radio("监控来源", options=monitor_mode_options, horizontal=False,
                              help="你可以在这里指定要监控哪个程序/哪次运行的输出目录。")

    manual_dir = None
    if monitor_mode == "监控：手动输入输出目录路径":
        manual_dir = st.text_input(
            "输入要监控的输出目录路径",
            value="",
            placeholder=r"web_runs\run_YYYYMMDD_HHMMSS_topN",
        ).strip()

    monitor_dir = None
    if monitor_mode.startswith("监控：当前正在运行") and running_dir:
        monitor_dir = running_dir
    elif monitor_mode == "监控：最近在更新的运行目录（按 run.log 判断）":
        monitor_dir = active_dir_by_log
    elif monitor_mode == "监控：左侧栏选择的输出目录":
        if selected_run_dir and selected_run_dir != "（本次运行后自动出现）":
            monitor_dir = selected_run_dir
    elif monitor_mode == "监控：最近一次运行（web_runs 下最新）":
        monitor_dir = latest_dir
    elif monitor_mode == "监控：手动输入输出目录路径":
        monitor_dir = manual_dir or None

    if not monitor_dir:
        st.info("还没有可监控的输出目录。请先运行一次，或在上面手动输入一个输出目录路径。")
    else:
        if not os.path.isdir(monitor_dir):
            st.error(f"监控目录不存在：`{monitor_dir}`")
            st.stop()

        run_log = os.path.join(monitor_dir, "run.log")
        log_csv = os.path.join(monitor_dir, "training_log.csv")
        pred_csv = os.path.join(monitor_dir, "prediction_results.csv")

        log_is_active = _file_recently_updated(run_log, seconds=30)
        started_is_fresh = _run_dir_is_recently_started(monitor_dir, seconds=120)
        if (is_running and monitor_mode.startswith("监控：当前正在运行")) or log_is_active or started_is_fresh:
            st.info(f"正在监控：`{monitor_dir}`（训练中/日志更新中）")
        else:
            st.caption(f"正在监控：`{monitor_dir}`")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**training_log.csv**：{_file_status(log_csv)}")
        with c2:
            st.markdown(f"**prediction_results.csv**：{_file_status(pred_csv)}")
        with c3:
            st.markdown(f"**run.log**：{_file_status(run_log)}")

        auto_refresh_default = True if (is_running or log_is_active or started_is_fresh) else False
        auto_refresh = st.checkbox("自动刷新（训练进行中建议开启）", value=auto_refresh_default)
        refresh_seconds = st.slider("刷新间隔（秒）", min_value=2, max_value=10, value=3, step=1, disabled=not auto_refresh)
        st.button("手动刷新一次")
        _render_training_dashboard(monitor_dir, auto_refresh=auto_refresh, refresh_seconds=int(refresh_seconds))

        if (not os.path.isfile(log_csv)) and os.path.isfile(run_log):
            st.divider()
            st.markdown("**还没出现训练曲线？先看 run.log 最后几行（通常卡在数据加载/特征工程/尚未进入训练）。**")
            st.markdown('<div class="terminal-block">' + _tail_text_file(run_log, max_lines=40) + '</div>', unsafe_allow_html=True)

# ======================================================================
# Tab 3: 结果预览
# ======================================================================
with tab_results:
    st.subheader("结果预览")
    if selected_run_dir == "（本次运行后自动出现）":
        st.info("先在「运行」里跑一次，或者在左侧选择一个历史输出目录。")
    else:
        st.caption(f"当前预览目录：`{selected_run_dir}`")

        # 实盘预测大卡
        future_csv = os.path.join(selected_run_dir, "future_forecast.csv")
        df_future = _read_csv_safe(future_csv)
        if df_future is None or df_future.empty:
            st.info("未找到下一天实盘预测所需的 `future_forecast.csv`。")
        else:
            first_row = df_future.iloc[0]
            date_val = first_row.get("Date") if hasattr(first_row, "get") else first_row["Date"]
            pred_val = first_row.get("Pred_Price") if hasattr(first_row, "get") else first_row["Pred_Price"]
            try:
                dt = pd.to_datetime(date_val)
                date_text = dt.strftime("%Y年%m月%d日")
            except Exception:
                date_text = str(date_val)
            try:
                pred_text = f"{float(pred_val):.2f}"
            except Exception:
                pred_text = str(pred_val)

            st.markdown(f"""
<div class="forecast-card">
  <div>
    <div class="forecast-lbl">实盘预测下一天油价</div>
    <div class="forecast-val">{pred_text}</div>
    <div class="forecast-date">{date_text}</div>
  </div>
  <div style="flex:0 0 auto;">
    <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="15" width="40" height="35" rx="6" stroke="#0080bf" stroke-width="3"/>
      <rect x="10" y="15" width="40" height="12" rx="6" fill="rgba(0,128,191,.15)"/>
      <rect x="17" y="22" width="7" height="7" rx="2" fill="#0080bf"/>
      <rect x="27" y="22" width="7" height="7" rx="2" fill="rgba(0,163,224,.5)"/>
      <rect x="37" y="22" width="7" height="7" rx="2" fill="rgba(0,128,191,.25)"/>
      <path d="M19 9V22" stroke="#006a9e" stroke-width="3" stroke-linecap="round"/>
      <path d="M41 9V22" stroke="#006a9e" stroke-width="3" stroke-linecap="round"/>
    </svg>
  </div>
</div>
""", unsafe_allow_html=True)

        # 两列表格预览
        daily_csv = os.path.join(selected_run_dir, "daily_predictions_vs_actual.csv")
        pred_csv = os.path.join(selected_run_dir, "prediction_results.csv")
        col_a, col_b = st.columns(2)
        with col_a:
            df_daily = _read_csv_safe(daily_csv)
            if df_daily is None:
                st.info("未找到 `daily_predictions_vs_actual.csv`")
            else:
                st.markdown("**每日预测 vs 真实值**")
                st.dataframe(df_daily, use_container_width=True, height=360)
        with col_b:
            df_pred = _read_csv_safe(pred_csv)
            if df_pred is None:
                st.info("未找到 `prediction_results.csv`")
            else:
                st.markdown("**对齐后的完整结果**")
                st.dataframe(df_pred, use_container_width=True, height=360)

        st.divider()
        st.markdown("## 企业银行团队报告")
        st.caption("底稿由训练脚本生成；AI 解读与页末「AI 专家」共用同一套模型与油价专家角色设定。")
        _bank_report = os.path.join(selected_run_dir, "bank_team_report.md")
        if os.path.isfile(_bank_report):
            try:
                with st.spinner("正在生成企业银行团队 AI 解读（底稿就绪后自动执行；已缓存则瞬间完成）…"):
                    _ai_body = generate_enterprise_bank_ai_report(selected_run_dir, force=False)
                if _ai_body and str(_ai_body).strip():
                    _render_bank_report_forecast_card(
                        label="企业银行团队报告（AI 解读）",
                        body_markdown=str(_ai_body).strip(),
                    )
                else:
                    with open(_bank_report, "r", encoding="utf-8", errors="replace") as _bf:
                        _draft = _bf.read()
                    _render_bank_report_forecast_card(
                        label="企业银行团队报告（脚本底稿）",
                        body_markdown=_draft,
                    )
                    st.caption("AI 解读暂不可用，已展示脚本底稿。")
            except Exception as _e_bank:
                st.warning(f"AI 解读失败，已回退为脚本底稿：{_e_bank}")
                with open(_bank_report, "r", encoding="utf-8", errors="replace") as _bf:
                    _draft_e = _bf.read()
                _render_bank_report_forecast_card(
                    label="企业银行团队报告（脚本底稿）",
                    body_markdown=_draft_e,
                )
        else:
            st.info(
                "未找到 `bank_team_report.md`。训练正常结束时主脚本会写入该文件；若 run.log 出现「报告生成失败」且提示缺少 "
                "`tabulate`，请执行 `pip install tabulate` 后重新跑一遍，或已修复的脚本会在无 tabulate 时自动用文本表兜底。"
            )

        st.divider()
        st.markdown("### 预测图表")

        pred_imgs = ["future_forecast.png", "gru_predictions.png", "gru_returns.png"]
        explain_imgs = ["direction_confusion_matrix.png", "top_drivers_spearman.png", "top_drivers_rf_importance.png"]
        backtest_imgs = ["backtest_nav_curve.png"]

        for name in pred_imgs:
            path = os.path.join(selected_run_dir, name)
            if os.path.isfile(path):
                st.image(path, caption=name, use_container_width=True)

        st.markdown("### 模型解释")
        valid_explain = [os.path.join(selected_run_dir, n) for n in explain_imgs
                         if os.path.isfile(os.path.join(selected_run_dir, n))]
        if valid_explain:
            cols = st.columns(len(valid_explain))
            for i, p in enumerate(valid_explain):
                with cols[i]:
                    st.image(p, caption=os.path.basename(p), use_container_width=True)
        else:
            st.info("暂无解释类图像")

        st.markdown("### 策略回测")
        for name in backtest_imgs:
            path = os.path.join(selected_run_dir, name)
            if os.path.isfile(path):
                st.image(path, caption=name, use_container_width=True)

        st.divider()
        st.markdown("## 因子分析（主要驱动因素）")
        driver_csv = os.path.join(selected_run_dir, "driver_factor_analysis.csv")
        df_driver = _read_csv_safe(driver_csv)
        if df_driver is None or df_driver.empty:
            st.info("未找到 `driver_factor_analysis.csv`（请确认脚本已更新并跑完一次）。")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top 20（按 |Spearman| 排序）**")
                show_df = df_driver.copy()
                cols = [c for c in ["feature", "spearman_corr_with_return", "rf_importance", "spearman_pvalue"] if c in show_df.columns]
                st.dataframe(show_df[cols].head(20), use_container_width=True, height=360)
            with c2:
                st.markdown("**字段说明**")
                st.markdown("- **spearman_corr_with_return**：驱动因子与实际收益的 Spearman 相关性\n- **rf_importance**：随机森林对 WTI_Price_t_plus_H 的特征重要性")

        st.divider()
        st.markdown("## 风险区间 / 信号分类")
        risk_csv = os.path.join(selected_run_dir, "risk_signal_classification.csv")
        df_risk = _read_csv_safe(risk_csv)
        if df_risk is None or df_risk.empty:
            st.info("未找到 `risk_signal_classification.csv`。")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**样本预览（前 50 行）**")
                st.dataframe(df_risk.head(50), use_container_width=True, height=360)
            with c2:
                st.markdown("**分布统计**")
                if "RiskLevel" in df_risk.columns:
                    st.write("RiskLevel：")
                    st.dataframe(df_risk["RiskLevel"].value_counts(dropna=False).to_frame("count"), use_container_width=True)
                if "Signal" in df_risk.columns:
                    st.write("Signal：")
                    st.dataframe(df_risk["Signal"].value_counts(dropna=False).to_frame("count"), use_container_width=True)
                if "TrueDirection" in df_risk.columns and "PredDirection" in df_risk.columns:
                    acc = (df_risk["TrueDirection"] == df_risk["PredDirection"]).mean()
                    st.metric("方向一致率（含 FLAT）", f"{acc:.2%}")

        st.divider()
        st.markdown("## 回测（信号驱动策略 vs Buy&Hold）")
        bt_metrics_csv = os.path.join(selected_run_dir, "backtest_metrics.csv")
        bt_csv = os.path.join(selected_run_dir, "backtest_results.csv")
        df_bt_metrics = _read_csv_safe(bt_metrics_csv)
        if df_bt_metrics is not None and not df_bt_metrics.empty:
            m = df_bt_metrics.iloc[0].to_dict()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("策略总收益", f"{float(m.get('Strategy_TotalReturn', 0.0)):.2%}")
            c2.metric("基准总收益", f"{float(m.get('BuyHold_TotalReturn', 0.0)):.2%}")
            c3.metric("最大回撤", f"{float(m.get('Strategy_MaxDrawdown', 0.0)):.2%}")
            c4.metric("胜率", f"{float(m.get('Strategy_WinRate', 0.0)):.2%}")
        else:
            st.info("未找到 `backtest_metrics.csv`。")

        df_bt = _read_csv_safe(bt_csv)
        if df_bt is not None and not df_bt.empty:
            st.markdown("**回测明细（末尾 50 行）**")
            st.dataframe(df_bt.tail(50), use_container_width=True, height=360)

        st.divider()
        st.markdown("## 实盘预测：未来 H 天")
        df_future2 = _read_csv_safe(future_csv)
        if df_future2 is None or df_future2.empty:
            st.info("未找到 `future_forecast.csv`（需在运行时勾选「递推预测未来 H 天」）。")
        else:
            st.dataframe(df_future2, use_container_width=True, height=240)

        # ─── 新能源整合预测 ───────────────────────────────
        st.divider()
        st.markdown("## 新能源整合预测")

        oil_pred_csv_path = os.path.join(selected_run_dir, "prediction_results.csv")
        ne_need_oil_pred = not os.path.isfile(oil_pred_csv_path)
        if ne_need_oil_pred:
            st.info("先在「运行」里跑完石油预测并生成 `prediction_results.csv`，再点下面的「运行新能源整合预测」。")
        else:
            ne_series = st.text_input("要跑的序列（逗号分隔）", value="new_energy", key="ne_series")
            uploaded_ne_data = st.file_uploader("上传新能源数据 zip（必选）", type=["zip"], key="ne_data")
            c1, c2, c3 = st.columns(3)
            with c1:
                ne_conf_level = st.number_input("置信水平", min_value=0.8, max_value=0.99, value=0.95, step=0.05, key="ne_conf")
            with c2:
                ne_scale = st.number_input("收益缩放", min_value=10.0, max_value=300.0, value=100.0, step=10.0, key="ne_scale")
            with c3:
                ne_make_viz = st.checkbox("生成可视化图片（推荐）", value=True, key="ne_viz")

            ne_rebuild = st.checkbox("重建 returns", value=False, key="ne_rebuild")
            ne_proc_alive = _is_proc_alive(st.session_state.get("new_energy_proc"))
            run_ne = st.button(
                "运行新能源整合预测",
                type="primary",
                disabled=ne_proc_alive
                or (uploaded_ne_data is None)
                or (_global_job_busy_message() is not None)
                or _other_session_holds_global_job(),
                key="run_ne",
            )

            if run_ne:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                ne_run_dir = os.path.abspath(os.path.join(selected_run_dir, "new_energy_runs", f"new_energy_{ts}"))
                ne_data_dir = os.path.join(ne_run_dir, "_data")
                os.makedirs(ne_data_dir, exist_ok=True)
                try:
                    st.write("正在解压新能源数据…")
                    _extract_zip_to_dir(uploaded_ne_data.getvalue(), ne_data_dir)
                except Exception as e:
                    st.error(f"新能源数据解压失败：{e}")
                    st.stop()

                cmd = [
                    sys.executable, "-u", NE_SCRIPT_NAME,
                    "--oil-pred-csv", str(oil_pred_csv_path),
                    "--series", ne_series,
                    "--conf-level", str(float(ne_conf_level)),
                    "--scale-oil-return", str(float(ne_scale)),
                    "--out-dir", ne_run_dir,
                    "--desktop-base", ne_data_dir,
                ]
                if ne_rebuild:
                    cmd += ["--rebuild-returns"]
                if ne_make_viz:
                    cmd += ["--make-viz"]

                if not Path(os.path.abspath(os.path.join(os.path.dirname(__file__), NE_SCRIPT_NAME))).exists():
                    st.error(f"找不到脚本：`{NE_SCRIPT_NAME}`")
                else:
                    try:
                        _start_background_cmd(cmd=cmd, output_dir=ne_run_dir,
                                              log_filename="new_energy_run.log",
                                              started_marker_filename="new_energy_run.started",
                                              session_state_prefix="new_energy")
                    except RuntimeError as e:
                        st.error(str(e))
                        st.stop()
                    st.success(f"已启动新能源整合预测（输出：`{ne_run_dir}`）。请稍候…")
                    st.rerun()

            # 展示
            latest_ne_dir = st.session_state.get("new_energy_output_dir")
            if not latest_ne_dir or not isinstance(latest_ne_dir, str) or not os.path.isdir(latest_ne_dir):
                ne_parent = os.path.abspath(os.path.join(selected_run_dir, "new_energy_runs"))
                if os.path.isdir(ne_parent):
                    candidates = [os.path.join(ne_parent, n) for n in os.listdir(ne_parent)
                                  if os.path.isdir(os.path.join(ne_parent, n)) and n.startswith("new_energy_")]
                    if candidates:
                        candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                        latest_ne_dir = candidates[0]
                else:
                    latest_ne_dir = None

            if ne_proc_alive:
                st.info("新能源整合预测正在运行中…")
                ne_log_path = os.path.join(st.session_state.get("new_energy_output_dir") or "", "new_energy_run.log")
                st.markdown('<div class="terminal-block">' + _tail_text_file(ne_log_path, max_lines=200) + '</div>', unsafe_allow_html=True)

            if latest_ne_dir:
                ne_img_names = ["compare_sigma_timeseries.png", "compare_risk_distribution.png", "compare_ci_width_boxplot.png"]
                ne_img_paths = [os.path.join(latest_ne_dir, n) for n in ne_img_names
                                if os.path.isfile(os.path.join(latest_ne_dir, n))]
                if ne_img_paths:
                    for p in ne_img_paths:
                        st.image(p, caption=os.path.basename(p), use_container_width=True)
                else:
                    st.info("暂无对比可视化图片（可能还没跑完）。")

        # ─── 绿债预测 ─────────────────────────────────
        st.divider()
        st.markdown("## 绿债预测")

        uploaded_bond_data = st.file_uploader("上传绿债数据 zip（可选）", type=["zip"], key="bond_upload")
        st.caption("绿债侧特征不要求放进油价 zip；应用在项目目录 `bond_date/data.csv` 中预置。")

        bond_oil_pred = os.path.join(selected_run_dir, "oil_pred.csv")
        bond_proc_alive = _is_proc_alive(st.session_state.get("bond_proc"))
        c_b1, c_b2 = st.columns([1, 2])
        with c_b1:
            run_bond_clicked = st.button(
                "运行绿债预测（自动识别数据来源）",
                type="primary",
                disabled=bond_proc_alive
                or (not os.path.isfile(os.path.join(os.path.dirname(__file__), BOND_SCRIPT_NAME)))
                or (_global_job_busy_message() is not None)
                or _other_session_holds_global_job(),
                key="run_bond",
            )
        with c_b2:
            if not os.path.isfile(os.path.join(os.path.dirname(__file__), BOND_SCRIPT_NAME)):
                st.caption(f"未找到脚本 `{BOND_SCRIPT_NAME}`。")
            elif not os.path.isfile(bond_oil_pred):
                st.caption("需先完成石油训练并生成 `oil_pred.csv`。")
            else:
                st.caption("准备就绪。")

        if run_bond_clicked:
            if not os.path.isfile(bond_oil_pred):
                st.error("请先运行油价预测生成 oil_pred.csv")
                st.stop()

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), BOND_SCRIPT_NAME))
            bond_run_dir = os.path.abspath(os.path.join(selected_run_dir, "bond_user_runs", f"bond_{ts}"))
            os.makedirs(bond_run_dir, exist_ok=True)

            data_root = None
            if uploaded_bond_data is not None:
                st.write("使用用户上传的绿债数据")
                bond_data_dir = os.path.join(bond_run_dir, "_data")
                os.makedirs(bond_data_dir, exist_ok=True)
                try:
                    _extract_zip_to_dir(uploaded_bond_data.getvalue(), bond_data_dir)
                except Exception as e:
                    st.error(f"解压 bond zip 失败：{e}")
                    st.stop()
                processed_csv_path = os.path.join(bond_run_dir, "processed.csv")
                data_root = _find_data_root(bond_data_dir)
            elif os.path.isfile(_DEFAULT_BOND_ZIP):
                st.write(f"使用默认 zip：{_DEFAULT_BOND_ZIP}")
                bond_data_dir = os.path.join(bond_run_dir, "_data")
                os.makedirs(bond_data_dir, exist_ok=True)
                with open(_DEFAULT_BOND_ZIP, "rb") as f:
                    _extract_zip_to_dir(f.read(), bond_data_dir)
                processed_csv_path = os.path.join(bond_run_dir, "processed.csv")
                data_root = _find_data_root(bond_data_dir)
            elif os.path.isdir(_DEFAULT_BOND_DIR):
                st.write(f"使用默认文件夹：{_DEFAULT_BOND_DIR}")
                processed_csv_path = os.path.join(bond_run_dir, "processed.csv")
                data_root = _find_data_root(_DEFAULT_BOND_DIR)
            else:
                data_csv_to_use = _DEFAULT_BOND_DATA_CSV
                data_root = None

            if data_root is not None:
                pipeline_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "Data_Pipeline.py"))
                if not os.path.isfile(pipeline_script):
                    st.error("找不到 Data_Pipeline.py")
                    st.stop()
                result = subprocess.run(
                    [sys.executable, "-u", pipeline_script, "--data-root", data_root, "--output-csv", processed_csv_path],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    st.error("Data_Pipeline 运行失败")
                    st.code(result.stdout + "\n" + result.stderr)
                    st.stop()
                data_csv_to_use = processed_csv_path

            bond_out = os.path.abspath(os.path.join(bond_run_dir, "bond_integrated_output"))
            cmd = [
                sys.executable, "-u", script_path,
                "--data-csv", data_csv_to_use,
                "--oil-pred-csv", os.path.abspath(bond_oil_pred),
                "--out-dir", bond_out,
                "--output-csv", "bond_forecast_with_confidence.csv",
            ]
            try:
                _start_background_cmd(cmd=cmd, output_dir=bond_out, log_filename="bond_run.log",
                                      started_marker_filename="bond_run.started", session_state_prefix="bond")
            except RuntimeError as e:
                st.error(str(e))
                st.stop()
            st.success("已启动绿债预测（含数据处理），请稍候刷新查看结果。")
            st.rerun()

        if bond_proc_alive:
            bond_log = os.path.join(st.session_state.get("bond_output_dir") or "", "bond_run.log")
            st.info("绿债预测正在运行…")
            st.markdown('<div class="terminal-block">' + _tail_text_file(bond_log, max_lines=200) + '</div>', unsafe_allow_html=True)
            time.sleep(2)
            st.rerun()

        bond_csv_name = "bond_forecast_with_confidence.csv"
        bond_imgs = ["bond_forecast_with_confidence_plot_actual_vs_pred.png",
                      "bond_forecast_with_confidence_plot_ci.png",
                      "bond_forecast_with_confidence_plot_sigma.png",
                      "bond_forecast_with_confidence_plot_risk.png"]
        bond_dir_candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "bond_integrated_output")),
            os.path.join(selected_run_dir, "bond_integrated_output"),
        ]
        bond_user_root = os.path.join(selected_run_dir, "bond_user_runs")
        if os.path.isdir(bond_user_root):
            for name in os.listdir(bond_user_root):
                p = os.path.join(bond_user_root, name, "bond_integrated_output")
                if os.path.isdir(p):
                    bond_dir_candidates.append(p)
        try:
            bond_dir_candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        except Exception:
            pass
        bond_dir = None
        for d in bond_dir_candidates:
            if os.path.isfile(os.path.join(d, bond_csv_name)):
                bond_dir = d
                break

        if not bond_dir:
            st.info(f"未找到绿债预测输出（请先运行）。")
        else:
            bond_csv_path = os.path.join(bond_dir, bond_csv_name)
            df_bond = _read_csv_safe(bond_csv_path)
            if df_bond is None or df_bond.empty or "NewEnergy_Sigma" not in df_bond.columns:
                st.info("绿债预测 csv 为空或缺少 `NewEnergy_Sigma` 列。")
            else:
                quant = df_bond["NewEnergy_Sigma"].quantile([0.1, 0.5, 0.9]).to_dict()
                risk_counts = df_bond["RiskLevel"].value_counts(dropna=False).to_dict() if "RiskLevel" in df_bond.columns else {}
                st.write({"Sigma分位(0.1/0.5/0.9)": quant, "RiskLevel计数": risk_counts})
                cols = [c for c in ["Date_target", "NewEnergy_MeanPred", "NewEnergy_Sigma", "RiskLevel"] if c in df_bond.columns]
                if cols:
                    st.dataframe(df_bond[cols].head(30), use_container_width=True, height=240)
                found_imgs = [os.path.join(bond_dir, n) for n in bond_imgs if os.path.isfile(os.path.join(bond_dir, n))]
                if found_imgs:
                    for p in found_imgs:
                        st.image(p, caption=os.path.basename(p), use_container_width=True)
                else:
                    st.info("暂无绿债预测 png 图片输出。")

        st.divider()
        st.markdown("**终端输出（run.log）**")
        runlog = os.path.join(selected_run_dir, "run.log")
        if os.path.isfile(runlog):
            tail = _tail_text_file(runlog, max_lines=200)
            st.markdown('<div class="terminal-block">' + tail + '</div>', unsafe_allow_html=True)
        else:
            st.info("未找到 run.log。")

        st.divider()
        st.subheader("AI 专家：油价预测 & 新能源风险分析")
        st.caption("会话咨询与「企业银行团队报告」的自动生成，均通过同一 yibuapi 接口；企业银行摘要 = 脚本底稿 + 油价专家角色下的行内摘要格式。")
        render_ai_expert_panel(
            workspace_root=Path(__file__).resolve().parent,
            selected_run_dir=selected_run_dir,
        )

# ======================================================================
# Tab 4: 下载/导出
# ======================================================================
with tab_download:
    st.subheader("下载/导出")
    if selected_run_dir == "（本次运行后自动出现）":
        st.info("先在「运行」里跑一次，或者在左侧选择一个历史输出目录。")
    else:
        files = []
        try:
            for name in sorted(os.listdir(selected_run_dir)):
                p = os.path.join(selected_run_dir, name)
                if os.path.isfile(p):
                    files.append(p)
        except Exception:
            files = []

        if not files:
            st.info("没有找到输出文件。")
        else:
            st.markdown(f"当前目录：`{selected_run_dir}`")
            st.markdown("点击按钮下载文件（CSV/PNG/H5/LOG）：")
            for p in files:
                try:
                    with open(p, "rb") as f:
                        st.download_button(
                            label=f"下载 {os.path.basename(p)}",
                            data=f.read(),
                            file_name=os.path.basename(p),
                            mime="application/octet-stream",
                        )
                except Exception as e:
                    st.warning(f"无法读取 {os.path.basename(p)}：{e}")
