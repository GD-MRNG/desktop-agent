import os
from pathlib import Path

import pytest

from tools.sandbox import PathEscapeError, resolve_within_root


def test_relative_path_within_root_resolves(tmp_path):
    (tmp_path / "sub").mkdir()
    resolved = resolve_within_root("sub/file.txt", root=str(tmp_path))
    assert resolved == (tmp_path / "sub" / "file.txt").resolve()


def test_root_itself_resolves(tmp_path):
    resolved = resolve_within_root(".", root=str(tmp_path))
    assert resolved == tmp_path.resolve()


def test_traversal_above_root_is_rejected(tmp_path):
    with pytest.raises(PathEscapeError):
        resolve_within_root("../escape.txt", root=str(tmp_path))


def test_absolute_path_outside_root_is_rejected(tmp_path):
    outside = tmp_path.parent / "escape.txt"
    with pytest.raises(PathEscapeError):
        resolve_within_root(str(outside), root=str(tmp_path))


def test_root_falls_back_to_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_WORKDIR", str(tmp_path))
    resolved = resolve_within_root("file.txt")
    assert resolved == (tmp_path / "file.txt").resolve()


def test_root_falls_back_to_cwd(monkeypatch):
    monkeypatch.delenv("AGENT_WORKDIR", raising=False)
    resolved = resolve_within_root("file.txt")
    assert resolved == (Path(os.getcwd()) / "file.txt").resolve()
