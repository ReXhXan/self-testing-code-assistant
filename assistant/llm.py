"""Pluggable LLM clients: OpenAI / Groq (OpenAI-compatible), Ollama (local) and offline Mock."""
from collections import deque

import httpx


class LLM:
    def generate(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleLLM(LLM):
    def __init__(self, model: str, api_key: str, base_url: str | None = None, temperature: float = 0.2):
        from openai import OpenAI
        self.client, self.model, self.temperature = OpenAI(api_key=api_key, base_url=base_url), model, temperature

    def generate(self, system, prompt):
        r = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content or ""


class OllamaLLM(LLM):
    def __init__(self, model: str, base_url: str, temperature: float = 0.2):
        self.model, self.url, self.temperature = model, base_url.rstrip("/") + "/api/chat", temperature

    def generate(self, system, prompt):
        r = httpx.post(self.url, timeout=300, json={
            "model": self.model, "stream": False, "options": {"temperature": self.temperature},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        })
        r.raise_for_status()
        return r.json()["message"]["content"]


class ScriptedLLM(LLM):
    """Returns pre-baked responses in order. Used by tests to simulate fail -> repair cycles."""

    def __init__(self, responses: list[str]):
        self.responses, self.calls = deque(responses), []

    def generate(self, system, prompt):
        self.calls.append((system, prompt))
        if not self.responses:
            raise RuntimeError("ScriptedLLM ran out of responses")
        return self.responses.popleft()


_DEMO_BUGGY = '''```python
def fizzbuzz(n: int) -> str:
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    if n % 15 == 0:
        return "FizzBuzz"
    return str(n)
```'''
_DEMO_FIXED = _DEMO_BUGGY.replace(
    '    if n % 3 == 0:\n        return "Fizz"\n    if n % 5 == 0:\n        return "Buzz"\n    if n % 15 == 0:\n        return "FizzBuzz"',
    '    if n % 15 == 0:\n        return "FizzBuzz"\n    if n % 3 == 0:\n        return "Fizz"\n    if n % 5 == 0:\n        return "Buzz"')
_DEMO_TESTS = '''```python
from solution import fizzbuzz

def test_plain():
    assert fizzbuzz(1) == "1"

def test_fizz():
    assert fizzbuzz(9) == "Fizz"

def test_buzz():
    assert fizzbuzz(10) == "Buzz"

def test_fizzbuzz():
    assert fizzbuzz(30) == "FizzBuzz"
```'''


class MockLLM(LLM):
    """Offline demo: deliberately writes a buggy FizzBuzz first, then fixes it when shown the failure."""

    def generate(self, system, prompt):
        if "Write pytest tests" in system:
            return _DEMO_TESTS
        if "FAILURES" in prompt:
            return _DEMO_FIXED
        return _DEMO_BUGGY


def get_llm(settings) -> LLM:
    p, t = settings.llm_provider.lower(), settings.llm_temperature
    if p == "openai":
        return OpenAICompatibleLLM(settings.llm_model, settings.openai_api_key, temperature=t)
    if p == "groq":
        return OpenAICompatibleLLM(settings.llm_model, settings.groq_api_key,
                                   base_url="https://api.groq.com/openai/v1", temperature=t)
    if p == "ollama":
        return OllamaLLM(settings.llm_model, settings.ollama_base_url, temperature=t)
    return MockLLM()
