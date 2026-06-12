import asyncio
from dotenv import load_dotenv
from agent.manager import AgentManager


def main() -> None:
    # [CONCEPT] asyncio.run() starts the event loop and drives the top-level coroutine.
    # Everything inside manager.start() runs asynchronously from this single entry point.
    load_dotenv()
    asyncio.run(AgentManager().start())


if __name__ == "__main__":
    main()
