# git_conflict_daemon.py
# A daemon that monitors Git repositories for remote changes and notifies the user via a popup window.
# It uses the GitPython library to interact with Git repositories, the watchdog library to monitor file changes, and the pystray library to create a system tray icon.


import os
import time
import threading
import platform
import json
import queue
import subprocess
from multiprocessing import Process
from git import Repo, GitCommandError, InvalidGitRepositoryError
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from pathlib import Path
import git_conflict_daemon

# === Config ===
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.git_conflictrc.json")
CONFIG = {
    "watch_paths": [os.path.expanduser("~")],
    "branches": [],
    "popup": True
}

if os.path.exists(DEFAULT_CONFIG_PATH):
    try:
        with open(DEFAULT_CONFIG_PATH) as f:
            user_config = json.load(f)
            CONFIG.update(user_config)
    except Exception as e:
        print(f"Failed to load config: {e}")

POLL_INTERVAL = 2
access_times = {}
last_seen_atime = {}
active_files = {}
SEEN_GRACE_PERIOD = 5
popup_queue = queue.Queue()

daemon_running = True

# === Git Helpers ===
def find_git_repos(root_paths):
    """ Find all Git repositories in the specified root paths. """
    git_repos = []
    for root_path in root_paths:
        for dirpath, dirnames, filenames in os.walk(os.path.expanduser(root_path)):
            if ".git" in dirnames:
                try:
                    repo = Repo(dirpath)
                    git_repos.append(repo)
                    dirnames[:] = []
                except InvalidGitRepositoryError:
                    continue
    return git_repos

def get_tracked_files(repo):
    """ Get all tracked files in the repository. """
    try:
        repo_path = repo.working_tree_dir
        files = repo.git.ls_files().splitlines()
        return [os.path.join(repo_path, f) for f in files]
    except Exception as e:
        print(f"Error getting tracked files: {e}")
        return []

def has_remote_changes(repo, rel_path):
    """ Check if there are remote changes for the given file. """
    try:
        if CONFIG["branches"] and repo.active_branch.name not in CONFIG["branches"]:
            return False
        repo.remotes.origin.fetch()
        diff_output = repo.git.diff('origin/' + repo.active_branch.name, '--', rel_path)
        return bool(diff_output.strip())
    except Exception as e:
        print(f"Error checking remote changes: {e}")
        return False

def get_diff_preview(repo, rel_path):
    try:
        return repo.git.diff('origin/' + repo.active_branch.name, '--', rel_path)
    except Exception as e:
        return f"Error generating diff: {e}"

def run_git_pull(repo):
    try:
        print(f"Pulling latest changes in {repo.working_tree_dir}...")
        repo.git.pull()
        print("Pull completed.")
    except Exception as e:
        print(f"Pull failed: {e}")

