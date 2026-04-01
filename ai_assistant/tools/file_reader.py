"""File reader tool - read and analyze local files."""

import os
from pathlib import Path


MAX_FILE_SIZE = 1_000_000  # 1MB limit
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".conf",
    ".sh", ".bash", ".zsh", ".fish",
    ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs", ".rb",
    ".sql", ".csv", ".xml", ".env.example",
    ".gitignore", ".dockerignore", ".editorconfig",
    "Makefile", "Dockerfile", "Jenkinsfile",
}


def read_file(filepath: str, start_line: int = 0, end_line: int = 0) -> str:
    """Read a file's contents with optional line range."""
    path = Path(filepath).expanduser().resolve()

    if not path.exists():
        return f"Error: File not found: {filepath}"

    if not path.is_file():
        return f"Error: Not a file: {filepath}"

    # Check extension
    if path.suffix and path.suffix not in ALLOWED_EXTENSIONS and path.name not in ALLOWED_EXTENSIONS:
        return f"Error: File type '{path.suffix}' is not supported for reading."

    # Check size
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        return f"Error: File is too large ({size:,} bytes). Max is {MAX_FILE_SIZE:,} bytes."

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        return f"Error: Permission denied: {filepath}"

    total_lines = len(lines)

    if start_line or end_line:
        start = max(0, start_line - 1)  # Convert to 0-indexed
        end = end_line if end_line else total_lines
        lines = lines[start:end]
        header = f"File: {path.name} (lines {start + 1}-{min(end, total_lines)} of {total_lines})\n"
    else:
        header = f"File: {path.name} ({total_lines} lines, {size:,} bytes)\n"

    # Add line numbers
    offset = (start_line - 1) if start_line else 0
    numbered = [f"{i + offset + 1:4d} | {line}" for i, line in enumerate(lines)]

    return header + "".join(numbered)


def list_directory(dirpath: str) -> str:
    """List contents of a directory."""
    path = Path(dirpath).expanduser().resolve()

    if not path.exists():
        return f"Error: Directory not found: {dirpath}"

    if not path.is_dir():
        return f"Error: Not a directory: {dirpath}"

    entries = []
    try:
        for entry in sorted(path.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                entries.append(f"  {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"  {entry.name} ({_human_size(size)})")
    except PermissionError:
        return f"Error: Permission denied: {dirpath}"

    header = f"Directory: {path}\n"
    return header + "\n".join(entries) if entries else header + "  (empty)"


def _human_size(size: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


TOOL_DEFINITION = {
    "name": "file_reader",
    "description": (
        "Read local files or list directory contents. Supports text files, code, "
        "config files, and more. Can read specific line ranges for large files."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "list"],
                "description": "'read' to read a file, 'list' to list a directory",
            },
            "path": {
                "type": "string",
                "description": "Path to the file or directory",
            },
            "start_line": {
                "type": "integer",
                "description": "Start line number (1-indexed, for 'read' action)",
            },
            "end_line": {
                "type": "integer",
                "description": "End line number (inclusive, for 'read' action)",
            },
        },
        "required": ["action", "path"],
    },
}


def handle(input_data: dict) -> str:
    """Handle a tool call from the API."""
    action = input_data["action"]
    path = input_data["path"]

    if action == "read":
        return read_file(path, input_data.get("start_line", 0), input_data.get("end_line", 0))
    elif action == "list":
        return list_directory(path)
    else:
        return f"Error: Unknown action '{action}'"
