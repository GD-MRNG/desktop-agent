# desktop-agent

A working desktop assistant built with the OpenAI Agents SDK

## Capabilities

### File system
- Read files and list directory contents
- Write and append to files
- Recursive text search across files with line-number results

### Clipboard
- Read from and write to the system clipboard

### Web search
- Search the web via DuckDuckGo for current information

### Shell execution
- Run shell commands (PowerShell on Windows, Bash on Unix)
- Every command requires explicit user approval before it runs

### Summarisation
- Condense text via a nested summary sub-agent

### Safety
- Input guardrail blocks dangerous patterns before the agent reasons
- Human-in-the-loop approval gate for all shell commands

---

> **Demo results** — coming soon

---

## Usage

```bash
# Install dependencies
uv sync

# Run the CLI agent
uv run python -m agent.main
```

## Tests

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_tools.py

# Run a single test by name
uv run pytest tests/test_tools.py::test_read_file_returns_content
```