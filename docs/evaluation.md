# Evaluation

This page tracks how the desktop-agent performs against its end-to-end test catalogue.

The tests are defined in [`docs/e2e.md`](e2e.md) and cover 18 scenarios across
conversations, file operations, search, shell execution, documentation lookup,
summarisation, and safety guardrails.

## How evaluation works

`agent/evaluate.py` drives the agent programmatically through each test case:

- Each test sends one or more prompts to a live `AgentManager` instance
- Tool calls and responses are captured without printing to the terminal
- `request_approval` is mocked per-test (auto-approve or auto-deny) so shell tests
  run headlessly
- After all runs complete, an LLM judge (gpt-4o-mini) rates each result PASS / PARTIAL / FAIL
  with one sentence of reasoning

Results are written to `docs/evals/evaluation_<date>_<commit>.md`.

## Running an evaluation

```bash
# Requires OPENAI_API_KEY in .env
uv run python agent/evaluate.py
```

The script exits with a non-zero code if any test is rated FAIL by the judge.

## Evaluation runs

| Date | Commit | Pass | Partial | Fail | Report |
|------|--------|------|---------|------|--------|
| 2026-06-13 | f13c336 | 15 | 2 | 0 | [evaluation_2026-06-13_f13c336.md](evals/evaluation_2026-06-13_f13c336.md) |

---

> Evaluation is intentionally lightweight — it measures whether the agent calls the
> right tools and produces coherent responses, not exact string matches. The LLM judge
> provides a qualitative signal that unit tests cannot.
