import json

from fastapi.testclient import TestClient

from assistant.api import create_app
from assistant.cli import main
from assistant.llm import MockLLM


def test_cli_writes_artifacts(tmp_path, capsys):
    code = main(["fizzbuzz", "--out", str(tmp_path), "--max-iter", "3"], llm=MockLLM())
    assert code == 0
    assert "def fizzbuzz" in (tmp_path / "solution.py").read_text()
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["success"] and len(report["iterations"]) == 2
    assert "SUCCESS" in capsys.readouterr().err


def test_cli_exit_code_on_failure():
    assert main(["fizzbuzz", "--max-iter", "1"], llm=MockLLM()) == 1


def test_api_solve():
    client = TestClient(create_app(llm=MockLLM()))
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/solve", json={"task": "fizzbuzz", "max_iterations": 3})
    assert r.status_code == 200 and r.json()["success"]
