"""Tests for AI Assistant tools."""

import os
import json
import tempfile
import pytest

from ai_assistant.tools import calculator, file_reader, datetime_tool, task_manager, code_helper


class TestCalculator:
    def test_basic_arithmetic(self):
        assert "Result: 5" in calculator.calculate("2 + 3")
        assert "Result: 6" in calculator.calculate("2 * 3")
        assert "Result: 2" in calculator.calculate("10 / 5")
        assert "Result: 8" in calculator.calculate("2 ** 3")

    def test_math_functions(self):
        assert "Result: 12" in calculator.calculate("sqrt(144)")
        assert "Result: 5" in calculator.calculate("abs(-5)")
        assert "Result: 120" in calculator.calculate("factorial(5)")

    def test_constants(self):
        result = calculator.calculate("pi")
        assert "3.14159" in result

    def test_complex_expressions(self):
        assert "Result: 21" in calculator.calculate("sqrt(144) + 3**2")

    def test_division_by_zero(self):
        result = calculator.calculate("1 / 0")
        assert "Error" in result

    def test_invalid_expression(self):
        result = calculator.calculate("import os")
        assert "Error" in result

    def test_handle(self):
        result = calculator.handle({"expression": "2 + 2"})
        assert "Result: 4" in result


class TestFileReader:
    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line 1\nline 2\nline 3\n")
            path = f.name
        try:
            result = file_reader.read_file(path)
            assert "line 1" in result
            assert "line 2" in result
            assert "3 lines" in result
        finally:
            os.unlink(path)

    def test_read_file_with_range(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("a\nb\nc\nd\ne\n")
            path = f.name
        try:
            result = file_reader.read_file(path, start_line=2, end_line=4)
            assert "b" in result
            assert "c" in result
            assert "d" in result
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        result = file_reader.read_file("/nonexistent/file.txt")
        assert "Error" in result

    def test_list_directory(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "test.txt"), "w").close()
            result = file_reader.list_directory(d)
            assert "test.txt" in result

    def test_handle(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello")
            path = f.name
        try:
            result = file_reader.handle({"action": "read", "path": path})
            assert "hello" in result
        finally:
            os.unlink(path)


class TestDatetime:
    def test_current_time(self):
        result = datetime_tool.get_current_time()
        assert "UTC" in result
        assert "Date:" in result

    def test_date_difference(self):
        result = datetime_tool.date_difference("2024-01-01", "2024-01-31")
        assert "30 days" in result

    def test_add_to_date(self):
        result = datetime_tool.add_to_date("2024-01-01", days=10)
        assert "January 11, 2024" in result

    def test_calendar(self):
        result = datetime_tool.show_calendar(2024, 1)
        assert "January" in result

    def test_handle(self):
        result = datetime_tool.handle({"action": "now"})
        assert "UTC" in result


class TestTaskManager:
    def setup_method(self):
        """Use a temp file for tasks."""
        self._original = task_manager.TASKS_FILE
        self._tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self._tmpfile.close()
        # Monkey-patch the tasks file path
        import ai_assistant.tools.task_manager as tm
        from pathlib import Path
        tm.TASKS_FILE = Path(self._tmpfile.name)
        # Clear it
        with open(self._tmpfile.name, "w") as f:
            json.dump([], f)

    def teardown_method(self):
        import ai_assistant.tools.task_manager as tm
        tm.TASKS_FILE = self._original
        os.unlink(self._tmpfile.name)

    def test_add_task(self):
        result = task_manager.add_task("Test task", "high")
        assert "Added task #1" in result
        assert "Test task" in result

    def test_list_tasks(self):
        task_manager.add_task("Task A")
        task_manager.add_task("Task B", "high")
        result = task_manager.list_tasks()
        assert "Task A" in result
        assert "Task B" in result

    def test_update_task(self):
        task_manager.add_task("Do something")
        result = task_manager.update_task(1, status="completed")
        assert "Updated" in result

    def test_delete_task(self):
        task_manager.add_task("Delete me")
        result = task_manager.delete_task(1)
        assert "Deleted" in result

    def test_handle(self):
        result = task_manager.handle({"action": "add", "title": "Handle test"})
        assert "Added" in result


class TestCodeHelper:
    def test_analyze_python(self):
        code = '''
import os
from pathlib import Path

class MyClass:
    def method(self):
        pass

def standalone(x, y):
    return x + y
'''
        result = code_helper.analyze_python(code)
        assert "MyClass" in result
        assert "method" in result
        assert "os" in result

    def test_count_lines(self):
        code = "# comment\ncode\n\nmore_code\n"
        result = code_helper.count_lines(code)
        assert "Total:" in result

    def test_find_patterns(self):
        code = "def foo():\n    pass\ndef bar():\n    pass\n"
        result = code_helper.find_patterns(code, r"def \w+")
        assert "2 match" in result

    def test_run_snippet(self):
        result = code_helper.run_python_snippet("print(2 + 2)")
        assert "4" in result

    def test_run_snippet_safety(self):
        result = code_helper.run_python_snippet("import subprocess; subprocess.run(['ls'])")
        assert "unsafe" in result.lower() or "error" in result.lower()

    def test_handle(self):
        result = code_helper.handle({"action": "count_lines", "code": "a\nb\nc"})
        assert "Total:" in result
