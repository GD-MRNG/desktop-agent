# readme.md — README Writing Skill

Use this skill when asked to write or update the README for the desktop-agent project.

## Structure

The README always follows this five-section order. Do not add sections or reorder them.

```
# desktop-agent

## Description

## Capabilities

## Setup

## Evaluation
```

---

## Section guidance

### Title

Plain `# desktop-agent`. No tagline, no badge, no subtitle on the same line.

### Description

Two sub-paragraphs:

1. **Purpose (why it was built):** One to two sentences. Name the target user
   (a developer), the core problem (augmenting day-to-day coding work), and the
   approach (scaffold + LLM + tools). Do not use the word "showcase".

2. **Principles (constraints):** One to two sentences naming the binding constraints
   that shaped the design — e.g. explicit human approval for shell commands,
   separation of Brain/Hands/Conductor layers, all tools are async. These are the
   rules the agent plays by, not features.

### Capabilities

Lead with a sentence that sets expectations ("When working well, the agent can...").
Then use subheadings, one per capability group. Each subheading gets 2–4 bullet points.

**Code execution** gets the most detail — expand on:
- What kinds of commands it can run (any shell command)
- How the approval gate works (explicit y/n prompt before each command)
- What the output looks like (stdout/stderr printed, exit code shown)
- That it is OS-aware (PowerShell on Windows, Bash on Unix)

Other capability groups: files, search, clipboard, documentation lookup, summarisation, safety.

Capabilities should read from the user's perspective — what they can accomplish, not
how the internals work. Avoid mentioning `@function_tool`, `Pydantic`, or SDK internals.

### Setup

Three subsections: **Prerequisites**, **Install & configure**, **Usage**.

Prerequisites: uv only (link to docs.astral.sh/uv), OpenAI API key, optional CONTEXT7_API_KEY.
Install & configure: `uv sync`, create `.env`.
Usage: `uv run python -m agent.main`. Include test commands in a separate Tests subsection.

### Evaluation

One short paragraph: what the evaluation measures and where to find results.
Link to `docs/evaluation.md`. Do not summarise individual test results here — that
belongs in the evaluation reports.

---

## Style rules

- No emojis
- No badges or shields
- No internal architecture details (Brain/Hands/Conductor, Pydantic, SDK imports)
- No "coming soon" placeholders — either the feature works or it is not listed
- Capabilities are written for someone evaluating whether to use the tool, not for
  someone already building it
- Avoid passive voice in capability bullets
- Keep the whole file under ~100 lines
