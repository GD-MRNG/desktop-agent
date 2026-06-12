# desktop-agent

A working desktop assistant built with the OpenAI Agents SDK, and a reference implementation of every major SDK concept.

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Install browser binaries
uv run playwright install chromium

# 3. Configure API key
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 4. Run
uv run python -m agent.main
```

## Tests

```bash
uv run pytest
```
