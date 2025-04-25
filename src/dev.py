#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

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
    logger = logging.getLogger("construct_dev_branch")
    current_branch = git("symbolic-ref", "--short", "HEAD").strip()
    try:
        git("branch", dest_branch, tracking)
    except Exception:
        pass
    git("checkout", dest_branch)
    git("reset", "--hard", tracking)

    try:
        for branch in branches.iter():
            logger.info("Merging %s into %s", branch, dest_branch)
            git("merge", "-m", f"Auto-merge {branch} by jgit-dev", branch)
    except ErrorReturnCode_1:
        logger.error("Failed to merge %s into %s.", branch, dest_branch)
        git("merge", "--abort")
        git("checkout", current_branch)
        logger.error("Aborted, returned to %s", current_branch)


def main():
    args = PARSER.parse_args()
    common.configure_logging(args)
    os.chdir(args.path)

    construct_dev_branch(
        branches=common.JGitBranches(args.path),
        tracking=args.tracking,
        dest_branch=args.branch,
    )


if __name__ == "__main__":
    main()
