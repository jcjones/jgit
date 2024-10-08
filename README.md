## What this does

When you use `jgit-push`, it:

1. Creates a temporary branch `dev` based on `tracking-branch`
1. For each branch name in ${REPO_DIR}/.git/jgit-branches:
	1. Merge that branch into `dev`
1. Shell into a remote host at `ssh-hostname`, and there:
	1. Change to the `remote-dir`
	1. `git stash push` any local changes
	1. Run `git fetch` on `remote-name-on-remote-dir`
	1. Checkout `dev` from `remote-name-on-remote-dir`
	1. `git stash pop` the local changes back
1. Cleanup the `dev` temporary branch
1. Return to the original branch

## Installation

### Dependencies
Install [gum](https://github.com/charmbracelet/gum) into your path.

### Installation
Add the scripts in `bin/` to your path, one way or another. Add to your `${PATH},` or symlink into your `${HOME}/bin`, whatever.

Then in each Git repo, configure the script inside your `git config -e`. Add sections like the following:

```toml
[jgit]
    default = proxmox
[jgit "proxmox"]
    ssh-hostname = proxmox.internal
    remote-dir = /srv/nfs/DevEnv
    remote-name-on-remote-dir = proxmox
    # The following options are optional, they have the listed defaults
	remote-checkout-branch = main
    tracking-branch = origin/main
```

In this case:
- `default`: The jgit block to use.
- `ssh-hostname`: The host the script will `ssh` into.
- `remote-dir`: The directory of the checkout on `ssh-hostname`.
- `remote-name-on-remote-dir`: The `remote` name used during a `git fetch` while in `remote-dir` on `ssh-hostname`.
- `remote-checkout-branch`: The branch name for the remote checkout, defaults to `main`
- `tracking-branch`: The branch to base `dev` on, defaults to `origin/main`

