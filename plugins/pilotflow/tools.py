"""PilotFlow project management tools.

These tools provide project management workflow capabilities.
They use lark-cli for Feishu API operations.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List

from tools.registry import tool_error, tool_result

logger = logging.getLogger(__name__)

PROFILE = os.environ.get("PILOTFLOW_LARK_PROFILE", "pilotflow-contest")
CHAT_ID = os.environ.get("PILOTFLOW_TEST_CHAT_ID", "")
BASE_TOKEN = os.environ.get("PILOTFLOW_BASE_TOKEN", "")
BASE_TABLE_ID = os.environ.get("PILOTFLOW_BASE_TABLE_ID", "")


def _run_lark(args: list[str]) -> tuple[bool, str, str]:
    """Run lark-cli and return (ok, stdout, stderr)."""
    cmd = ["lark-cli"] + args + ["--profile", PROFILE]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return False, "", "lark-cli timeout"
    except FileNotFoundError:
        return False, "", "lark-cli not found. Install: npm i -g @anthropic-ai/lark-cli"


# ---------------------------------------------------------------------------
# pilotflow_generate_plan
# ---------------------------------------------------------------------------

PILOTFLOW_GENERATE_PLAN_SCHEMA = {
    "name": "pilotflow_generate_plan",
    "description": (
        "从用户的自然语言输入中提取项目信息，生成结构化的项目执行计划。"
        "返回目标、成员、交付物、截止时间和风险。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "input_text": {
                "type": "string",
                "description": "用户的原始输入文本。",
            },
        },
        "required": ["input_text"],
    },
}


def _handle_generate_plan(params: Dict[str, Any]) -> str:
    """Parse user input and return a structured project plan."""
    text = params.get("input_text", "")

    # This tool returns structured data for the LLM to use.
    # The LLM will call Feishu tools (doc_create, task_create, etc.) separately.
    return tool_result(json.dumps({
        "status": "plan_generated",
        "input": text,
        "instructions": (
            "请根据以上输入生成项目执行计划，然后依次调用飞书工具创建产物：\n"
            "1. feishu_doc_create — 创建项目文档\n"
            "2. feishu_task_create — 创建任务\n"
            "3. feishu_im_send — 发送项目入口消息\n"
            "4. feishu_im_send — 发送交付总结"
        ),
    }, ensure_ascii=False))


# ---------------------------------------------------------------------------
# pilotflow_detect_risks
# ---------------------------------------------------------------------------

PILOTFLOW_DETECT_RISKS_SCHEMA = {
    "name": "pilotflow_detect_risks",
    "description": (
        "检测项目计划中的潜在风险：负责人缺失、截止时间模糊、交付物不明确等。"
        "返回风险列表和建议处理方式。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "members": {
                "type": "array",
                "items": {"type": "string"},
                "description": "项目成员列表。",
            },
            "deliverables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "交付物列表。",
            },
            "deadline": {
                "type": "string",
                "description": "截止时间。",
            },
        },
        "required": ["members", "deliverables", "deadline"],
    },
}


def _handle_detect_risks(params: Dict[str, Any]) -> str:
    """Detect risks in a project plan."""
    members = params.get("members", [])
    deliverables = params.get("deliverables", [])
    deadline = params.get("deadline", "")

    risks = []
    if not members:
        risks.append({"level": "high", "title": "未指定项目成员", "suggestion": "请确认至少一名负责人"})
    if not deliverables:
        risks.append({"level": "high", "title": "未指定交付物", "suggestion": "请明确具体交付物"})
    if not deadline or deadline in ("TBD", "待确认", ""):
        risks.append({"level": "medium", "title": "截止时间不明确", "suggestion": "请确认具体截止日期"})

    if not risks:
        return tool_result("未检测到风险，计划信息完整。")

    return tool_result(json.dumps({
        "risks_found": len(risks),
        "risks": risks,
        "instructions": "请将以上风险发送到群里，让用户确认处理方式。",
    }, ensure_ascii=False))


# ---------------------------------------------------------------------------
# pilotflow_create_project_space
# ---------------------------------------------------------------------------

PILOTFLOW_CREATE_PROJECT_SPACE_SCHEMA = {
    "name": "pilotflow_create_project_space",
    "description": (
        "一键创建项目空间：飞书文档 + 多维表格记录 + 飞书任务 + 项目入口消息。"
        "需要先确认 PILOTFLOW_TEST_CHAT_ID、PILOTFLOW_BASE_TOKEN、PILOTFLOW_BASE_TABLE_ID 环境变量已配置。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "项目标题。",
            },
            "goal": {
                "type": "string",
                "description": "项目目标。",
            },
            "members": {
                "type": "array",
                "items": {"type": "string"},
                "description": "项目成员。",
            },
            "deliverables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "交付物列表。",
            },
            "deadline": {
                "type": "string",
                "description": "截止时间。",
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "已知风险。",
            },
        },
        "required": ["title", "goal"],
    },
}


def _handle_create_project_space(params: Dict[str, Any]) -> str:
    """Create a complete project space in Feishu."""
    title = params.get("title", "项目")
    goal = params.get("goal", "")
    members = params.get("members", [])
    deliverables = params.get("deliverables", [])
    deadline = params.get("deadline", "")
    risks = params.get("risks", [])

    if not CHAT_ID:
        return tool_error("缺少 PILOTFLOW_TEST_CHAT_ID 环境变量")

    artifacts = []

    # 1. Create project doc
    doc_content = f"# {title}\n\n## 目标\n{goal}\n\n"
    if members:
        doc_content += f"## 成员\n{', '.join(members)}\n\n"
    if deliverables:
        doc_content += f"## 交付物\n" + "\n".join(f"- {d}" for d in deliverables) + "\n\n"
    if deadline:
        doc_content += f"## 截止时间\n{deadline}\n\n"
    if risks:
        doc_content += f"## 风险\n" + "\n".join(f"- {r}" for r in risks) + "\n\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(doc_content)
        tmp_path = f.name

    try:
        ok, stdout, stderr = _run_lark([
            "docs", "+create",
            "--api-version", "v2",
            "--as", "bot",
            "--title", f"{title} - 项目简报",
            "--doc-format", "markdown",
            "--content", f"@{tmp_path}",
        ])
        if ok:
            artifacts.append(f"文档: {title} - 项目简报")
        else:
            logger.warning("doc create failed: %s", stderr)
    finally:
        os.unlink(tmp_path)

    # 2. Write base record
    if BASE_TOKEN and BASE_TABLE_ID:
        record = {
            "fields": {
                "type": "project",
                "title": title,
                "owner": ", ".join(members) if members else "TBD",
                "due_date": deadline or "TBD",
                "status": "active",
                "risk_level": "high" if risks else "low",
            }
        }
        ok, stdout, stderr = _run_lark([
            "base", "+record-batch-create",
            "--as", "bot",
            "--base-token", BASE_TOKEN,
            "--table-id", BASE_TABLE_ID,
            "--json", json.dumps([record]),
        ])
        if ok:
            artifacts.append("多维表格: 项目状态记录")

    # 3. Create task
    if deliverables:
        for d in deliverables[:3]:  # Max 3 tasks
            ok, stdout, stderr = _run_lark([
                "task", "+create",
                "--as", "bot",
                "--summary", f"{d}",
                "--description", f"项目: {title}\n负责人: {', '.join(members) if members else 'TBD'}",
            ])
            if ok:
                artifacts.append(f"任务: {d}")

    # 4. Send entry message
    entry_text = f"📌 项目入口: {title}\n目标: {goal}"
    if members:
        entry_text += f"\n成员: {', '.join(members)}"
    if deadline:
        entry_text += f"\n截止: {deadline}"

    ok, stdout, stderr = _run_lark([
        "im", "+messages-send",
        "--as", "bot",
        "--chat-id", CHAT_ID,
        "--text", entry_text,
    ])
    if ok:
        artifacts.append("项目入口消息")

    if not artifacts:
        return tool_error("未能创建任何产物，请检查环境变量和 lark-cli 配置。")

    return tool_result(json.dumps({
        "status": "project_space_created",
        "title": title,
        "artifacts": artifacts,
        "message": f"已创建 {len(artifacts)} 个产物: {', '.join(artifacts)}",
    }, ensure_ascii=False))


# ---------------------------------------------------------------------------
# pilotflow_send_summary
# ---------------------------------------------------------------------------

PILOTFLOW_SEND_SUMMARY_SCHEMA = {
    "name": "pilotflow_send_summary",
    "description": "向飞书群发送项目执行总结，包含已创建的产物列表。",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "项目标题。"},
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "已创建的产物列表。",
            },
            "status": {"type": "string", "description": "项目状态（如 completed, in_progress）。"},
        },
        "required": ["title", "artifacts"],
    },
}


def _handle_send_summary(params: Dict[str, Any]) -> str:
    """Send a delivery summary to the Feishu group."""
    title = params.get("title", "")
    artifacts = params.get("artifacts", [])
    status = params.get("status", "completed")

    if not CHAT_ID:
        return tool_error("缺少 PILOTFLOW_TEST_CHAT_ID 环境变量")

    summary = f"✅ {title} — 执行完成\n\n已创建产物:\n"
    for a in artifacts:
        summary += f"  • {a}\n"
    summary += f"\n状态: {status}"

    ok, stdout, stderr = _run_lark([
        "im", "+messages-send",
        "--as", "bot",
        "--chat-id", CHAT_ID,
        "--text", summary,
    ])
    if not ok:
        return tool_error(f"发送总结失败: {stderr}")

    return tool_result(f"已发送项目总结到群聊: {title}")
