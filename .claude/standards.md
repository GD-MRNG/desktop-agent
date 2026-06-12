# standards.md — Project Coding Standards

These principles apply to all code in this project.
They are drawn from *Good Code, Bad Code* (Tom Long) and exist to keep the codebase
readable, safe to change, and hard to misuse.

---

## Abstraction

- Each function or class solves **one problem at a time** at a single level of abstraction.
  Don't mix high-level orchestration with low-level implementation in the same function.
- Keep functions small enough to understand in one read.
  If you need to scroll to understand it, split it.
- Hide implementation details behind clear boundaries.
  Callers should not need to know *how*, only *what*.

## Code Contracts

- Function signatures are the contract. Parameter names, types, and return types
  must make correct usage obvious without reading the body.
- Minimise "small print": avoid hidden preconditions, silent failures, or magic defaults
  that callers must know about to use the code correctly.
- Enforce contracts defensively at boundaries (validate inputs, assert invariants)
  so misuse fails loudly rather than silently corrupting state.

## Error Handling

- **Fail fast**: surface errors at the point they occur, not silently later.
- Distinguish recoverable errors (return/raise explicitly) from programming errors (assert/crash).
- Never swallow exceptions without a documented reason.
- Error messages must say *what went wrong* and *where*, not just that something failed.

## Readability

- Name things after what they *are or do*, not how they work internally.
- Avoid deep nesting — flatten with early returns or extracted functions.
- No large anonymous functions or clever one-liners that sacrifice clarity for brevity.
- Constants get named; magic numbers do not exist in this codebase.

## Avoiding Surprises

- Functions do exactly what their name says — nothing more, nothing hidden.
- Avoid unexpected side effects in functions that appear to be pure queries.
- Return types are consistent; no functions that return a value *or* None depending on mood.

## Hard to Misuse

- Prefer immutable data where mutation is not required.
- Single source of truth: no duplicated state that can drift out of sync.
- Avoid overly general types (e.g. `dict` or `Any`) when a specific type communicates intent.

---

> When in doubt: would a competent engineer reading this for the first time
> understand it correctly without asking you a question? If no, revise.