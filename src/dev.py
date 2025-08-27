#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from rich.console import Console
from sh.contrib import git
from sh import ErrorReturnCode_1

import common

PARSER = argparse.ArgumentParser(description="Change branch to a jgit dev branch")
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
PARSER.add_argument("--branch", "-b", default="dev", help="Dev branch to use")


def construct_dev_branch(*, dest_branch, branches, tracking):
    current_branch = git("symbolic-ref", "--short", "HEAD").strip()
    try:
        git("branch", dest_branch, tracking)
    except Exception:
        pass
    git("checkout", dest_branch)
    git("reset", "--hard", tracking)

    console = Console()
    with console.status(f"[bold green]Merging branches into {dest_branch}"):
        try:
            for branch in branches.iter():
                console.log(f"Merging {branch} into {dest_branch}")
                git("merge", "-m", f"Auto-merge {branch} by jgit-dev", branch)
        except ErrorReturnCode_1:
            console.log(f"Failed to merge {branch} into {dest_branch}.")
            git("merge", "--abort")
            git("checkout", current_branch)
            console.log(f"Aborted, returned to {current_branch}")


def main():
    args = PARSER.parse_args()
    common.configure_logging(args)
    os.chdir(args.path)

    construct_dev_branch(
        branches=common.JGitBranches(args.path, logging.getLogger(__name__)),
        tracking=args.tracking,
        dest_branch=args.branch,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
