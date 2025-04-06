# 👀 Git Conflict Daemon

Welcome!  
This is a lightweight, real-time Git conflict detector that runs quietly in the background and gently lets you know *before* you make changes to files that would result in merge conflicts.

## 🚀 What It Does

- Watches your Git repositories in real time
- Detects if the file you're about to edit has remote changes
- Pops up a friendly window to:
  - Warn you
  - Offer to pull changes
  - Show you a preview of incoming diffs
- Lives in your system tray for easy control

All without getting in your way. Just helpful. Just smart. ✨

---

## 🔧 Installation

Once it's published, just run:

```bash
pip3 install git-conflict-daemon
```

Or if you're testing it locally:

```bash
git clone https://github.com/Izadel257/git-conflict-daemon.git
cd git-conflict-daemon
pip3 install .
```

---

## 💥 Usage

After installation, simply run:

```bash
git-conflict-daemon
```

You'll see a tray icon appear. The daemon is now watching your Git repos, quietly working in the background.

---

## 🛠️ Configuration

You can customize its behavior using a config file at:

```
~/.git_conflictrc.json
```

Example:

```json
{
  "watch_paths": ["/Users/you/projects"],
  "branches": ["main", "dev"],
  "popup": true
}
```

---

## ❓ Why Use This?

If you’ve ever:
- Opened a file
- Made edits
- Pushed…
- ...only to hit a merge conflict 🙃

Then this tool is for you.

It helps you **pull first**, or at least be aware, so you’re not surprised later.

---

## 🧪 Running Tests

If you're hacking on the daemon:

```bash
pip install pytest
pytest
```

---

## ✨ Thanks!

Built with love (and Python) by [Paul Claudel Izabayo](https://github.com/izadel257).  
Contributions and ideas are welcome.

