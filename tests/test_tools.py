"""Async unit tests for all tool functions.

The @function_tool decorator wraps each function in a FunctionTool object (for SDK use).
Tests call the original async functions directly via _unwrap(), which extracts them from
the FunctionTool closure. This lets us test logic without SDK invocation overhead or an
active RunContext.
"""
import os
from unittest.mock import patch
import pytest

from tools.read import read_file, list_directory, read_clipboard
from tools.write import write_file, append_file, write_clipboard
from tools.search import search_files
from tools.execute import run_command


def _unwrap(tool):
    """Extract the original async function from a @function_tool wrapper.

    The SDK stores the original callable in the _on_invoke_tool_impl closure.
    This is used in tests so we can call tool logic directly without a RunContext.
    """
    for cell in tool.on_invoke_tool._invoke_tool_impl.__closure__ or []:
        try:
            val = cell.cell_contents
            if callable(val) and hasattr(val, "__name__") and not isinstance(val, type):
                return val
        except ValueError:
            continue
    raise ValueError(f"Could not extract function from tool '{tool.name}'")


# ── read tools ──────────────────────────────────────────────────────────────

async def test_read_file_returns_content(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("line one\nline two\nline three")
    result = await _unwrap(read_file)(str(f))
    assert result.content == "line one\nline two\nline three"
    assert result.line_count == 3
    assert result.path == str(f)


async def test_list_directory_returns_entries(tmp_path):
    (tmp_path / "a.txt").write_text("")
    (tmp_path / "b.py").write_text("")
    result = await _unwrap(list_directory)(str(tmp_path))
    assert "a.txt" in result.entries
    assert "b.py" in result.entries
    assert result.count == 2


async def test_read_clipboard_returns_content():
    with patch("pyperclip.paste", return_value="clipboard text"):
        result = await _unwrap(read_clipboard)()
    assert result.content == "clipboard text"


# ── write tools ─────────────────────────────────────────────────────────────

async def test_write_file_creates_file(tmp_path):
    path = str(tmp_path / "out.txt")
    result = await _unwrap(write_file)(path, "hello world")
    assert result.success is True
    assert os.path.exists(path)
    assert open(path).read() == "hello world"


async def test_write_file_overwrites_existing(tmp_path):
    path = str(tmp_path / "out.txt")
    await _unwrap(write_file)(path, "original")
    await _unwrap(write_file)(path, "overwritten")
    assert open(path).read() == "overwritten"


async def test_append_file_adds_content(tmp_path):
    path = str(tmp_path / "log.txt")
    await _unwrap(write_file)(path, "first\n")
    result = await _unwrap(append_file)(path, "second\n")
    assert result.success is True
    assert open(path).read() == "first\nsecond\n"


async def test_write_clipboard_copies_text():
    with patch("pyperclip.copy") as mock_copy:
        result = await _unwrap(write_clipboard)("hello clipboard")
    mock_copy.assert_called_once_with("hello clipboard")
    assert result.success is True


# ── search tools ─────────────────────────────────────────────────────────────

async def test_search_files_finds_match(tmp_path):
    (tmp_path / "notes.txt").write_text("TODO: fix the thing\nother line")
    result = await _unwrap(search_files)(str(tmp_path), "TODO")
    assert result.total >= 1
    assert any("TODO" in m.line_content for m in result.matches)
    assert result.query == "TODO"


async def test_search_files_no_match(tmp_path):
    (tmp_path / "empty.txt").write_text("nothing here")
    result = await _unwrap(search_files)(str(tmp_path), "XYZZY_NOT_FOUND")
    assert result.total == 0
    assert result.matches == []


async def test_search_files_returns_line_numbers(tmp_path):
    (tmp_path / "code.py").write_text("# line 1\n# TODO at line 2\n# line 3")
    result = await _unwrap(search_files)(str(tmp_path), "TODO")
    assert result.matches[0].line_number == 2


# ── execute tool ─────────────────────────────────────────────────────────────

async def test_run_command_denied_by_user():
    # Patch the name as bound in execute.py, not the definition in approvals.py
    with patch("tools.execute.request_approval", return_value=False):
        result = await _unwrap(run_command)("echo hello")
    assert result.exit_code == 1
    assert "denied" in result.stderr.lower()


async def test_run_command_approved_executes():
    with patch("tools.execute.request_approval", return_value=True):
        result = await _unwrap(run_command)("echo hello")
    assert result.exit_code == 0
    assert "hello" in result.stdout
