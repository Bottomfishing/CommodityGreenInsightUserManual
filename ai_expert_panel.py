# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


@dataclass
class AiConfig:
    base_url: str
    api_key: str
    model: str = "gpt-4o"


# 兜底写死 key：避免环境变量/导入 gptapifree.py 失败导致的无法获取 API_KEY。
# 注意：这是你当前项目里 `gptapifree.py` 的同一个 key。
_HARD_BASE_URL = "https://yibuapi.com/v1"
_HARD_API_KEY = "sk-xbAnmbF8Dn2r6mPhOAZH7Q9gWNFtbJ3OUqmkMw8bkkIZaa4b"


def _get_ai_config() -> AiConfig:
    """
    获取 AI 配置：
    - 优先读取环境变量 `YIBU_API_KEY` 和 `YIBU_BASE_URL`
    - 否则尝试从本项目已有的 `gptapifree.py` 中导入 API_KEY（避免你重复填 key）
    """
    base_url = os.environ.get("YIBU_BASE_URL") or _HARD_BASE_URL
    api_key = os.environ.get("YIBU_API_KEY") or _HARD_API_KEY

    if not api_key:
        raise RuntimeError("找不到 AI API_KEY：请设置环境变量 `YIBU_API_KEY` 或检查代码内兜底配置。")

    return AiConfig(base_url=base_url, api_key=api_key)


def _safe_json_extract_content(data: dict[str, Any]) -> str | None:
    """
    尝试按 OpenAI 兼容格式提取 message.content；如果接口返回结构不同，就尽量 fallback。
    """
    try:
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None


def call_chat_completion(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    cfg = _get_ai_config()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.api_key}",
    }
    json_data = {
        "model": cfg.model,
        "messages": messages,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "stream": False,
    }

    # 用 urllib 发请求，避免 httpx 依赖缺失导致 Streamlit 起不来
    url = f"{cfg.base_url}/chat/completions"
    body = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        raise RuntimeError(f"AI 请求失败：{e}")
    content = _safe_json_extract_content(data)
    if content is None:
        # fallback：把整个响应压缩展示给你定位结构差异
        return f"[AI响应解析失败] 返回内容：{json.dumps(data, ensure_ascii=False)[:2000]}"
    return content


def _build_context_oil(selected_run_dir: str) -> str:
    if not selected_run_dir or selected_run_dir == "（本次运行后自动出现）":
        return ""

    pred_csv = Path(selected_run_dir) / "prediction_results.csv"
    if not pred_csv.exists():
        return ""

    try:
        df = pd.read_csv(pred_csv)
        if df.empty:
            return ""
        # 简单做摘要喂给 AI
        if "Date_target" in df.columns and "GRU_Pred_Return" in df.columns:
            df["Date_target"] = pd.to_datetime(df["Date_target"], errors="coerce")
            last_date = df["Date_target"].dropna().max()
            pred_tail = df.dropna(subset=["Date_target", "GRU_Pred_Return"]).sort_values("Date_target").tail(7)
            pred_stats = {
                "last_date": str(last_date)[:10] if pd.notna(last_date) else "",
                "pred_return_mean_7d": float(pred_tail["GRU_Pred_Return"].mean()) if not pred_tail.empty else None,
                "pred_return_std_7d": float(pred_tail["GRU_Pred_Return"].std(ddof=0)) if not pred_tail.empty else None,
            }
            return "当前油价预测结果摘要：" + "\n" + "\n".join([f"- {k}: {v}" for k, v in pred_stats.items()]) + "\n"
    except Exception:
        return ""
    return ""


def _build_context_new_energy(workspace_root: Path) -> str:
    # 你整合脚本输出目录
    ne_dir = workspace_root / "new_energy_integrated_outputs"
    if not ne_dir.exists():
        return ""

    # 默认用 new_energy_conf0.95（如果没有就取任意 csv）
    fp = ne_dir / "new_energy_forecast_new_energy_conf0.95.csv"
    if not fp.exists():
        candidates = list(ne_dir.glob("new_energy_forecast_*_conf*.csv"))
        if not candidates:
            return ""
        fp = candidates[0]

    try:
        df = pd.read_csv(fp)
        if df.empty or "NewEnergy_Sigma" not in df.columns:
            return ""
        q = df["NewEnergy_Sigma"].quantile([0.1, 0.5, 0.9]).to_dict()
        risk_counts = df["RiskLevel"].value_counts(dropna=False).to_dict() if "RiskLevel" in df.columns else {}
        return (
            f"当前新能源（从 {fp.name} 读取）摘要：\n"
            f"- Sigma分位(0.1/0.5/0.9)：{q}\n"
            f"- 风险等级计数：{risk_counts}\n"
        )
    except Exception:
        return ""
    return ""


