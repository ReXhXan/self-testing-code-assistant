"""Pull Python code out of LLM replies and sanity-check it before running anything."""
import ast
import re

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(reply: str) -> str:
    """Return the largest fenced block, or the whole reply if the model skipped fences."""
    blocks = _FENCE.findall(reply)
    code = max(blocks, key=len) if blocks else reply
    return code.strip() + "\n"


def syntax_error(code: str) -> str | None:
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno})"


def count_tests(test_code: str) -> int:
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return 0
    return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")
               for n in ast.walk(tree))
