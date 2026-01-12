#!/usr/bin/python3

from pathlib import Path
import argparse
import logging
import os
import sys

from sh.contrib import git
from sh import gh
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Prompt

import common

PARSER = argparse.ArgumentParser(description="New branch")
PARSER.add_argument(
    "--log-level",
    default=logging.INFO,
    type=lambda x: getattr(logging, x.upper()),
    help="Configure the logging level, defaults to INFO.",
)
PARSER.add_argument(
    "--path",
    "-p",
    default=Path.cwd(),
    type=lambda x: Path(x),
    help="Path to operate from",
)


def main():
    args = PARSER.parse_args()
    common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path, logging.getLogger(__name__))

    console = Console()

    gh.issue.list(
        limit=10,
        _out=sys.stdout,
        _err=sys.stderr,
    )

    current_branch = git("symbolic-ref", "--short", "HEAD").strip()
    new_branch = (
        Prompt().ask("New branch name", console=console, default=current_branch).strip()
    )

    git.branch(new_branch, branches._default_branch())
    git.checkout(new_branch)

    syntax = Syntax(branches.contents(), "ini", theme="monokai", line_numbers=True)
    console.print("Branch list:")
    console.print(syntax)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