def _system_prompt(mode: str) -> str:
    if mode == "oil":
        return (
            "你是油价预测与风险分析专家。"
            "用户会提供油价预测结果（如 Date_target、GRU_Pred_Return 等）或提问。"
            "请用中文回答：先给结论，再解释依据（用数据摘要），最后给可执行的风险控制/跟踪建议。"
            "如果缺少关键数据，请明确列出需要哪些字段。"
        )
    if mode == "new_energy":
        return (
            "你是新能源股票/指数风险分析专家。"
            "用户会提供新能源波动率代理（Sigma）、置信区间(CI_low/CI_high)、以及风险等级(RiskLevel)。"
            "请用中文回答：先给结论，再解释：波动率来自什么、置信区间意味着什么、风险等级如何理解；"
            "最后给投资者/研究员可执行的跟踪指标与情景分析建议。"
            "如果缺少关键数据，请明确列出需要哪些字段。"
        )
    return "你是一个专业AI助手。"


def generate_enterprise_bank_ai_report(selected_run_dir: str, *, force: bool = False) -> str | None:
    """
    基于本次运行目录中的 `bank_team_report.md` 与预测摘要，调用大模型生成「企业银行团队」AI 解读，
    写入 `bank_team_report_ai.md`。底稿不存在则返回 None；若 AI 文件已存在且新于底稿且不 force，则直接读盘返回。
    """
    if not selected_run_dir or selected_run_dir == "（本次运行后自动出现）":
        return None
    root = Path(selected_run_dir)
    report_md = root / "bank_team_report.md"
    ai_md = root / "bank_team_report_ai.md"
    if not report_md.is_file():
        return None
    if not force and ai_md.is_file() and ai_md.stat().st_mtime >= report_md.stat().st_mtime:
        return ai_md.read_text(encoding="utf-8", errors="replace")

    base_text = report_md.read_text(encoding="utf-8", errors="replace")
    ctx = _build_context_oil(selected_run_dir)
    # 与结果页「油价预测专家」同一套角色设定，并叠加银行执行摘要输出格式
    sys_prompt = (
        _system_prompt("oil")
        + " 现需在同一份回答中输出「企业银行团队」面向行内的执行摘要：严格基于用户提供的「模型输出报告」与「数据摘要」，"
        "不得编造材料中不存在的数字或结论。"
        "全文使用 Markdown；一级标题必须为「企业银行团队执行摘要（AI）」；其下依次给出：核心结论（≤5条短句）、"
        "风险关注点、建议跟踪指标与复核要点、合规提示（模型输出仅供参考等）。语气正式、简洁。"
    )
    user_body = (
        "【模型输出报告（Markdown）】\n"
        + base_text
        + "\n\n【数据摘要】\n"
        + (ctx if ctx.strip() else "（无额外摘要）")
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_body},
    ]
    answer = call_chat_completion(messages, temperature=0.25, max_tokens=2800)
    ans = (answer or "").strip()
    if not ans:
        return None
    if ans.startswith("[AI响应解析失败]"):
        return None
    ai_md.write_text(ans + "\n", encoding="utf-8")
    return ans


