from setuptools import setup

setup(
    name="git-conflict-daemon",
    version="0.1.0",
    author="Paul Claudel Izabayo",
    description="Real-time Git merge conflict detector with popup and tray icon",
    py_modules=["git_conflict_daemon"],
    install_requires=[
        "GitPython",
        "watchdog",
        "pystray",
        "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "git-conflict-daemon = git_conflict_daemon:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
