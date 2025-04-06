# popup_window.py

import sys
import tkinter as tk
import subprocess
from pathlib import Path
from git import Repo

print(f"[POPUP SCRIPT] Launched with args: {sys.argv}")

file_path = None
repo_path = None

def get_diff(repo, rel_path):
    try:
        repo.remotes.origin.fetch()
        return repo.git.diff('origin/' + repo.active_branch.name, '--', rel_path)
    except Exception as e:
        return f"Error generating diff: {e}"

def pull_changes():
    try:
        subprocess.run(["git", "pull"], cwd=repo_path)
    except Exception as e:
        print(f"Git pull failed: {e}")

def ask_user():
    repo = Repo(repo_path)
    rel_path = Path(file_path).relative_to(repo.working_tree_dir)

    root = tk.Tk()
    root.title("Merge Conflict Warning")
    root.geometry("700x200")
    root.lift()
    root.attributes("-topmost", True)

    label = tk.Label(root, text=f"{file_path}\n\nhas remote changes. Pull now?", padx=20, pady=10)
    label.pack()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    def on_yes():
        pull_changes()
        root.destroy()

    def on_no():
        root.destroy()

    def on_view():
        diff_text = get_diff(repo, str(rel_path))
        print("\n==================== Incoming Changes ====================")
        print(f"File: {file_path}\n")
        print(diff_text or "No incoming changes.")
        print("========================================================\n")

    tk.Button(btn_frame, text="Yes (Pull)", command=on_yes).pack(side="left", padx=5)
    tk.Button(btn_frame, text="No (Continue)", command=on_no).pack(side="left", padx=5)
    tk.Button(btn_frame, text="View Changes", command=on_view).pack(side="left", padx=5)

    root.mainloop()

if __name__ == "__main__":
    file_path = sys.argv[1]
    repo_path = sys.argv[2]
    ask_user()
