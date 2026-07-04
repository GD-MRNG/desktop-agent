import pyperclip
from agents import function_tool
from schemas.models import FileContent, DirectoryListing, ClipboardContent
from tools.sandbox import resolve_within_root


@function_tool
async def read_file(path: str) -> FileContent:
    """Read a text file and return its content with line count.

    Args:
        path: Absolute or relative path to the file to read.
    """
    # Basic async tool definition with Pydantic return type.
    # The @function_tool decorator extracts the signature + docstring to build
    # the JSON schema the model sees. Return type is a BaseModel, not a raw dict.
    # resolve_within_root contains the path to AGENT_WORKDIR before any I/O happens.
    resolved = resolve_within_root(path)
    with open(resolved, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    return FileContent(content=content, path=path, line_count=len(lines))


@function_tool
async def list_directory(path: str) -> DirectoryListing:
    """List files and directories at the given path.

    Args:
        path: Directory path to list. Use '.' for the current directory.
    """
    # Structured return values — every field is named and typed.
    resolved = resolve_within_root(path)
    entries = [p.name for p in resolved.iterdir()]
    return DirectoryListing(path=path, entries=sorted(entries), count=len(entries))


@function_tool
async def read_clipboard() -> ClipboardContent:
    """Read the current contents of the system clipboard."""
    # Side-effect-free tool — reads OS state without modifying it.
    content = pyperclip.paste()
    return ClipboardContent(content=content)
