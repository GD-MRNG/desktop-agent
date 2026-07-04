import os
from pathlib import Path


class PathEscapeError(Exception):
    """Raised when a requested path resolves outside the allowed sandbox root."""


def resolve_within_root(path: str, root: str | None = None) -> Path:
    """Resolve `path` against the sandbox root and reject anything that escapes it.

    Root defaults to the AGENT_WORKDIR env var, falling back to the current
    working directory. This is the single containment check shared by the file
    and shell tools — hardening and the future Docker volume mount both key off
    the same AGENT_WORKDIR concept, so there is one control point, not two.

    Args:
        path: Absolute or relative path requested by the agent.
        root: Override for the sandbox root (mainly for tests).

    Raises:
        PathEscapeError: if the resolved path is outside the root, whether via
            `..` traversal or an absolute path pointing elsewhere.
    """
    root_path = Path(root or os.environ.get("AGENT_WORKDIR") or os.getcwd()).resolve()
    target = (root_path / path).resolve()

    if target != root_path and root_path not in target.parents:
        raise PathEscapeError(f"'{path}' resolves outside the allowed root '{root_path}'")

    return target
