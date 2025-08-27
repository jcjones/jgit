#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from iterfzf import iterfzf
from sh.contrib import git

import common

PARSER = argparse.ArgumentParser(description="Change branch to a jgit branch")
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
    log = common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path, log)
    selection = iterfzf(branches.iter_commented_strings(), prompt="Branch?")
    if selection:
        branch, _, notes = selection.partition("#")
        if notes:
            log.info("Selected branch %s with notes %s", branch.strip(), notes.strip())

        git.checkout(branch.strip())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
