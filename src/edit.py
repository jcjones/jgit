#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path

from sh import vim
from rich.console import Console
from rich.syntax import Syntax

import common

PARSER = argparse.ArgumentParser(description="Edit jgit branch list")
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
    vim(branches.path, _fg=True)

    syntax = Syntax(branches.contents(), "ini", theme="monokai", line_numbers=True)
    console = Console()
    console.print("Branch list:")
    console.print(syntax)


if __name__ == "__main__":
    main()
