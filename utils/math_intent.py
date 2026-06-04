"""从用户输入中识别简单算术并走本地计算器。"""
from __future__ import annotations

import re
from typing import Optional

from tools.calculator import calculate

_PREFIX = re.compile(
    r"^(?:请?\s*计算|算一下|算算|计算|求|算)[:：\s]*",
    re.IGNORECASE,
)
_EXPR_CHARS = re.compile(r"^[\d\s+\-*/().%^eE]+$")
_CANDIDATE = re.compile(
    r"\((?:[^()]+|\([^()]*\))*\)|"
    r"[\d.]+\s*[\+\-\*/]\s*[\d.]+(?:\s*[\+\-\*/]\s*[\d.]+)*|"
    r"[\d.]+\s*[\+\-\*/]\s*\([^)]+\)",
)


def _normalize_expr(expr: str) -> str:
    return (
        expr.replace("×", "*")
        .replace("÷", "/")
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
    )


def try_quick_calculate(user_text: str) -> Optional[str]:
    """
    若输入为简单算式则返回格式化结果字符串，否则返回 None。
    示例：「计算 (125+76)*9」→ 「(125+76)*9 = 1809」
    """
    raw = (user_text or "").strip()
    if not raw:
        return None

    stripped = _PREFIX.sub("", raw).strip() or raw
    candidates = [stripped]
    candidates.extend(m.group(0) for m in _CANDIDATE.finditer(stripped))

    seen = set()
    for cand in candidates:
        expr = _normalize_expr(cand)
        if not expr or expr in seen:
            continue
        seen.add(expr)
        if not _EXPR_CHARS.match(expr):
            continue
        if not re.search(r"[\+\-\*/]", expr):
            continue
        result = calculate(expr)
        if result.startswith("无法") or result.startswith("请输入"):
            continue
        if result.startswith("错误") or result.startswith("表达式"):
            continue
        return f"**{cand.strip()}** = **{result}**"

    return None


def messages_need_assistant_reply(messages: list) -> bool:
    visible = [m for m in messages if m.get("role") in ("user", "assistant")]
    return bool(visible) and visible[-1]["role"] == "user"
