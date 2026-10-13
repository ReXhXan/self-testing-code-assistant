"""The generate -> test -> run -> repair loop."""
import logging
from dataclasses import asdict, dataclass, field

from . import prompts
from .extract import count_tests, extract_code, syntax_error
from .llm import LLM
from .sandbox import RunResult, run_tests

log = logging.getLogger(__name__)


@dataclass
class Iteration:
    n: int
    passed: bool
    n_passed: int
    n_failed: int
    timed_out: bool
    output: str


@dataclass
class AgentResult:
    success: bool
    code: str
    tests: str
    iterations: list[Iteration] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class SelfTestingAgent:
    def __init__(self, llm: LLM, max_iterations: int = 4, timeout_s: float = 20.0, memory_mb: int = 512):
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        self.llm, self.max_iterations, self.timeout_s, self.memory_mb = llm, max_iterations, timeout_s, memory_mb

    def _code(self, system: str, prompt: str) -> str:
        code = extract_code(self.llm.generate(system, prompt))
        if err := syntax_error(code):
            # one cheap retry with the error attached before spending a sandbox run
            code = extract_code(self.llm.generate(system, prompt + f"\nYour previous reply had a {err}. Fix it."))
        return code

    def run(self, task: str, tests: str | None = None, on_iteration=None) -> AgentResult:
        """Solve `task`. Pass `tests` to use your own spec instead of generating one."""
        code = self._code(prompts.CODER_SYSTEM, prompts.coder_prompt(task))
        if tests is None:
            tests = self._code(prompts.TESTER_SYSTEM, prompts.tester_prompt(task, code))
        if count_tests(tests) == 0:
            raise ValueError("no pytest test functions were produced")

        result = AgentResult(success=False, code=code, tests=tests)
        for i in range(1, self.max_iterations + 1):
            run: RunResult = run_tests(code, tests, self.timeout_s, self.memory_mb)
            it = Iteration(i, run.passed, run.n_passed, run.n_failed, run.timed_out, run.failure_report)
            result.iterations.append(it)
            log.info("iteration %d: passed=%s (%d ok, %d failed)", i, run.passed, run.n_passed, run.n_failed)
            if on_iteration:
                on_iteration(it)
            if run.passed:
                result.success, result.code = True, code
                return result
            if i < self.max_iterations:
                code = self._code(prompts.REPAIR_SYSTEM,
                                  prompts.repair_prompt(task, code, tests, run.failure_report))
                result.code = code
        return result
