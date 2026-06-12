# pr.md — Pull Request Description Standards

Every PR description must follow this structure. No exceptions.

---

## Template

```
## What
One or two sentences. What does this PR do?
State the change, not the implementation. A non-technical reader should understand it.

## Why
One or two sentences. What problem does this solve, or what requirement does it meet?
Link to the ticket/issue if one exists.

## How (optional)
Only include if the approach is non-obvious or worth flagging for reviewers.
Not a line-by-line walkthrough — just the key decisions or trade-offs made.

## Testing
How was this verified? Unit tests added/updated, manual steps taken, edge cases covered.
If nothing was tested, say so and explain why.

## Notes (optional)
Anything the reviewer should know: follow-up work, known limitations, areas of risk.
```

---

## Rules

- **Title**: imperative mood, under 72 characters. `Add user auth` not `Added user auth` or `This PR adds user auth`.
- **What** comes first — reviewers decide whether to read further based on it.
- No filler phrases: "This PR...", "As part of...", "Simply...", "Just...".
- If a section has nothing meaningful to say, omit it — don't pad it.
- Screenshots or output snippets are welcome in **Testing** for UI or CLI changes.
- A good PR description lets a reviewer understand the change, assess the risk,
and give useful feedback — without needing to ask clarifying questions first.

---