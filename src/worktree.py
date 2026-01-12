#!/usr/bin/python3

from pathlib import Path
import argparse
import logging
import os

from iterfzf import iterfzf
from sh.contrib import git
from rich.console import Console
from rich.prompt import Prompt, Confirm

import common

PARSER = argparse.ArgumentParser(description="Worktrees")
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


def new():
    args = PARSER.parse_args()
    log = common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path, logging.getLogger(__name__))

    worktrees = common.dot_git(args.path).parent / ".worktrees"
    if not worktrees.is_dir():
        worktrees.mkdir()

    console = Console()

    selection = iterfzf(branches.iter_commented_strings(), prompt="Branch?")
    if selection:
        branch, _, notes = selection.partition("#")
        if notes:
            log.info("Selected branch %s with notes %s", branch.strip(), notes.strip())

    branch = branch.strip()
    new_wt = Prompt().ask("New worktree name", console=console, default=branch).strip()
    new_wt_path = worktrees / new_wt

    git.worktree.add(new_wt_path, branch)


def remove():
    args = PARSER.parse_args()
    os.chdir(args.path)

    worktrees = common.dot_git(args.path).parent / ".worktrees"
    assert worktrees.is_dir()

    console = Console()

    wt_list = git.worktree.list().split("\n")

    selection = iterfzf(wt_list)
    if selection:
        worktree_path, commit, branch = selection.split()
        if Confirm().ask(
            f"Really remove {worktree_path}, {commit}, {branch}?", console=console
        ):
            git.worktree.remove(worktree_path)
