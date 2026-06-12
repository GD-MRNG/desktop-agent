# testing.md — Unit Testing Standards

Applies to all unit and integration tests in this project.

---

## What to Test

- Test **behaviours**, not implementations. Tests should still pass if you refactor internals
  without changing what the function does.
- Every important behaviour gets a test. "Important" means: if this broke silently, it would cause
  a real problem.
- Test edge cases explicitly: empty inputs, boundary values, error conditions, None.
- Don't test private implementation details — if you have to, the abstraction is probably wrong.

## Test Structure

- One logical assertion per test (a single `assert` or a tightly related group).
  If a test fails, the name alone should tell you what broke.
- Test names describe the scenario: `test_parse_returns_empty_list_for_blank_input`
  not `test_parse_2`.
- Arrange / Act / Assert — keep these three phases clearly separated, even visually.
- No logic in tests (no loops, no conditionals). If you need them, use parametrize.

## Test Doubles

- Use **mocks** only to isolate from external systems (I/O, network, time, randomness).
  Don't mock things just because they're inconvenient to set up.
- Prefer **fakes** (working lightweight implementations) over mocks where possible —
  they test more realistic behaviour.
- Never mock the thing you're testing. Only mock its *dependencies*.
- Assert on mock calls only when the call itself is the behaviour being tested
  (e.g. verifying a notification was sent), not as a shortcut to avoid proper assertions.

## Test Quality

- A failing test must produce a message that tells you *what* failed and *what was expected*.
  Use assertion messages or descriptive variable names.
- Tests must be deterministic: no dependence on time, random seeds, or external state unless
  explicitly controlled.
- Tests that always pass are worse than no tests — they create false confidence.
  Delete or fix flaky tests immediately.

## Levels of Testing

- **Unit tests**: fast, isolated, no I/O. The majority of tests should be here.
- **Integration tests**: test the wiring between components; acceptable to be slower.
- Don't write an integration test for something a unit test can cover — and vice versa.

---

> The purpose of tests is to detect breakages. A test suite that doesn't fail when
> behaviour breaks is not a safety net — it's theatre.