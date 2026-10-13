"""Run generated code + tests in an isolated subprocess with a timeout and resource limits.

Isolation used here:
  * fresh temporary directory as cwd (deleted afterwards)
  * a separate Python process (`python -I`: ignores PYTHON* env vars and user site-packages)
  * minimal environment (no API keys or other secrets inherited)
  * wall-clock timeout, plus CPU-time / address-space / file-size rlimits on POSIX
This stops accidents and runaway loops. It does NOT make running hostile code safe; use the Docker image
(non-root, --network none) for that.
"""
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_SUMMARY = re.compile(r"(\d+) (passed|failed|error|errors)")


@dataclass
class RunResult:
    passed: bool
    n_passed: int
    n_failed: int
    output: str
    timed_out: bool = False

    @property
    def failure_report(self) -> str:
        """Trimmed output to feed back into the repair prompt."""
        return self.output[-4000:]


def _limits(memory_mb: int, cpu_s: int):
    def apply():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        mem = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024,) * 2)
    return apply


def run_tests(code: str, tests: str, timeout_s: float = 20.0, memory_mb: int = 512,
              module_name: str = "solution") -> RunResult:
    with tempfile.TemporaryDirectory(prefix="sandbox-") as tmp:
        d = Path(tmp)
        (d / f"{module_name}.py").write_text(code, encoding="utf-8")
        (d / f"test_{module_name}.py").write_text(tests, encoding="utf-8")
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": tmp, "HOME": tmp}
        cmd = [sys.executable, "-I", "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
               "--rootdir", tmp, str(d)]
        # -I drops cwd from sys.path, so put the sandbox dir back explicitly via a conftest
        (d / "conftest.py").write_text(f"import sys\nsys.path.insert(0, {tmp!r})\n", encoding="utf-8")
        preexec = _limits(memory_mb, int(timeout_s) + 1) if os.name == "posix" else None
        try:
            p = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True,
                               timeout=timeout_s, preexec_fn=preexec)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode(errors="replace")
            return RunResult(False, 0, 0, out + f"\nTIMEOUT: tests exceeded {timeout_s}s", timed_out=True)
        out = (p.stdout + p.stderr).replace(tmp, "<sandbox>")
        counts = {k: int(n) for n, k in _SUMMARY.findall(out)}
        n_pass = counts.get("passed", 0)
        n_fail = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
        return RunResult(p.returncode == 0 and n_pass > 0, n_pass, n_fail, out)
