import pytest

from assistant.agent import SelfTestingAgent
from assistant.llm import MockLLM, ScriptedLLM

GOOD = "```python\ndef square(x):\n    return x * x\n```"
BAD = "```python\ndef square(x):\n    return x + x\n```"
TESTS = "```python\nfrom solution import square\ndef test_sq():\n    assert square(3) == 9\n```"


def test_passes_first_try():
    llm = ScriptedLLM([GOOD, TESTS])
    res = SelfTestingAgent(llm, max_iterations=3).run("square a number")
    assert res.success and len(res.iterations) == 1


def test_repairs_from_failure_feedback():
    llm = ScriptedLLM([BAD, TESTS, GOOD])
    res = SelfTestingAgent(llm, max_iterations=3).run("square a number")
    assert res.success and [i.passed for i in res.iterations] == [False, True]
    repair_prompt = llm.calls[2][1]
    assert "FAILURES" in repair_prompt and "assert" in repair_prompt


def test_gives_up_after_max_iterations():
    llm = ScriptedLLM([BAD, TESTS, BAD, BAD])
    res = SelfTestingAgent(llm, max_iterations=3).run("square a number")
    assert not res.success and len(res.iterations) == 3


def test_user_supplied_tests_skip_generation():
    llm = ScriptedLLM([GOOD])
    res = SelfTestingAgent(llm).run("square", tests="from solution import square\ndef test_s():\n    assert square(4) == 16\n")
    assert res.success and len(llm.calls) == 1


def test_syntax_error_triggers_regeneration():
    llm = ScriptedLLM(["```python\ndef square(x:\n```", GOOD, TESTS])
    assert SelfTestingAgent(llm).run("square").success


def test_rejects_empty_test_suite():
    with pytest.raises(ValueError):
        SelfTestingAgent(ScriptedLLM([GOOD, "```python\nx = 1\n```"])).run("square")


def test_mock_llm_demo_needs_one_repair():
    res = SelfTestingAgent(MockLLM(), max_iterations=3).run("fizzbuzz")
    assert res.success and len(res.iterations) == 2
