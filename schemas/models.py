from pydantic import BaseModel


class FileContent(BaseModel):
    content: str
    path: str
    line_count: int


class DirectoryListing(BaseModel):
    path: str
    entries: list[str]
    count: int


class ClipboardContent(BaseModel):
    content: str


class OperationResult(BaseModel):
    success: bool
    message: str
    path: str = ""


class SearchMatch(BaseModel):
    file: str
    line_number: int
    line_content: str


class SearchResults(BaseModel):
    matches: list[SearchMatch]
    total: int
    query: str


class WebResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchResults(BaseModel):
    results: list[WebResult]
    query: str


class CommandResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    command: str


class SafetyCheck(BaseModel):
    # [CONCEPT] Pydantic structured output for guardrail agent
    # The guardrail agent returns this model so the tripwire logic
    # can read is_safe as a typed bool rather than parsing free text.
    is_safe: bool
    reason: str


class ScreenshotResult(BaseModel):
    image_base64: str
    width: int
    height: int