def render_ai_expert_panel(workspace_root: Path, selected_run_dir: str) -> None:
    st.subheader("AI专家：油价预测 & 新能源风险分析")
    st.caption("这是一个直接调用你现有 yibuapi 接口的聊天面板，不需要 fastapi。")

    mode = st.radio("选择专家", ["油价预测专家", "新能源股票专家"], horizontal=True)
    mode_key = "oil" if mode == "油价预测专家" else "new_energy"

    # 聊天历史
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    # 仅初始化空时给一句引导
    if not st.session_state["ai_messages"]:
        st.session_state["ai_messages"].append(
            {"role": "assistant", "content": "你好！你可以问：（1）基于我当前的预测结果怎么看趋势与风险；（2）新能源波动率/Sigma如何解读；（3）给我一个可执行的跟踪清单。"}
        )

    for m in st.session_state["ai_messages"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    user_prompt = st.chat_input("输入你的问题（例如：用我这份结果分析未来风险）")
    if not user_prompt:
        return

    st.session_state["ai_messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        # 组装上下文摘要（尽量喂有用信息，避免把整份 csv 全量塞给模型）
        context_lines = []
        if mode_key == "oil":
            context_lines.append(_build_context_oil(selected_run_dir))
        else:
            context_lines.append(_build_context_new_energy(workspace_root))
        context = "\n".join([c for c in context_lines if c])

        sys_prompt = _system_prompt(mode_key)
        messages: list[dict[str, Any]] = [{"role": "system", "content": sys_prompt}]
        if context.strip():
            messages.append({"role": "user", "content": f"你可以参考的当前数据摘要如下：\n{context}"})
        messages.append({"role": "user", "content": user_prompt})

        with st.spinner("AI思考中..."):
            try:
                answer = call_chat_completion(messages)
            except Exception as e:
                answer = f"AI调用失败：{e}"

        st.write(answer)
        st.session_state["ai_messages"].append({"role": "assistant", "content": answer})


def render_ai_newbie_guide_panel() -> None:
    """
    首页（tab_run）给新手的 AI 引导：基于压缩包/输出规则做问答式指引（不一次性输出全文）。
    """
    st.subheader("AI新手引导：这个Web怎么用")
    

    # 用独立的 session key，避免和“AI专家面板”的对话混在一起
    if "newbie_ai_messages" not in st.session_state:
        st.session_state["newbie_ai_messages"] = []

    if not st.session_state["newbie_ai_messages"]:
        st.session_state["newbie_ai_messages"].append(
            {
                "role": "assistant",
                "content": (
                    "你好！你可以直接问我：\n"
                    "（1）我的 zip 里哪些文件是必须的？\n"
                    "（2）点“开始运行”后，结果分别在哪个 tab 看？\n"
                    "（3）`prediction_results.csv` / `gru_returns.png` 这些怎么解读？"
                ),
            }
        )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.caption("")
    with col2:
        st.button(
            "清空对话",
            on_click=lambda: st.session_state.update({"newbie_ai_messages": []}),
            use_container_width=True,
        )

    # 展示聊天历史
    for m in st.session_state["newbie_ai_messages"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    user_prompt = st.chat_input("输入你的问题（例如：zip 缺了 X 会怎样？）")
    if not user_prompt:
        return

    st.session_state["newbie_ai_messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # 只把“规则要点”作为上下文，避免一次性输出全文教程
    newbie_knowledge = (
        "以下是本项目在读取数据与产出方面的关键规则（仅用于回答用户问题）：\n"
        "- 必须：`raw_data/WTI_futuresprice.csv`\n"
        "- 可选：`raw_data/WTI_spotprice.xls`（读取失败则用空表）\n"
        "- 必须（金融市场）：`raw_data/DXY_Index.csv`、`raw_data/SP500_Index.csv`、"
        "`raw_data/US10Y_Yield.csv`、`raw_data/VIX_index.csv`、`raw_data/OVX_index.csv`\n"
        "- 必须（情绪指标）：`raw_data/情绪指标/oil price.csv`、`raw_data/情绪指标/gas price.csv`\n"
        "- 必须（供需侧）："
        "`能源基本面与下游产业/一、原油供需情况/美国商业原油库存.csv`（程序里 skiprows=4）与"
        "`能源基本面与下游产业/一、原油供需情况/美国原油产量周度数据.csv`（程序里 skiprows=4）\n"
        "- 可选（供需侧）：`能源基本面与下游产业/一、原油供需情况/活跃钻井机数量.xlsx`\n"
        "- 必须（地缘事件）：`能源基本面与下游产业/三、地缘大事记.xlsx` "
        "（读取 sheet0；需要“开始日期”；“关键影响/备注”若可转数值会用于强度）\n"
        "- 运行后会生成/输出：`prediction_results.csv`、`daily_predictions_vs_actual.csv`、"
        "`driver_factor_analysis.csv`、`risk_signal_classification.csv`、`backtest_results.csv`、以及若干 png 图片。\n"
        "- Web 使用：tab 分别是“运行 / 训练监控 / 结果预览 / 下载/导出”，并在“运行”里上传 zip、设置 Top-N、点击开始。\n"
    )

    sys_prompt = (
        "你是一个面对新手的、耐心且解释力强的技术助理。"
        "用户会问“怎么放文件/怎么操作/输出怎么读/缺文件会怎样”。"
        "重要要求：不要一次性输出整篇教程；只回答用户当前问题。"
        "如果用户问总览（例如说“给我完整教程”），你才允许给结构化的总览。"
    )

    messages: list[dict[str, Any]] = [{"role": "system", "content": sys_prompt}]
    # 将知识点和用户对话串起来，但不把“整篇教程”当输出目标
    messages.append({"role": "user", "content": newbie_knowledge})
    messages.extend(st.session_state["newbie_ai_messages"][-8:])  # 限制上下文长度

    with st.spinner("AI思考中..."):
        try:
            answer = call_chat_completion(messages, temperature=0.2, max_tokens=900)
        except Exception as e:
            answer = f"AI调用失败：{e}"

    st.session_state["newbie_ai_messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)

