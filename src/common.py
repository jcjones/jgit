#!/usr/bin/python3

from iterfzf import iterfzf
from pathlib import Path
from sh.contrib import git

import logging
import sh


class NoGitRepoException(Exception):
    pass


class NotConfiguredException(Exception):
    pass


def configure_logging(args):
    logging.basicConfig(level=args.log_level)
    logging.getLogger("sh").setLevel(logging.WARNING)
    return logging.getLogger("jgit")


def dot_git(pos=Path.cwd()):
    while pos.name:
        dot_git = pos / ".git"
        if dot_git.is_dir():
            return dot_git
        pos = pos.parent
    raise NoGitRepoException("Could not find a parent directory with a .git subdir")


class JGitBranches:
    def __init__(self, path):
        self.path = dot_git(path) / "jgit-branches"

    def _default_branch(self):
        try:
            remote = "origin"
            return (
                git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
                .removeprefix(f"{remote}/")
                .strip()
            )
        except sh.ErrorReturnCode_128:
            log = logging.getLogger("jgit")
            log.error("You need to set 'git remote set-head origin -a'")
            return "main"

    def iter(self):
        try:
            contents = self.path.read_text()
            for line in contents.splitlines():
                if not line.startswith("#"):
                    yield line
            yield self._default_branch()
        except FileNotFoundError:
            raise NotConfiguredException("No branches are configured in %s", self.path)

    def list(self):
        return list(self.iter())

    def contents(self):
        return self.path.read_text()

    def remove(self, branch):
        contents = self.path.read_text()
        with self.path.open("w") as f:
            for line in contents.splitlines():
                if line != branch:
                    print(line, file=f)

    def append(self, branch):
        if branch in self.list():
            return
        with self.path.open("a") as f:
            print(branch, file=f)


def confirm(header):
    result = iterfzf(["Yes", "No"], header=header)
    return result == "Yes"
