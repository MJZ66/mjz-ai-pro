import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.math_intent import try_quick_calculate  # noqa: E402


def test_calculate_phrase_with_parens():
    out = try_quick_calculate("计算 (125+76)*9")
    assert out is not None
    assert "1809" in out


def test_plain_expression():
    out = try_quick_calculate("(10+5)*2")
    assert out is not None
    assert "30" in out


def test_non_math_returns_none():
    assert try_quick_calculate("这个人的专业是什么？") is None
