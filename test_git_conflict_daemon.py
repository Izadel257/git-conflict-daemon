# test_git_conflict_daemon.py

import os
import time
import subprocess
from unittest.mock import MagicMock, patch
from git_conflict_daemon import has_remote_changes, get_diff_preview, find_git_repos, poll_file_access

# === TEST has_remote_changes ===
def test_has_remote_changes_true():
    mock_repo = MagicMock()
    mock_repo.active_branch.name = "main"
    mock_repo.git.diff.return_value = "some changes"
    mock_repo.remotes.origin.fetch.return_value = None

    result = has_remote_changes(mock_repo, "file.txt")
    assert result is True

@patch("git_conflict_daemon.CONFIG", {"branches": ["dev"]})
def test_has_remote_changes_skips_unwatched_branch():
    mock_repo = MagicMock()
    mock_repo.active_branch.name = "main"  # not in watched branches
    result = has_remote_changes(mock_repo, "file.txt")
    assert result is False

# === TEST get_diff_preview ===
def test_get_diff_preview_returns_diff():
    mock_repo = MagicMock()
    mock_repo.git.diff.return_value = "diff --git..."
    result = get_diff_preview(mock_repo, "file.txt")
    assert "diff --git" in result

# === TEST find_git_repos ===
def test_find_git_repos_finds_repo(tmp_path):
    repo_dir = tmp_path / "myrepo"
    os.makedirs(repo_dir)
    subprocess.run(["git", "init"], cwd=repo_dir, stdout=subprocess.PIPE)

    repos = find_git_repos([str(tmp_path)])
    assert any(str(repo.working_tree_dir).endswith("myrepo") for repo in repos)

# === TEST poll_file_access triggers popup ===
# @patch("git_conflict_daemon.has_remote_changes", return_value=True)
# @patch("git_conflict_daemon.launch_popup")
# @patch("git_conflict_daemon.SEEN_GRACE_PERIOD", 0)
# def test_poll_file_access_triggers_popup(mock_launch, mock_has_remote, tmp_path):
#     # Setup dummy repo and file
#     dummy_repo = MagicMock()
#     dummy_repo.working_tree_dir = str(tmp_path)
#     tracked_file = tmp_path / "tracked.txt"
#     tracked_file.write_text("initial content")
#     real_path = os.path.realpath(str(tracked_file))

#     # Import shared state from daemon
#     from git_conflict_daemon import last_seen_atime, active_files
#     last_seen_atime.clear()
#     active_files.clear()

#     # Step 1: simulate first access
#     os.stat(real_path)
#     poll_file_access([(real_path, dummy_repo)])

#     # Step 2: simulate second access (with actual read to bump atime)
#     time.sleep(1)
#     with open(real_path) as f:
#         _ = f.read()

#     active_files.clear()
#     poll_file_access([(real_path, dummy_repo)])

#     mock_launch.assert_called_once_with(real_path, dummy_repo.working_tree_dir)
