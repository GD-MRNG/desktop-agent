"""Unit tests for Context7 MCP tool functions.

Both tools wrap an external HTTP service via _Context7Transport. Tests mock
_Context7Transport to avoid live network calls, verifying that:
  - the correct MCP methods and arguments are used
  - return types match their Pydantic schemas
  - library ID parsing handles the real response format
"""
from unittest.mock import patch, MagicMock

from tools.context7 import resolve_library_id, fetch_library_docs


def _unwrap(tool):
    """Extract the original async function from a @function_tool wrapper."""
    for cell in tool.on_invoke_tool._invoke_tool_impl.__closure__ or []:
        try:
            val = cell.cell_contents
            if callable(val) and hasattr(val, "__name__") and not isinstance(val, type):
                return val
        except ValueError:
            continue
    raise ValueError(f"Could not extract function from tool '{tool.name}'")


_RESOLVE_RAW = """\
Available Libraries:

- Title: HTTPX
- Context7-compatible library ID: /encode/httpx
- Description: A next generation HTTP client for Python.
- Code Snippets: 208
- Source Reputation: High
- Benchmark Score: 86.9
"""

_DOCS_RAW = """\
### AsyncClient

```python
async with httpx.AsyncClient() as client:
    resp = await client.get("https://example.com")
```
"""


# ── resolve_library_id ────────────────────────────────────────────────────────

async def test_resolve_extracts_library_id():
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = _RESOLVE_RAW
    with patch("tools.context7._Context7Transport", mock_cls):
        result = await _unwrap(resolve_library_id)("python httpx")
    assert result.library_id == "/encode/httpx"
    assert result.raw == _RESOLVE_RAW


async def test_resolve_calls_initialize_then_tool():
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = _RESOLVE_RAW
    with patch("tools.context7._Context7Transport", mock_cls):
        await _unwrap(resolve_library_id)("react")
    mock_cls.return_value.initialize.assert_called_once()
    mock_cls.return_value.call_tool.assert_called_once_with(
        "resolve-library-id",
        {"query": "react", "libraryName": "react"},
    )


async def test_resolve_returns_empty_id_when_no_match():
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = "No libraries found."
    with patch("tools.context7._Context7Transport", mock_cls):
        result = await _unwrap(resolve_library_id)("xyzzy_nonexistent")
    assert result.library_id == ""
    assert result.raw == "No libraries found."


# ── fetch_library_docs ────────────────────────────────────────────────────────

async def test_fetch_docs_returns_content():
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = _DOCS_RAW
    with patch("tools.context7._Context7Transport", mock_cls):
        result = await _unwrap(fetch_library_docs)("/encode/httpx", "async client")
    assert result.content == _DOCS_RAW
    assert result.library_id == "/encode/httpx"
    assert result.query == "async client"


async def test_fetch_docs_calls_query_docs_tool():
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = _DOCS_RAW
    with patch("tools.context7._Context7Transport", mock_cls):
        await _unwrap(fetch_library_docs)("/encode/httpx", "streaming")
    mock_cls.return_value.initialize.assert_called_once()
    mock_cls.return_value.call_tool.assert_called_once_with(
        "query-docs",
        {"libraryId": "/encode/httpx", "query": "streaming"},
    )


async def test_fetch_docs_new_transport_per_call():
    # Each tool call must create a fresh transport instance (new session).
    mock_cls = MagicMock()
    mock_cls.return_value.call_tool.return_value = _DOCS_RAW
    with patch("tools.context7._Context7Transport", mock_cls):
        await _unwrap(fetch_library_docs)("/encode/httpx", "first call")
        await _unwrap(fetch_library_docs)("/encode/httpx", "second call")
    assert mock_cls.call_count == 2
