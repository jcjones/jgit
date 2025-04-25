#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from iterfzf import iterfzf
from sh.contrib import git
import sh
import rich

import common

PARSER = argparse.ArgumentParser(
    description="Cleanup merged jgit branches"
)
PARSER.add_argument(
    "--log-level",
    default=logging.INFO,
    type=lambda x: getattr(logging, x.upper()),
    help="Configure the logging level, defaults to INFO.",
)
PARSER.add_argument(
    "--path", "-p",
    default=Path.cwd(),
    type=lambda x: Path(x),
    help="Path to operate from"
)
PARSER.add_argument(
    "--tracking",
    default="main",
    help="Tracking branch"
)

def branch_apparently_merged(*, tracking, branch):
    logger = logging.getLogger(__name__)

    patch_id=git('patch-id', '--stable', _in=git('diff', git('merge-base', tracking, branch).strip(), branch)).split()[0]
    logger.debug("Calculated patch-id %s between %s..%s", patch_id, tracking, branch)
    for rev in git('rev-list', f'{branch}..{tracking}').split():
        other_patch_id=git('patch-id', '--stable', _in=git('diff', f'{rev}~', rev)).split()[0]
        if patch_id == other_patch_id:
            logger.debug("Found patch-id %s at rev %s", patch_id, rev)
            return True
    return False

def main():
    args = PARSER.parse_args()
    logger = common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path)
    for branch in branches.iter():
        try:
            git('rev-parse', branch)
        except sh.ErrorReturnCode_128:
            logger.info("%s doesn't exist", branch)
            continue

        if not branch_apparently_merged(tracking=args.tracking, branch=branch):
            continue

        logger.info("%s is apparently merged", branch)

        if common.confirm(f"Delete apparently-merged branch {branch}?"):
            logger.info("Deleting %s", branch)
            git('branch', '-D', branch, _tty_out=True)
            branches.remove(branch)


if __name__ == "__main__":
    main()
