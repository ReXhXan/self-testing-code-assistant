from assistant.extract import count_tests, extract_code, syntax_error


def test_extract_fenced_largest_block():
    reply = "Here:\n```python\nx = 1\n```\nand\n```python\ndef f():\n    return 2\n```"
    assert extract_code(reply) == "def f():\n    return 2\n"


def test_extract_unfenced():
    assert extract_code("def g(): pass") == "def g(): pass\n"


def test_syntax_error_detected():
    assert syntax_error("def f(:\n") .startswith("SyntaxError")
    assert syntax_error("x = 1\n") is None


def test_count_tests():
    assert count_tests("def test_a(): pass\ndef helper(): pass\nasync def test_b(): pass\n") == 2
    assert count_tests("not python (") == 0
