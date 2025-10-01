#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from iterfzf import iterfzf
from rich.console import Console
from sh.contrib import git
import sh

import common

PARSER = argparse.ArgumentParser(description="Delete branches")
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
PARSER.add_argument("--tracking", default="main", help="Tracking branch")
PARSER.add_argument(
    "--all",
    action="store_true",
    help="Apply to all branches, not just those known to jgit",
)


def main():
    args = PARSER.parse_args()
    common.configure_logging(args)
    os.chdir(args.path)

    console = Console()
    current_branch = git("symbolic-ref", "--short", "HEAD").strip()
    branches = common.JGitBranches(args.path, logging.getLogger(__name__))
    selections = iterfzf(
        branches.iter_commented_strings(), multi=True, prompt="Branches to delete?"
    )
    for selection in selections:
        branch, _, notes = selection.partition("#")
        branch = branch.strip()
        if branch == args.tracking:
            console.log(f"Skipping tracking branch {branch}")
            continue
        if branch == current_branch:
            console.log(f"Skipping current branch {branch}")
            continue

        try:
            git("rev-parse", branch)
        except sh.ErrorReturnCode_128:
            console.log(f"{branch} doesn't exist")
            continue

        if common.confirm(f"Delete branch {branch}?"):
            console.log(f"Deleting {branch}")
            git("branch", "-D", branch, _tty_out=True)
            branches.remove(branch)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
