#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from rich.console import Console
from sh.contrib import git
import sh

import common

PARSER = argparse.ArgumentParser(description="Cleanup merged jgit branches")
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


def branch_apparently_merged(*, tracking, branch):
    logger = logging.getLogger(__name__)

    logger.debug("Checking if %s is merged to %s", branch, tracking)
    diff_result = git("diff", git("merge-base", tracking, branch).strip(), branch)
    if not diff_result:
        logger.debug("No diff between %s and %s", branch, tracking)
        return True

    logger.debug(
        "Diff between %s and %s is %d lines", branch, tracking, diff_result.count("\n")
    )
    patch_id = git("patch-id", "--stable", _in=diff_result).split()[0]
    logger.debug("Calculated patch-id %s between %s..%s", patch_id, tracking, branch)
    for rev in git("rev-list", f"{branch}..{tracking}").split():
        other_patch_id = git(
            "patch-id", "--stable", _in=git("diff", f"{rev}~", rev)
        ).split()[0]
        if patch_id == other_patch_id:
            logger.debug("Found patch-id %s at rev %s", patch_id, rev)
            return True
    return False


def is_local_branch(branch):
    if "*" in branch:
        return False
    if "release/" in branch:
        return False
    return True


def main():
    args = PARSER.parse_args()
    common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path)
    if args.all:
        branch_iter = filter(is_local_branch, git("branch").split())
    else:
        branch_iter = branches.iter()

    current_branch = git("symbolic-ref", "--short", "HEAD").strip()

    console = Console()
    with console.status("[bold green]Cleaning branches..."):
        for branch in branch_iter:
            if branch == args.tracking:
                continue
            if branch == current_branch:
                console.log(f"Skipping current branch {branch}")
                continue

            try:
                git("rev-parse", branch)
            except sh.ErrorReturnCode_128:
                console.log(f"{branch} doesn't exist")
                continue

            if not branch_apparently_merged(tracking=args.tracking, branch=branch):
                console.log(f"{branch} has outstanding changes")
                continue

            console.log(f"{branch} is apparently merged")

            if common.confirm(f"Delete apparently-merged branch {branch}?"):
                console.log(f"Deleting {branch}")
                git("branch", "-D", branch, _tty_out=True)
                branches.remove(branch)


if __name__ == "__main__":
    main()
