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
    def __init__(self, path, log):
        self.path = dot_git(path) / "jgit-branches"
        self.log = log.getChild(__name__)

    def _default_branch(self):
        try:
            remote = "origin"
            return (
                git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
                .removeprefix(f"{remote}/")
                .strip()
            )
        except sh.ErrorReturnCode_128:
            self.log.error("You need to set 'git remote set-head origin -a'")
            return "main"

    def _is_branch(self, name):
        try:
            git.show(name)
            return True
        except sh.ErrorReturnCode_128:
            return False

    def iter(self):
        tracked = {}
        try:
            contents = self.path.read_text()
            for line in contents.splitlines():
                if line.startswith("#"):
                    continue
                parts = line.split("#", maxsplit=1)
                branchname = parts[0].strip()
                comment_list = [parts[1]] if len(parts) == 2 else []
                tracked[branchname] = comment_list
        except FileNotFoundError:
            self.log.debug("No branches are configured in %s", self.path)

        for line in git.branch(
            list=True, verbose=True, all=True, sort="refname", _iter=True
        ):
            branchname, comment = line.removeprefix("* ").strip().split(maxsplit=1)
            branchname = branchname.strip()
            if branchname in tracked:
                comment_list = tracked[branchname]
            else:
                comment_list = []

            if line.startswith("* "):
                comment_list.append("[HEAD]")
            if branchname in tracked:
                comment_list.append("[tracked]")

            if comment_list:
                yield f"{branchname} # {' '.join(comment_list)}"
            else:
                yield branchname

            if branchname in tracked:
                del tracked[branchname]

        for branchname, comment_list in tracked.items():
            self.log.warn("Missing tracked branch: %s %s", branchname, comment_list)

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
        try:
            if branch in self.list():
                return
        except NotConfiguredException:
            self.log.info("Creating new file at %s", self.path)
        with self.path.open("a") as f:
            print(branch, file=f)


def confirm(header):
    result = iterfzf(["Yes", "No"], header=header)
    return result == "Yes"
