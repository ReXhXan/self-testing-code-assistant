from assistant.sandbox import run_tests

CODE = "def add(a, b):\n    return a + b\n"


def test_passing_run():
    r = run_tests(CODE, "from solution import add\ndef test_add():\n    assert add(2, 3) == 5\n")
    assert r.passed and r.n_passed == 1 and r.n_failed == 0


def test_failing_run_reports_assertion():
    r = run_tests(CODE, "from solution import add\ndef test_add():\n    assert add(2, 2) == 5\n")
    assert not r.passed and r.n_failed == 1 and "assert" in r.failure_report


def test_timeout_kills_infinite_loop():
    r = run_tests("def f():\n    while True: pass\n",
                  "from solution import f\ndef test_f():\n    f()\n", timeout_s=2)
    assert not r.passed and (r.timed_out or r.n_failed >= 1)


def test_secrets_not_inherited(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    r = run_tests("import os\nKEY = os.environ.get('OPENAI_API_KEY')\n",
                  "from solution import KEY\ndef test_key():\n    assert KEY is None\n")
    assert r.passed


def test_no_tests_is_not_a_pass():
    assert not run_tests(CODE, "x = 1\n").passed


def test_import_error_is_failure():
    r = run_tests("raise ImportError('boom')\n", "from solution import add\ndef test_x():\n    pass\n")
    assert not r.passed
