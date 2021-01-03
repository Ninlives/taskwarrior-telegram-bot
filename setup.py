from setuptools import setup

setup(
    name="taskwarrior-telegram-bot",
    version="0.1.0",
    package_dir={"": "src"},
    packages=["bot", "lib"],
    entry_points={"console_scripts": ["taskbot=bot.entry:main"]},
    install_requires=["python-telegram-bot", "tasklib"],
)
