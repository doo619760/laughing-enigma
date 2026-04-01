"""Code helper tool - analyze, explain, and transform code."""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path


def analyze_python(code: str) -> str:
    """Analyze Python code structure."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax Error at line {e.lineno}: {e.msg}"

    classes = []
    functions = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({"name": node.name, "line": node.lineno, "methods": methods})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not any(node.lineno > c.get("line", 0) for c in classes if isinstance(c, dict)):
                args = [a.arg for a in node.args.args]
                functions.append({"name": node.name, "line": node.lineno, "args": args})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    lines = [f"Python Code Analysis ({len(code.splitlines())} lines):"]

    if imports:
        lines.append(f"\nImports ({len(imports)}):")
        for imp in imports[:20]:
            lines.append(f"  - {imp}")
        if len(imports) > 20:
            lines.append(f"  ... and {len(imports) - 20} more")

    if classes:
        lines.append(f"\nClasses ({len(classes)}):")
        for cls in classes:
            lines.append(f"  class {cls['name']} (line {cls['line']})")
            for m in cls["methods"]:
                lines.append(f"    - {m}()")

    if functions:
        lines.append(f"\nFunctions ({len(functions)}):")
        for fn in functions:
            args_str = ", ".join(fn["args"])
            lines.append(f"  def {fn['name']}({args_str}) (line {fn['line']})")

    return "\n".join(lines)


def count_lines(code: str) -> str:
    """Count lines of code, comments, and blank lines."""
    lines = code.splitlines()
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())
    comments = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*")))
    code_lines = total - blank - comments

    return (
        f"Line count:\n"
        f"  Total:    {total}\n"
        f"  Code:     {code_lines}\n"
        f"  Comments: {comments}\n"
        f"  Blank:    {blank}"
    )


def find_patterns(code: str, pattern: str) -> str:
    """Find regex pattern matches in code."""
    try:
        matches = list(re.finditer(pattern, code, re.MULTILINE))
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    if not matches:
        return f"No matches found for pattern: {pattern}"

    lines = [f"Found {len(matches)} match(es) for '{pattern}':"]
    for i, match in enumerate(matches[:25]):
        line_num = code[:match.start()].count("\n") + 1
        lines.append(f"  Line {line_num}: {match.group()[:80]}")

    if len(matches) > 25:
        lines.append(f"  ... and {len(matches) - 25} more matches")

    return "\n".join(lines)


def run_python_snippet(code: str) -> str:
    """Run a small Python snippet safely (with timeout)."""
    # Basic safety checks
    dangerous_patterns = [
        r"\bos\.system\b", r"\bsubprocess\b", r"\b__import__\b",
        r"\beval\b", r"\bexec\b", r"\bopen\b.*['\"]w",
        r"\bshutil\.(rmtree|move)\b", r"\bos\.(remove|unlink|rmdir)\b",
    ]
    for pat in dangerous_patterns:
        if re.search(pat, code):
            return "Error: Code contains potentially unsafe operations. Refusing to execute."

    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nStderr:\n{result.stderr}"
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (10s limit)."
    except Exception as e:
        return f"Error: {e}"


TOOL_DEFINITION = {
    "name": "code_helper",
    "description": (
        "Analyze, inspect, and run code. Can analyze Python structure (classes, "
        "functions, imports), count lines, search for patterns with regex, or run "
        "small Python snippets safely."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["analyze", "count_lines", "find_pattern", "run_snippet"],
                "description": "What to do with the code",
            },
            "code": {
                "type": "string",
                "description": "The code to analyze or run",
            },
            "pattern": {
                "type": "string",
                "description": "Regex pattern (for 'find_pattern' action)",
            },
        },
        "required": ["action", "code"],
    },
}


def handle(input_data: dict) -> str:
    """Handle a tool call from the API."""
    action = input_data["action"]
    code = input_data.get("code", "")

    if action == "analyze":
        return analyze_python(code)
    elif action == "count_lines":
        return count_lines(code)
    elif action == "find_pattern":
        pattern = input_data.get("pattern", "")
        if not pattern:
            return "Error: 'pattern' is required for find_pattern action."
        return find_patterns(code, pattern)
    elif action == "run_snippet":
        return run_python_snippet(code)
    else:
        return f"Error: Unknown action '{action}'"
