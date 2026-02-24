# jgit

A collection of Git workflow helpers for managing feature branches. jgit tracks a set of "active" branches per-repo in `.git/jgit-branches` and provides interactive tools (powered by `fzf`) for switching, creating, merging, and cleaning up branches.

## Concepts

**Branch list** — Each repo has a file at `.git/jgit-branches` listing the branches you're actively working on. Most jgit commands operate on this list. You can add inline comments with `#` to annotate branches.

**Default branch** — jgit detects the default branch from `origin/HEAD` (set via `git remote set-head origin -a`).

**Worktrees** — jgit stores worktrees in a `.worktrees/` directory adjacent to the repo root.

## Installation

```sh
pip install .
# or
uv pip install .
```

Requires Python >= 3.13 and [`fzf`](https://github.com/junegunn/fzf) in your `$PATH`.

## Commands

### `jgit-track-this`

Add the current branch to the jgit branch list. Prints the updated list on exit.

```sh
jgit-track-this [-p PATH]
```

### `jgit-change-branch`

Interactively select a branch from the jgit branch list (via `fzf`) and check it out.

```sh
jgit-change-branch [-p PATH]
```

### `jgit-new-branch`

List open GitHub issues (via `gh`), prompt for a new branch name, create it from the default branch, and check it out.

```sh
jgit-new-branch [-p PATH]
```

### `jgit-rename-this`

Rename the current branch (prompts for the new name), updating the branch list accordingly.

```sh
jgit-rename-this [-p PATH]
```

### `jgit-edit-branches`

Open the `.git/jgit-branches` file in `vim` for manual editing, then print the updated list.

```sh
jgit-edit-branches [-p PATH]
```

### `jgit-del-branches`

Interactively select one or more branches from the jgit branch list to delete (with confirmation). Skips the current and tracking branches.

```sh
jgit-del-branches [-p PATH] [--tracking BRANCH] [--all]
```

- `--tracking` — tracking branch to protect from deletion (default: `main`)
- `--all` — show all local branches instead of just those in the jgit list

### `jgit-cleanup-branches`

Find branches that appear to be merged (using `git patch-id`) and offer to delete them.

```sh
jgit-cleanup-branches [-p PATH] [--tracking BRANCH] [--all]
```

- `--tracking` — branch to compare against (default: `main`)
- `--all` — check all local branches, not just those in the jgit list

### `jgit-dev`

Create (or reset) a `dev` branch by merging all branches in the jgit list on top of the tracking branch. Useful for deploying a combination of in-progress branches together.

```sh
jgit-dev [-p PATH] [--tracking BRANCH] [--branch DEV_BRANCH]
```

- `--tracking` — base branch (default: `main`)
- `--branch` — name for the merged branch (default: `dev`)

### `jgit-wt-new`

Create a new git worktree under `.worktrees/`. Prompts to select an existing branch from the jgit list or create a new branch, then prompts for a worktree directory name.

```sh
jgit-wt-new [-p PATH]
```

### `jgit-wt-del`

Interactively select one or more worktrees from `.worktrees/` to remove, with an option to also delete the associated branch.

```sh
jgit-wt-del [-p PATH]
```

## Common options

All commands accept:

- `-p PATH` / `--path PATH` — operate on a repo at a specific path instead of `cwd`
- `--log-level LEVEL` — set logging verbosity (e.g. `DEBUG`, `INFO`, `WARNING`)

## Testing

```sh
uv tool run --with pytest pytest
```
