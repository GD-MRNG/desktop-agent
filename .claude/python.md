# python.md — Python Coding Standards

Python-specific practices. Read alongside CLAUDE.md, which takes precedence on general principles.

---

## Types

- Use type hints on all function signatures. `def foo(x: int) -> str:` not `def foo(x):`.
- Prefer specific types over `Any`, `dict`, or `list` without parameters.
- Use `TypedDict`, `dataclass`, or `@dataclass(frozen=True)` for structured data
  instead of raw dicts — this makes the contract explicit and enables static checking.
- `Optional[X]` (or `X | None`) must be handled explicitly by callers; document why None is valid.

## Error Signaling

- Use **exceptions** for errors the caller must handle; don't return `None` or `-1` as a sentinel.
- Create specific exception subclasses for domain errors rather than raising bare `Exception`.
- Use `logging` not `print` for runtime diagnostics; never leave debug prints in committed code.
- Context managers (`with`) for all resources (files, connections, locks) — no bare open/close pairs.

## Modularity

- Favour **composition over inheritance**. If a class hierarchy goes more than 2 levels deep, question it.
- Use dependency injection: pass dependencies as constructor arguments rather than importing globals
  or instantiating them inside functions. This makes testing and swapping implementations trivial.
- Keep modules focused. If a file is doing two unrelated things, split it.

## Immutability & State

- Default to immutable: use `tuple` over `list`, `frozenset` over `set`, `frozen=True` dataclasses
  when the data shouldn't change after creation.
- Avoid module-level mutable state. Global variables that change at runtime cause hard-to-trace bugs.
- Functions should not mutate arguments unless that is their explicit, named purpose (e.g. `sort_inplace`).

## Reusability

- Extract repeated logic into well-named helpers rather than copy-pasting with minor variations.
- Avoid hardcoded values — use constants, config, or parameters so behaviour can change without
  editing internals.
- Write functions that do one thing well at a general enough level that they can be reused,
  but not so general that they become confusing.

---

> Python idioms are fine; cleverness is not. Use list comprehensions where they read naturally.
> Use a regular loop when the comprehension would need a comment to explain.