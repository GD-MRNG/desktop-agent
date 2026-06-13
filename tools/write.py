import os
import pyperclip
from agents import function_tool
from schemas.models import OperationResult


@function_tool
async def write_file(path: str, content: str) -> OperationResult:
    """Write content to a file, creating it if it does not exist.

    Args:
        path: Path to the file to write (will be created or overwritten).
        content: Text content to write to the file.
    """
    # Side-effecting tool — creates or overwrites a file.
    # Pydantic return communicates clearly whether the operation succeeded.
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return OperationResult(success=True, message=f"Wrote {len(content)} characters.", path=path)


@function_tool
async def append_file(path: str, content: str) -> OperationResult:
    """Append content to an existing file, or create it if it does not exist.

    Args:
        path: Path to the file to append to.
        content: Text content to append.
    """
    # Idempotency consideration — append is safer than overwrite
    # when the caller does not want to destroy existing content.
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)
    return OperationResult(success=True, message=f"Appended {len(content)} characters.", path=path)


@function_tool
async def write_clipboard(content: str) -> OperationResult:
    """Write text to the system clipboard.

    Args:
        content: Text to place on the clipboard.
    """
    # Lightweight side effect — changes OS state, returns typed result.
    pyperclip.copy(content)
    return OperationResult(success=True, message="Content copied to clipboard.", path="")
