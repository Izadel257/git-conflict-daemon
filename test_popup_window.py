# test_popup_window.py

import pytest
from unittest.mock import MagicMock, patch
import popup_window
from popup_window import get_diff, pull_changes

# === TEST get_diff ===
def test_get_diff_returns_diff_text():
    mock_repo = MagicMock()
    mock_repo.git.diff.return_value = "diff --git a/file.txt b/file.txt\n+new line"
    mock_repo.active_branch.name = "main"
    mock_repo.remotes.origin.fetch.return_value = None

    result = get_diff(mock_repo, "file.txt")

    assert "diff --git" in result
    mock_repo.remotes.origin.fetch.assert_called_once()
    mock_repo.git.diff.assert_called_once()

# === TEST pull_changes ===
@patch("popup_window.subprocess.run")
def test_pull_changes_calls_git_pull(mock_run):
    popup_window.repo_path = "/mock/path"
    pull_changes()
    mock_run.assert_called_once_with(["git", "pull"], cwd="/mock/path")
