"""安全四则运算工具。"""
import ast
import operator
from typing import Union

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_EXPRESSION_LEN = 200
# Python 3.14+ 移除 ast.Num；3.8+ 数字字面量均为 ast.Constant
_AST_NUM = getattr(ast, "Num", None)


def _safe_eval_node(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("仅支持数字常量")
    if _AST_NUM is not None and isinstance(node, _AST_NUM):
        return node.n
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return _ALLOWED_OPS[type(node.op)](left, right)
    raise ValueError("表达式包含不允许的运算")


def calculate(expression: str) -> str:
    """
    对简单数学表达式求值。
    仅允许数字、括号、+ - * / // % ** 运算。
    """
    expr = (expression or "").strip()
    if not expr:
        return "请输入数学表达式，例如：12 * (3 + 4)"
    if len(expr) > _MAX_EXPRESSION_LEN:
        return "表达式过长，请简化后重试。"

    try:
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval_node(tree.body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except ZeroDivisionError:
        return "错误：除数不能为零。"
    except Exception:
        return "无法计算该表达式，请检查格式。"


TOOL_NAME = "calculator"
TOOL_DESCRIPTION = "基础四则运算，例如：`(10 + 5) * 2`"
