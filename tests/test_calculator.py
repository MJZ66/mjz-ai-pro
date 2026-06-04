import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.calculator import calculate


def test_addition():
    assert calculate("1 + 2") == "3"


def test_complex_expression():
    assert calculate("(10 + 5) * 2") == "30"


def test_resume_style_expression():
    assert calculate("(125+76)*9") == "1809"


def test_division_by_zero():
    assert "除数" in calculate("1 / 0")


def test_invalid_expression():
    assert "非法" in calculate("import os") or "无法" in calculate("import os")
