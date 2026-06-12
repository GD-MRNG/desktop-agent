from agents import Agent
from tools.read import read_file, list_directory, read_clipboard
from tools.write import write_file, append_file, write_clipboard
from tools.search import search_files, web_search
from tools.execute import run_command
from app_agents.summary_agent import SummaryAgent
from agent.guardrails import safety_check

_SYSTEM_PROMPT = """You are a desktop assistant with file system and shell access.

Before calling any tool, briefly state what you are about to do and why.
Format: "I will [action] because [reason]."

Guidelines:
- Use search_files to locate content in files, then read_file to examine the matches — this is tool chaining
- Use web_search for current information not available in local files
- Always use run_command for shell tasks — it will prompt the user for approval first
- Call summarise_text when asked to summarise or condense content
- Be concise and precise in your final responses
"""

# Brain layer — the agent definition is the "who" and "what". It knows nothing
# about when it runs or how conversation history is managed; that is the Conductor's job.
DesktopAgent = Agent(
    name="DesktopAgent",
    instructions=_SYSTEM_PROMPT,
    model="gpt-4o",
    tools=[
        read_file,
        list_directory,
        read_clipboard,
        write_file,
        append_file,
        write_clipboard,
        search_files,
        web_search,
        run_command,
        SummaryAgent.as_tool(
            # agent-as-tool: SummaryAgent runs as a nested sub-agent.
            # DesktopAgent calls it like any other tool and receives the summary result back.
            # The parent retains control — unlike a handoff where the parent exits the flow.
            tool_name="summarise_text",
            tool_description="Summarise a block of text into 3–5 concise sentences. Pass the full text as input.",
            max_turns=3,  # max_turns circuit breaker for this sub-agent's loop
        ),
    ],
    input_guardrails=[safety_check],  # middleware — fires before agent reasoning starts
)
# max_turns=15 for DesktopAgent is set in AgentManager.run() via Runner.run(max_turns=15)