def popup_worker(root):
    def process_queue():
        try:
            file_path, repo = popup_queue.get_nowait()
        except queue.Empty:
            root.after(100, process_queue)
            return

        if not CONFIG.get("popup", True):
            print(f"WARNING: {file_path} has remote changes.")
            root.after(100, process_queue)
            return

        window = tk.Toplevel(root)
        window.title("Merge Conflict Warning")
        window.lift()
        window.attributes("-topmost", True)

        window.update_idletasks()
        w = window.winfo_screenwidth()
        h = window.winfo_screenheight()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x = w // 2 - size[0] // 2
        y = h // 2 - size[1] // 2
        window.geometry("+%d+%d" % (x, y))

        label = tk.Label(window, text=f"{file_path}\n\nhas remote changes. Pull now?", padx=20, pady=10)
        label.pack()
        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=10)

        def on_response(pull):
            window.destroy()
            if pull:
                threading.Thread(target=run_git_pull, args=(repo,), daemon=True).start()

        def show_diff():
            rel_path = os.path.relpath(file_path, repo.working_tree_dir)
            diff_text = get_diff_preview(repo, rel_path)

            text_window = tk.Toplevel(window)
            text_window.title("Incoming Changes Preview")
            text_window.geometry("800x400")

            text_widget = tk.Text(text_window, wrap=tk.WORD)
            text_widget.pack(expand=True, fill=tk.BOTH)

            scrollbar = tk.Scrollbar(text_widget)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar.config(command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)

            text_widget.insert(tk.END, diff_text)
            text_widget.config(state=tk.DISABLED)

        tk.Button(btn_frame, text="Yes (Pull)", command=lambda: on_response(True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="No (Continue)", command=lambda: on_response(False)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="View Changes", command=show_diff).pack(side="left", padx=5)

        root.after(100, process_queue)

    root.after(100, process_queue)
    root.mainloop()

def polling_loop(file_repo_pairs):
    while True:
        now = time.time()
        for file_path, repo in file_repo_pairs:
            try:
                if not os.path.exists(file_path):
                    continue

                stat = os.stat(file_path)
                atime = stat.st_atime

                if file_path in active_files and now - atime > SEEN_GRACE_PERIOD:
                    del active_files[file_path]

                if file_path not in last_seen_atime:
                    last_seen_atime[file_path] = atime

                elif atime > last_seen_atime[file_path]:
                    last_seen_atime[file_path] = atime
                    if file_path in active_files:
                        continue

                    rel_path = os.path.relpath(file_path, repo.working_tree_dir)
                    if has_remote_changes(repo, rel_path):
                        print(f"Detected remote changes in: {file_path}")
                        active_files[file_path] = True
                        launch_popup(file_path, repo.working_tree_dir)

            except Exception as e:
                print(f"Polling error: {e}")
                continue

        time.sleep(POLL_INTERVAL)

class DummyEventHandler(FileSystemEventHandler):
    pass

def create_image():
    image = Image.new('RGB', (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill=(255, 0, 0))
    return image

def toggle_daemon(icon, item):
    global daemon_running
    daemon_running = not daemon_running
    status = "resumed" if daemon_running else "paused"
    print(f"Daemon {status}.")

def show_repos(icon, item):
    print("Active Repositories:")
    for repo in repos:
        print("-", repo.working_tree_dir)

def quit_daemon(icon, item):
    print("Quitting daemon...")
    icon.stop()
    observer.stop()

def popup_runner(file_path, repo_path):
    # Locate popup_window.py inside the installed package
    package_dir = Path(git_conflict_daemon.__file__).parent
    popup_script = package_dir / "popup_window.py"

    if not popup_script.exists():
        print(f"[POPUP RUNNER] ERROR: popup_window.py not found at {popup_script}")
        return

    print(f"[POPUP RUNNER] Launching popup for: {file_path} in {repo_path}")
    result = os.system(f'python3 "{popup_script}" "{file_path}" "{repo_path}"')
    print(f"[POPUP RUNNER] Popup process exited with code: {result}")

def launch_popup(file_path, repo_path):
    Process(target=popup_runner, args=(file_path, repo_path)).start()
def launch_tray():
    menu = Menu(
        MenuItem("Pause/Resume", toggle_daemon),
        MenuItem("Show Repos", show_repos),
        MenuItem("Quit", quit_daemon)
    )
    tray_icon = Icon("GitConflictDaemon", create_image(), "Git Conflict Daemon", menu)
    tray_icon.run()

def start_git_conflict_daemon():
    global repos, observer
    print("Starting Git Conflict Daemon")

    repos = find_git_repos(CONFIG["watch_paths"])
    file_repo_pairs = [(f, repo) for repo in repos for f in get_tracked_files(repo)]

    if not file_repo_pairs:
        print("No Git-tracked files found in configured paths.")

    observer = Observer()
    for path in CONFIG["watch_paths"]:
        observer.schedule(DummyEventHandler(), os.path.expanduser(path), recursive=True)
    observer.start()

    threading.Thread(target=polling_loop, args=(file_repo_pairs,), daemon=True).start()

def main():
    print("🚀 Starting Git Conflict Daemon with Tray...")
    threading.Thread(target=start_git_conflict_daemon, daemon=True).start()
    launch_tray()

if __name__ == "__main__":
    main()
