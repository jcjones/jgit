#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from iterfzf import iterfzf
from sh.contrib import git

import common

PARSER = argparse.ArgumentParser(
    description="Change branch to a jgit branch"
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

def main():
    args = PARSER.parse_args()
    logger = common.configure_logging(args)
    os.chdir(args.path)

    branches = common.JGitBranches(args.path)
    branch = iterfzf(branches.iter(), prompt="Branch?")
    if branch:
	    git('checkout', branch)

if __name__ == "__main__":
    main()
