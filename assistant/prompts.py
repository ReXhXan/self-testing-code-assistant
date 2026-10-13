"""Prompt templates for the three agent roles: coder, tester, repairer."""

CODER_SYSTEM = (
    "You are a senior Python engineer. Write a single self-contained Python module that solves the task. "
    "Use only the standard library unless told otherwise. Include type hints and docstrings. "
    "Reply with ONE ```python code block and nothing else."
)

TESTER_SYSTEM = (
    "You are a meticulous QA engineer. Write pytest tests for a module named `solution`. "
    "Import from it with `from solution import ...`. Cover normal cases, edge cases and error handling "
    "described in the task. Do not test behaviour the task does not specify. "
    "Reply with ONE ```python code block and nothing else."
)

REPAIR_SYSTEM = (
    "You are debugging a Python module. The tests are the specification; fix the CODE so they pass. "
    "Reply with the full corrected module in ONE ```python code block and nothing else."
)


def coder_prompt(task: str) -> str:
    return f"TASK:\n{task}\n"


def tester_prompt(task: str, code: str) -> str:
    # Tests are written from the task. The code is shown only so names and signatures match.
    return f"TASK:\n{task}\n\nPUBLIC INTERFACE (module `solution`):\n```python\n{code}```\n"


def repair_prompt(task: str, code: str, tests: str, failures: str) -> str:
    return (f"TASK:\n{task}\n\nCODE:\n```python\n{code}```\n\nTESTS:\n```python\n{tests}```\n\n"
            f"FAILURES:\n```\n{failures}\n```\n")
