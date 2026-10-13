"""Command-line interface.

    python -m assistant "Write fizzbuzz(n) returning 'Fizz', 'Buzz', 'FizzBuzz' or str(n)"
    python -m assistant --task-file task.md --tests my_tests.py --out runs/fizz
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from .agent import SelfTestingAgent
from .config import get_settings
from .llm import get_llm


def main(argv=None, llm=None) -> int:
    s = get_settings()
    ap = argparse.ArgumentParser(prog="assistant", description="Generate code, test it, and repair it.")
    ap.add_argument("task", nargs="?", help="task description")
    ap.add_argument("--task-file")
    ap.add_argument("--tests", help="use this pytest file as the spec instead of generating tests")
    ap.add_argument("--max-iter", type=int, default=s.max_iterations)
    ap.add_argument("--timeout", type=float, default=s.sandbox_timeout_s)
    ap.add_argument("--out", help="directory to write solution.py, test_solution.py and report.json")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    a = ap.parse_args(argv)
    logging.basicConfig(level=s.log_level.upper(), format="%(levelname)s %(message)s")

    task = Path(a.task_file).read_text() if a.task_file else a.task
    if not task:
        ap.error("give a task or --task-file")
    tests = Path(a.tests).read_text() if a.tests else None

    agent = SelfTestingAgent(llm or get_llm(s), a.max_iter, a.timeout, s.sandbox_memory_mb)
    show = (lambda it: print(f"[iter {it.n}] {'PASS' if it.passed else 'FAIL'} "
                             f"{it.n_passed} passed, {it.n_failed} failed"
                             + (" (timeout)" if it.timed_out else ""), file=sys.stderr))
    res = agent.run(task, tests, on_iteration=show)

    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "solution.py").write_text(res.code)
        (out / "test_solution.py").write_text(res.tests)
        (out / "report.json").write_text(json.dumps(res.to_dict(), indent=2))
    print(json.dumps(res.to_dict(), indent=2) if a.json else res.code)
    print(f"{'SUCCESS' if res.success else 'GAVE UP'} after {len(res.iterations)} iteration(s)", file=sys.stderr)
    return 0 if res.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
