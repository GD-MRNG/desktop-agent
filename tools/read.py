import os
import pyperclip
from agents import function_tool
from schemas.models import FileContent, DirectoryListing, ClipboardContent


@function_tool
async def read_file(path: str) -> FileContent:
    """Read a text file and return its content with line count.

    Args:
        path: Absolute or relative path to the file to read.
    """
    # [CONCEPT] Basic async tool definition with Pydantic return type.
    # The @function_tool decorator extracts the signature + docstring to build
    # the JSON schema the model sees. Return type is a BaseModel, not a raw dict.
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    return FileContent(content=content, path=path, line_count=len(lines))


@function_tool
async def list_directory(path: str) -> DirectoryListing:
    """List files and directories at the given path.

    Args:
        path: Directory path to list. Use '.' for the current directory.
    """
    # [CONCEPT] Structured return values — every field is named and typed.
    entries = os.listdir(path)
    return DirectoryListing(path=path, entries=sorted(entries), count=len(entries))


@function_tool
async def read_clipboard() -> ClipboardContent:
    """Read the current contents of the system clipboard."""
    # [CONCEPT] Side-effect-free tool — reads OS state without modifying it.
    content = pyperclip.paste()
    return ClipboardContent(content=content)
