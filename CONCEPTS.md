# CONCEPTS.md — OpenAI Agents SDK Reference

> This file maps every key concept in the OpenAI Agents SDK to the exact file and
> function in this project where it is demonstrated. Read this alongside the code.
>
> Each entry follows the same structure:
> - **What it is** — the plain-English definition
> - **Why it matters** — the engineering reason it exists
> - **Where it lives** — the file(s) in this project
> - **The gotcha** — the most common mistake learners make
> - **The mental model** — a one-line analogy to lock it in

---

## Table of Contents

1. [The Agent Reasoning Loop](#1-the-agent-reasoning-loop)
2. [async / await and the Event Loop](#2-async--await-and-the-event-loop)
3. [asyncio.gather() — True Concurrency](#3-asynciogather--true-concurrency)
4. [@function_tool — The Docstring is the Prompt](#4-function_tool--the-docstring-is-the-prompt)
5. [Pydantic Structured Outputs](#5-pydantic-structured-outputs)
6. [Runner — The Execution Orchestrator](#6-runner--the-execution-orchestrator)
7. [Trace — Observability](#7-trace--observability)
8. [Tool Chaining](#8-tool-chaining)
9. [Human-in-the-Loop](#9-human-in-the-loop)
10. [@input_guardrail — The Tripwire](#10-input_guardrail--the-tripwire)
11. [max_turns — The Circuit Breaker](#11-max_turns--the-circuit-breaker)
12. [Handoff — State Transfer Between Agents](#12-handoff--state-transfer-between-agents)
13. [agent.as_tool() — Agent as a Callable](#13-agentastool--agent-as-a-callable)
14. [Handoff vs agent.as_tool() — Choosing the Right Pattern](#14-handoff-vs-agentastool--choosing-the-right-pattern)
15. [Chain of Thought Prompting](#15-chain-of-thought-prompting)
16. [Vision / Multimodal Tools](#16-vision--multimodal-tools)
17. [Generator Streaming — The yield Pattern](#17-generator-streaming--the-yield-pattern)
18. [Brain / Hands / Conductor — The Architecture Pattern](#18-brain--hands--conductor--the-architecture-pattern)
19. [Cost Awareness in Agentic Loops](#19-cost-awareness-in-agentic-loops)

---

## 1. The Agent Reasoning Loop

**What it is:**
An agent is not a chatbot. It is a *reasoning loop* — a cycle of observe → plan → act →
observe again. On each turn the model reads the conversation history, decides whether to
call a tool or respond, executes the tool if needed, reads the result, and loops until
it has a final answer.

**Why it matters:**
Understanding the loop is what separates "I used an LLM" from "I built an agent." Every
other concept in this file is either a part of this loop or a mechanism that controls it.

**Where it lives:**
```
agent/manager.py     — starts and drives the loop via Runner
agent/trace.py       — makes each step of the loop visible
app_agents/desktop_agent.py  — defines what the loop has access to
```

**The loop in pseudocode:**
```
while not done and turns < max_turns:
    response = model(conversation_history + tools)
    if response.wants_tool:
        result = await call_tool(response.tool_name, response.tool_args)
        conversation_history.append(tool_result)
    else:
        final_answer = response.text
        done = True
```

**The gotcha:**
The loop is stateless between `Runner.run()` calls. The model has no memory across
separate invocations — you must pass the full conversation history each time.

**Mental model:** The agent is a chef who reads a recipe (system prompt), checks the
fridge (tools), decides what to do next, acts, then re-reads the recipe to decide the
next step — until the dish is done.

---

## 2. async / await and the Event Loop

**What it is:**
`async def` marks a function as a *coroutine* — code that can pause at a defined point
and let other work happen while it waits. `await` is the pause point. Python's `asyncio`
event loop manages a queue of coroutines, switching between them whenever one hits an
`await`.

**Why it matters:**
LLM API calls are high-latency network operations. Without async, your program sits idle
waiting for each response. With async, the event loop can handle other work — tool calls,
UI updates, other agent turns — while waiting. This is the foundational pattern of
non-blocking agentic systems.

**Where it lives:**
```
All files in tools/    — every tool is async def
agent/manager.py       — the top-level loop is async
agent/main.py          — entry point uses asyncio.run()
```

**Minimal pattern:**
```python
import asyncio
from agents import Agent, Runner

agent = Agent(name="Demo", instructions="Be helpful.")

async def main():
    result = await Runner.run(agent, "Hello!")
    print(result.final_output)

asyncio.run(main())   # starts the event loop
```

**The gotcha — this will burn you:**
```python
# ❌ WRONG — this does NOT call the function
result = my_async_tool("some input")
print(result)  # prints: <coroutine object my_async_tool at 0x...>

# ✅ CORRECT
result = await my_async_tool("some input")
print(result)  # prints the actual data
```
Calling an `async` function without `await` returns a coroutine object, not data. Your
program appears to do nothing. Always `await` async calls.

**I/O-bound vs CPU-bound:**
Use `asyncio` for I/O-bound work (API calls, file reads, network requests) — anything
where your code spends time *waiting*. For CPU-bound work (number crunching, model
training, data processing) use `multiprocessing` instead — async won't help there because
the CPU never gets to pause.

**Mental model:** Async is a chef who puts a pot on to boil, then starts chopping
vegetables while waiting, instead of staring at the pot.

---

## 3. asyncio.gather() — True Concurrency

**What it is:**
`asyncio.gather(*coroutines)` schedules multiple coroutines on the event loop
*simultaneously*. They all start immediately and the loop switches between them as each
hits an `await`. The overall wait time is roughly the duration of the *slowest* task,
not the *sum* of all tasks.

**Why it matters:**
Sequential `await` in a loop runs tasks one-by-one — if each takes 1 second and you have
5, you wait 5 seconds. `asyncio.gather()` runs them in parallel — you wait ~1 second.
For agents making multiple API calls or tool invocations this difference is significant
in both latency and user experience.

**Where it lives:**
```
tools/search.py    — search_files and web_search gathered in parallel
```

**The contrast:**
```python
# ❌ Sequential — waits 3 seconds total (1s + 1s + 1s)
result_a = await search_files(directory, query)
result_b = await web_search(query)
result_c = await read_file(path)

# ✅ Concurrent — waits ~1 second total (all run simultaneously)
result_a, result_b, result_c = await asyncio.gather(
    search_files(directory, query),
    web_search(query),
    read_file(path),
)
```

**When to use gather vs sequential await:**
Use `gather()` when results are *independent* — neither depends on the other.
Use sequential `await` when B depends on the output of A (tool chaining).

**The gotcha:**
`gather()` raises an exception if *any* task fails, by default cancelling the others.
Use `return_exceptions=True` if you want all tasks to complete regardless:
```python
results = await asyncio.gather(*tasks, return_exceptions=True)
# results may contain exception objects — check before using
```

**Cost warning:**
Parallel tool calls that hit paid APIs (web search, LLM calls) all fire simultaneously.
10 parallel web searches cost the same as 10 sequential ones — you just pay it all at
once. Always be intentional about when you use `gather()`.

**Mental model:** Sequential await is a single checkout lane. `gather()` opens all
lanes at once — throughput is the same, but wait time drops to the slowest lane.

---

## 4. @function_tool — The Docstring is the Prompt

**What it is:**
`@function_tool` is a decorator from the OpenAI Agents SDK that wraps a Python function
and automatically generates the JSON schema the model uses to decide when and how to call
it. The schema is built from three things: the function name, its type-annotated
parameters, and its docstring.

**Why it matters:**
The model never sees your Python code. It only sees the name, parameters, and the
docstring. The docstring is literally the prompt the model uses to decide whether to call
this tool. A vague docstring means unreliable tool selection.

**Where it lives:**
```
Every file in tools/   — all tools use @function_tool
```

**Minimal pattern:**
```python
from agents import function_tool
from schemas.models import FileContent

@function_tool
async def read_file(path: str) -> FileContent:
    """
    Read the full text content of a file at the given path.
    Use this when the user asks to read, view, or inspect a file.
    Returns the content and metadata. Fails if the file does not exist.
    """
    # implementation here
```

**What the model actually receives:**
```json
{
  "name": "read_file",
  "description": "Read the full text content of a file at the given path...",
  "parameters": {
    "type": "object",
    "properties": {
      "path": { "type": "string" }
    },
    "required": ["path"]
  }
}
```

**The gotcha:**
Treat the docstring as production logic. Changing it changes the model's behaviour.
If you write "use this to read files", the model will use it broadly. If you write
"use this ONLY for text files under 1MB", the model will respect that constraint.
Good docstrings = reliable tool selection.

**Mental model:** The `@function_tool` decorator is like publishing a job posting.
The function signature defines the requirements; the docstring is the job description
the model reads when deciding who to hire for the task.

---

## 5. Pydantic Structured Outputs

**What it is:**
Instead of returning raw strings or dicts from tools, we return typed `BaseModel`
subclasses from Pydantic. This enforces a strict schema on the data flowing through
the agent — the model's output must match the defined shape or an error is raised.

**Why it matters:**
LLMs are stochastic. Without schema enforcement, a tool might return `{"content": "..."}` 
one time and `{"text": "..."}` the next, silently breaking downstream code. Pydantic turns
"I hope the shape is right" into "the shape is guaranteed or it fails loudly."

**Where it lives:**
```
schemas/models.py      — all Pydantic models defined here
Every file in tools/   — tools return these models as their output type
```

**Example:**
```python
# schemas/models.py
from pydantic import BaseModel

class FileContent(BaseModel):
    content: str
    path: str
    line_count: int

class SearchMatch(BaseModel):
    file: str
    line_number: int
    line_content: str

class SearchResults(BaseModel):
    matches: list[SearchMatch]
    total: int
    query: str
```

**The gotcha:**
Over-constraining can cause failures. If you require a field the model can't reliably
produce, it will either hallucinate a value or the validation will fail. Keep schemas
focused on what you genuinely need downstream.

**Mental model:** Pydantic is a customs officer. Every package (tool return) must match
the declared manifest (schema) exactly. Anything that doesn't match is rejected at the
border, not silently accepted and discovered broken later.

---

## 6. Runner — The Execution Orchestrator

**What it is:**
`Runner` is the SDK class that drives the agent reasoning loop. You call `Runner.run(agent,
input)` and it handles the back-and-forth between the model and tools, managing the
conversation state internally until the agent produces a final response.

**Why it matters:**
Without `Runner`, you would write hundreds of lines of JSON-parsing, tool-dispatching,
and loop-management boilerplate. `Runner` encapsulates all of that — it is the "engine"
that powers the observe → plan → act cycle.

**Where it lives:**
```
agent/manager.py    — all Runner.run() calls go through here
```

**Minimal pattern:**
```python
from agents import Runner

result = await Runner.run(desktop_agent, user_input)
print(result.final_output)
```

**The gotcha:**
`Runner` ties execution to the SDK's specific opinion about state and handoffs. If you
need behaviour the SDK doesn't support, you may need to manage the loop manually with
raw API calls. For this project, `Runner` covers everything we need.

**Mental model:** `Runner` is the stage manager. You set up the actors (agents) and
the props (tools). The stage manager calls them at the right moment, handles the
transitions, and tells you when the show is over.

---

## 7. Trace — Observability

**What it is:**
`Trace` is a context manager from the SDK that groups all async events from a single
logical session — tool calls, model responses, sub-agent calls — into one named trace.
This makes it possible to see the full timeline of what happened in a given agent turn.

**Why it matters:**
Multi-agent systems with async tool calls are nearly impossible to debug without
observability. Without a trace, you have a stream of disconnected events with no context
about which turn they belong to, who called whom, or what the payloads were. The trace is
the primary debugging tool for agentic systems.

**Where it lives:**
```
agent/trace.py     — wraps the SDK Trace with rich CLI formatting
agent/manager.py   — every Runner.run() call is wrapped in a Trace
```

**Minimal pattern:**
```python
from agents import trace

with trace("user-turn-001"):
    result = await Runner.run(agent, user_input)
```

**What it produces in this project:**
```
─────────────────────────────────────────────
[TURN] user-turn-001
[AGENT] Thinking...
[REASON] I need to search the files first, then read the matches.
[TOOL →] search_files(directory="./src", query="TODO")
[TOOL ←] 3 matches found
[TOOL →] read_file(path="./src/main.py")
[TOOL ←] 142 lines read
[AGENT] Composing final response...
[RESPONSE] Found 3 TODOs across 2 files...
─────────────────────────────────────────────
```

**The gotcha:**
`Trace` adds slight overhead and is most useful with an external dashboard (the SDK
supports OpenAI's tracing UI). For this project we use it primarily for CLI output — the
educational value of *seeing* the loop is more important than the dashboard integration.

**Mental model:** `Trace` is the flight data recorder. You hope you never need it to
debug a crash — but when something goes wrong, it's the only record of exactly what
happened and in what order.

---

## 8. Tool Chaining

**What it is:**
Tool chaining is when the agent uses the output of one tool as the input to the next —
not because you programmed it to, but because the model's reasoning leads it there.
The agent calls tool A, reads the result, decides it needs more information, and calls
tool B with data from A's output.

**Why it matters:**
This is emergent reasoning — the agent solving a multi-step problem autonomously. It
demonstrates that the agent is not just calling functions; it is thinking about *which*
functions to call and in *what order* based on what it observes.

**Where it lives:**
```
tools/search.py    — search_files returns file paths
tools/read.py      — read_file is then called on those paths
```

**What it looks like in the trace:**
```
[TOOL →] search_files(directory="./src", query="TODO")
[TOOL ←] [{file: "main.py", line: 42, content: "# TODO: handle errors"}]
[TOOL →] read_file(path="./src/main.py")   ← agent decided to do this
[TOOL ←] <full file content>
[RESPONSE] Found 1 TODO in main.py at line 42...
```

**The gotcha:**
The agent decides whether to chain — you cannot force it. You can encourage chaining via
the system prompt ("after searching, always read the matching files before responding")
but ultimately the model reasons about it. Clear, descriptive tool docstrings are the
best way to guide this behaviour.

**Mental model:** Tool chaining is the agent following a thread — pulling on one piece
of information leads it to pull on another, until it has enough to answer.

---

## 9. Human-in-the-Loop

**What it is:**
A deliberate pause in the agent's execution where a human must approve an action before
it proceeds. This is application-level safety logic — the agent has decided to call a
tool, but the tool itself holds until a human confirms.

**Why it matters:**
Some actions are irreversible. Running a shell command, deleting a file, or sending an
email cannot be undone. Requiring human approval before high-risk actions is a core safety
pattern for any agent operating in the real world.

**Where it lives:**
```
tools/execute.py    — run_command pauses for approval
agent/approvals.py  — approval prompt and response parsing
```

**Pattern:**
```python
@function_tool
async def run_command(command: str, working_dir: str = ".") -> CommandResult:
    """Run a shell command. Always requires user confirmation first."""
    # [CONCEPT] Human-in-the-loop: pause before any side effect
    approved = await request_approval(
        action=f"Run command: `{command}`",
        working_dir=working_dir
    )
    if not approved:
        return CommandResult(stdout="", stderr="Cancelled by user.", exit_code=-1)
    # proceed with execution
```

**The difference from the guardrail:**
The `@input_guardrail` (see concept 10) fires *before the agent processes the message*.
The human-in-the-loop fires *after the agent decides to act*. They are two distinct safety
layers at different points in the loop.

```
User input → [@input_guardrail] → Agent reasoning → Tool call → [Human approval] → Execution
```

**The gotcha:**
Don't overuse approval gates — they destroy the agent's usefulness if every action
requires confirmation. Reserve them for actions that are irreversible, destructive, or
externally visible (commands, emails, file deletions, API writes).

**Mental model:** The human-in-the-loop is a surgeon's checklist. The agent is ready
to operate — but someone must say "proceed" before the first incision.

---

## 10. @input_guardrail — The Tripwire

**What it is:**
`@input_guardrail` is an SDK decorator that creates a middleware function which runs
*before* the agent processes any user input. It evaluates the message against a set of
rules and can trigger a "tripwire" — halting the request entirely before the agent ever
sees it.

**Why it matters:**
Some inputs should never reach the agent at all. A guardrail that intercepts `rm -rf /` 
before the agent can reason about whether to run it is safer than hoping the agent's
reasoning rejects it. Guardrails separate *intent detection* (is this input dangerous?)
from *task execution* (should I do this task?).

**Where it lives:**
```
agent/guardrails.py    — @input_guardrail definition
app_agents/desktop_agent.py — guardrail registered on DesktopAgent
```

**Pattern:**
```python
from agents import input_guardrail, GuardrailFunctionOutput, RunContextWrapper
from agents import Agent
from schemas.models import SafetyCheck

# A fast, cheap model evaluates safety — not the main agent
guard_agent = Agent(
    name="SafetyChecker",
    instructions="Check if the user's request involves destructive system commands.",
    output_type=SafetyCheck,   # SafetyCheck: { is_safe: bool, reason: str }
    model="gpt-4o-mini",       # cheap model for fast checks
)

@input_guardrail
async def safety_check(
    context: RunContextWrapper, agent: Agent, input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(guard_agent, input)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_safe,
    )
```

**The difference from human-in-the-loop:**
| | @input_guardrail | Human-in-the-loop |
|---|---|---|
| When it fires | Before agent sees input | After agent decides to act |
| Who decides | Another LLM (or rules) | A human |
| What it blocks | Dangerous *requests* | Dangerous *actions* |
| User sees | Rejection message | Approval prompt |

**The gotcha:**
Guardrails add latency (an extra LLM call) and cost. Use a fast, cheap model (`gpt-4o-mini`)
for the check, not your main model. For simple cases, a regex or keyword check is faster
and cheaper than an LLM guardrail.

**Mental model:** The guardrail is a bouncer at the door. The human-in-the-loop is the
manager you ask before doing something expensive. The bouncer acts first.

---

## 11. max_turns — The Circuit Breaker

**What it is:**
`max_turns` is a parameter on the agent (or `Runner.run()`) that limits how many
reasoning steps the agent can take before the SDK forcibly stops it and returns whatever
it has so far.

**Why it matters:**
An agent that is "unsatisfied" with a tool result will retry — potentially forever. This
is called an agentic loop. Without a hard stop, a runaway agent can exhaust your API
budget in seconds or run indefinitely. `max_turns` is the circuit breaker that prevents
this.

**Where it lives:**
```
app_agents/desktop_agent.py   — max_turns=15
app_agents/browser_agent.py   — max_turns=10
app_agents/summary_agent.py   — max_turns=3
```

**Pattern:**
```python
desktop_agent = Agent(
    name="DesktopAgent",
    instructions="...",
    tools=[...],
    max_turns=15,   # [CONCEPT] circuit breaker — never let the loop run forever
)
```

**Choosing the right limit:**
- Complex tasks (desktop agent): 10–20 turns
- Focused sub-tasks (browser, summary): 3–10 turns
- Simple single-purpose agents: 2–5 turns

**The gotcha:**
When `max_turns` is hit, the SDK returns a partial result — not an error. Always check
`result.stopped_reason` to know whether the agent finished naturally or was cut off:
```python
result = await Runner.run(agent, input)
if result.stopped_reason == "max_turns":
    print("Warning: agent hit turn limit — response may be incomplete")
```

**Mental model:** `max_turns` is the taxi meter limit you set before getting in. The
driver (agent) can take as many turns as needed to get you there — but the meter stops
at your limit whether you've arrived or not.

---

## 12. Handoff — State Transfer Between Agents

**What it is:**
A handoff is a control flow pattern where one agent transfers the *entire conversation
state and responsibility* to another agent. The original agent exits the flow — it does
not receive the result. The new agent takes over as if it had been the agent all along.

**Why it matters:**
Some tasks require a fundamentally different capability set. When the desktop agent needs
to control a browser, it shouldn't try to use browser tools itself — it should hand the
task to a specialised browser agent and step aside. Handoffs enable clean separation of
concerns between agents with different roles.

**Where it lives:**
```
app_agents/desktop_agent.py    — defines the handoff to BrowserAgent
app_agents/browser_agent.py    — the handoff target
```

**Pattern:**
```python
from agents import Agent, handoff

browser_agent = Agent(
    name="BrowserAgent",
    instructions="You control a web browser. Use screenshot and click to navigate.",
    tools=[open_browser, screenshot, click, type_text],
    max_turns=10,
)

desktop_agent = Agent(
    name="DesktopAgent",
    instructions="...",
    tools=[read_file, write_file, search_files, run_command],
    handoffs=[handoff(browser_agent)],  # [CONCEPT] handoff registration
)
```

**What happens during a handoff:**
```
1. DesktopAgent decides a browser task is needed
2. SDK transfers full conversation history to BrowserAgent
3. BrowserAgent executes its vision loop (screenshot → click → type)
4. BrowserAgent returns its final response
5. DesktopAgent is NOT resumed — the handoff is terminal for that turn
```

**The gotcha:**
The original agent loses visibility after the handoff. If you need the result back in the
parent agent's reasoning, use `agent.as_tool()` instead (see concept 13). Use handoffs
for distinct *phase shifts* — not for sub-tasks where you need the output.

**Mental model:** A handoff is like a relay race baton pass — once the baton leaves your
hand, you're done. The next runner takes full responsibility and you don't get a summary
of how they did.

---

## 13. agent.as_tool() — Agent as a Callable

**What it is:**
`agent.as_tool()` wraps an entire agent as a callable tool on a parent agent. The parent
agent *calls* the sub-agent like any other tool, receives the result, and continues its
own reasoning with that result in context.

**Why it matters:**
Sometimes you need a specialised agent's capability but still want the parent to use the
result. `SummaryAgent` is a good example — the desktop agent needs a summary, calls the
summary agent, gets the summary back, and uses it in its final response. The parent
remains in control throughout.

**Where it lives:**
```
app_agents/summary_agent.py     — the agent being wrapped as a tool
app_agents/desktop_agent.py     — registers SummaryAgent via .as_tool()
```

**Pattern:**
```python
summary_agent = Agent(
    name="SummaryAgent",
    instructions="Summarise the provided text concisely in 3–5 sentences.",
    max_turns=3,
)

desktop_agent = Agent(
    name="DesktopAgent",
    tools=[
        read_file,
        write_file,
        search_files,
        run_command,
        summary_agent.as_tool(  # [CONCEPT] agent-as-tool registration
            tool_name="summarise_text",
            tool_description="Summarise a block of text. Pass the text as input.",
        ),
    ],
    handoffs=[handoff(browser_agent)],
)
```

**What happens during an agent.as_tool() call:**
```
1. DesktopAgent decides to summarise some text
2. SDK calls SummaryAgent with the text as input
3. SummaryAgent runs its own reasoning loop (up to max_turns=3)
4. SummaryAgent returns its final output
5. DesktopAgent receives the summary as a tool result ← KEY DIFFERENCE from handoff
6. DesktopAgent continues its own reasoning with the summary
```

**The gotcha:**
Each `as_tool()` call adds latency — you're running a nested LLM call. Don't wrap every
agent as a tool. Reserve this pattern for well-defined, bounded sub-tasks where you
genuinely need the result back.

**Mental model:** `agent.as_tool()` is like calling a specialist on the phone — you ask
the question, wait for the answer, hang up, and continue your own work with the answer
in hand. A handoff is like transferring the call entirely — you're out of the loop.

---

## 14. Handoff vs agent.as_tool() — Choosing the Right Pattern

**The core question:** Do you need the result back in the parent agent's reasoning?

| | Handoff | agent.as_tool() |
|---|---|---|
| Parent gets result? | ❌ No — parent exits | ✅ Yes — result returned as tool output |
| Context after call | Parent is done | Parent continues with result |
| Best for | Distinct phase shifts | Bounded sub-tasks with output |
| Token cost | Lower (parent context ends) | Higher (nested LLM call + result) |
| Example in this project | Desktop → Browser (navigate the web) | Desktop → Summary (summarise text) |
| SDK analogy | `goto` / process transfer | Function call |

**Decision rule:**
- Is this a *new phase* of the task where the original agent's role is complete? → **Handoff**
- Is this a *sub-task* where you need the output to continue? → **agent.as_tool()**

**From the lecture notes:**
> "Use Tools for sub-tasks requiring verification; use Handoffs for distinct phase shifts
> in a workflow."

---

## 15. Chain of Thought Prompting

**What it is:**
Instructing the model to *state its reasoning* before taking action. In this project, the
`DesktopAgent` system prompt explicitly requires the model to explain what it is about to
do and why before calling any tool.

**Why it matters:**
LLMs are next-token predictors. By generating reasoning tokens first, the model
statistically constrains itself to produce actions that are *consistent with that
reasoning*. This significantly improves reliability on multi-step tasks — the model
can't reason one way and act another.

**Where it lives:**
```
app_agents/desktop_agent.py    — system prompt includes CoT instruction
agent/trace.py             — [REASON] lines in the trace output
```

**System prompt excerpt:**
```
Before calling any tool, briefly state what you are about to do and why.
Format: "I will [action] because [reason]."
This makes your reasoning visible and helps the user understand your process.
```

**What it produces in the trace:**
```
[REASON] I will search the files for TODO comments because the user asked
         for a summary of outstanding tasks in the codebase.
[TOOL →] search_files(directory="./src", query="TODO")
```

**The gotcha:**
CoT adds tokens to every response — more cost, more latency. For simple, single-step
tasks it's overkill. Reserve explicit CoT instructions for agents making multi-step
decisions where reliability matters more than speed.

**Mental model:** CoT is requiring a surgeon to say "I'm making a 5cm incision on the
left side" out loud before cutting. It forces deliberate action and creates a record
that can be checked.

---

## 16. Vision / Multimodal Tools

**What it is:**
GPT-4o can process images as input. In the browser agent, we take a screenshot of the
current browser state and pass it to the model as a multimodal message. The model
"sees" the page and decides what to click or type next.

**Why it matters:**
Vision enables the agent to interact with interfaces that have no API — any web page,
any desktop UI. It's how an agent navigates the real world visually rather than
programmatically.

**Where it lives:**
```
tools/browser.py         — screenshot() returns base64 image
app_agents/browser_agent.py  — vision loop: screenshot → model → action → repeat
```

**Vision loop pattern:**
```python
# [CONCEPT] Vision loop — the agent sees the page, decides, acts, sees again
async def vision_step(page) -> str:
    img = await screenshot()           # capture current state
    response = await model.run(
        input=[
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img.image_base64}"}},
            {"type": "text", "text": "What do you see? What should you click or type next?"}
        ]
    )
    return response.final_output
```

**The gotcha:**
Vision is high-latency and expensive per call (images consume many tokens). Each
screenshot → model → action cycle takes 2–5 seconds. The `max_turns=10` on
`BrowserAgent` is especially important here — a runaway vision loop is slow and costly.

**Mental model:** Vision is giving the agent eyes. Instead of reading a structured API
response, it looks at the screen the same way a human would — and decides what to do
based on what it sees.

---

## 17. Generator Streaming — The yield Pattern

**What it is:**
Instead of a function that blocks until it returns a single final result, a Python
generator uses `yield` to emit incremental updates as they become available. The caller
receives a stream of partial states in real time rather than waiting for completion.

**Why it matters:**
Agent tasks can take 10–30 seconds. Without streaming, the user sees a blank screen until
the agent finishes — a terrible experience that also destroys trust ("is it doing
anything?"). With streaming, the user sees tool calls, reasoning steps, and partial
results as they happen. This is the professional standard for agentic UIs.

**Where it lives:**
```
agent/manager.py     — yields state updates as the loop progresses (Phase 3)
ui/app.py            — Flask SSE endpoint consumes the generator
ui/static/main.js    — frontend handles incremental updates
```

**Pattern:**
```python
# manager.py — generator-based streaming
async def run_streaming(user_input: str):
    yield {"type": "status", "text": "Thinking..."}

    async for event in Runner.run_streamed(agent, user_input):
        if event.type == "tool_call":
            yield {"type": "tool_call", "name": event.tool_name, "args": event.args}
        elif event.type == "tool_result":
            yield {"type": "tool_result", "name": event.tool_name, "result": event.result}
        elif event.type == "text_delta":
            yield {"type": "delta", "text": event.delta}

    yield {"type": "done"}
```

**The gotcha:**
The UI must be designed to handle *partial and accumulating data* — not just a final
payload. A frontend that waits for a complete JSON response will not work with a streaming
endpoint. Use Server-Sent Events (SSE) or WebSockets, not regular HTTP.

**Mental model:** The difference between streaming and blocking is the difference between
watching a live sports broadcast and watching a highlight reel after the game. Same
information — completely different experience of time and engagement.

---

## 18. Brain / Hands / Conductor — The Architecture Pattern

**What it is:**
A mental model for separating the three concerns in any agentic system:
- **Brain** — the agent(s): who does the reasoning and makes decisions
- **Hands** — the tools: how actions are executed in the world
- **Conductor** — the manager/orchestrator: when each agent is invoked and how state flows

**Why it matters:**
When these three concerns are mixed together (everything in one `main.py`), the system
becomes impossible to maintain. You cannot swap a tool API without touching the agent
logic. You cannot add a new agent without rewriting the orchestrator. Separation makes
each layer independently changeable.

**Where it lives:**
```
app_agents/    — the Brain (who)
tools/     — the Hands (how)
agent/manager.py  — the Conductor (when)
```

**The mapping in this project:**
```
Brain (app_agents/)
├── desktop_agent.py   — primary reasoning + decision making
├── browser_agent.py   — visual navigation specialist
└── summary_agent.py   — text summarisation specialist

Hands (tools/)
├── read.py            — file + clipboard reading
├── write.py           — file + clipboard writing
├── search.py          — local + web search
├── execute.py         — shell command execution
└── browser.py         — Playwright browser control

Conductor (agent/manager.py)
└── owns Runner, conversation history, streaming, session state
```

**The practical benefit:**
To swap the web search API from OpenAI to Tavily, you change one function in `tools/search.py`.
Nothing else changes. The agent doesn't know or care what search backend is used.

**Mental model:** An orchestra — the conductor (manager) decides when each section plays,
the musicians (agents) interpret the score, and the instruments (tools) produce the sound.
None of them need to know how the others work.

---

## 19. Cost Awareness in Agentic Loops

**What it is:**
A mindset — not a code pattern. Agentic systems can make many LLM calls and tool calls
per user turn. Each call costs money and takes time. Without awareness of this, a single
user request can generate 20+ API calls, thousands of tokens, and significant latency.

**Why it matters:**
This is one of the most common ways agentic projects fail in production — not because the
reasoning is wrong, but because the cost structure was never considered. A "smart" agent
that calls web search 10 times per query may be technically correct but economically
unviable.

**The main cost drivers in this project:**

| Action | Cost driver | Mitigation |
|---|---|---|
| Each LLM reasoning step | Token usage (input + output) | `max_turns` limit |
| `asyncio.gather()` parallel calls | All fire simultaneously | Only gather independent tasks |
| GPT-4o vision (BrowserAgent) | Images = many tokens | `max_turns=10` on BrowserAgent |
| `@input_guardrail` | Extra LLM call per input | Use `gpt-4o-mini`, not `gpt-4o` |
| `agent.as_tool()` call | Nested LLM call | Only use for genuinely bounded sub-tasks |

**Rules of thumb:**
- Use `gpt-4o-mini` for guardrails and classification tasks — save `gpt-4o` for reasoning
- Set `max_turns` conservatively, loosen if needed — never leave it unbounded
- Prefer sequential tool calls for dependent tasks; `gather()` only for independent ones
- Log token usage during development so surprises don't hit production

**Mental model:** Treat each LLM call like a taxi ride — you want to take the most
efficient route, not the longest one. `max_turns` is your fare cap.

---

## Concept Quick Reference

| Concept | File | Phase |
|---|---|---|
| Agent reasoning loop | `agent/manager.py` | 1 |
| async/await | All `tools/*.py` | 1 |
| asyncio.gather() | `tools/search.py` | 1 |
| @function_tool | All `tools/*.py` | 1 |
| Pydantic structured outputs | `schemas/models.py` | 1 |
| Runner | `agent/manager.py` | 1 |
| Trace | `agent/trace.py` | 1 |
| Tool chaining | `tools/search.py` + `tools/read.py` | 1 |
| Human-in-the-loop | `tools/execute.py`, `agent/approvals.py` | 1 |
| @input_guardrail | `agent/guardrails.py` | 1 |
| max_turns | `app_agents/*.py` | 1 |
| agent.as_tool() | `app_agents/summary_agent.py` | 1 |
| Chain of Thought | `app_agents/desktop_agent.py` (system prompt) | 1 |
| Handoff | `app_agents/desktop_agent.py` → `app_agents/browser_agent.py` | 2 |
| Vision / multimodal | `tools/browser.py`, `app_agents/browser_agent.py` | 2 |
| Generator streaming | `agent/manager.py`, `ui/app.py` | 3 |
| Brain / Hands / Conductor | `app_agents/`, `tools/`, `agent/manager.py` | 1–3 |
| Cost awareness | `CONCEPTS.md` (this doc), all agents | 1–3 |