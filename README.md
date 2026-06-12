# desktop-agent

A working desktop assistant built with the OpenAI Agents SDK

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