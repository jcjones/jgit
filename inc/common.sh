#!/bin/bash
# This file should be included, not run on its own
set -euf

error() {
    if hash gum; then
        gum style --border=rounded --foreground="#FF0000" "${*}"
    else
        echo "[ERROR] ${*}"
    fi
}

info() {
    if hash gum; then
        gum style --border=rounded --foreground="#00FF00" "${*}"
    else
        echo "[INFO] ${*}"
    fi
}

notify() {
    case $(uname) in
        "Darwin")
            osascript -e "display notification \"Complete\" with title \"${*}\"";;
        "Linux")
            notify-send "${*}";;
        *)
            echo "[NOTIFICATION] ${*}"
    esac
}

_setup_help() {
    cat <<EOF
Your git config is missing parameters. You'll want to add sections like:
[jgit]
    default = proxmox
[jgit "proxmox"]
    ssh-hostname = proxmox.internal
    remote-dir = /srv/nfs/DevEnv
    remote-name-on-remote-dir = proxmox
    # These are optional, with these defaults:
    # remote-checkout-branch = main
    # tracking-branch = origin/main
EOF
}

_git_get_conf_to_env() {
    local outvar key
    outvar="${1}"
    key="${2}"
    default="${3:-}"
    if ! output="$(git config --get "${key}")"; then
        output="${default}"
    fi
    if [ -z "${output}" ] ; then
        error "No results for Git key ${key}"
        _setup_help
        exit 99
    fi
    export "${outvar}"="${output}"
}

_usage() {
    cat <<EOF
${0} [-e]

-e      Run the command in jgit.${GITREMOTE}.remote_after_push_cmd on the remote
        host after a successful jgit-push.
EOF
    exit 1
}

common_setup_env() {
    REPO_DIR=$(git rev-parse --show-toplevel)
    BRANCH_LIST=${REPO_DIR}/.git/jgit-branches
    _git_get_conf_to_env GITREMOTE "jgit.default"
    _git_get_conf_to_env TRACK_BRANCH "jgit.${GITREMOTE}.tracking-branch" "origin/main"
    _git_get_conf_to_env REMOTE_DIR "jgit.${GITREMOTE}.remote-dir"
    _git_get_conf_to_env REMOTE_CHECKOUT_BRANCH "jgit.${GITREMOTE}.remote-checkout-branch" "main"
    _git_get_conf_to_env REMOTE_NAME_ON_DIR "jgit.${GITREMOTE}.remote-name-on-remote-dir"
    _git_get_conf_to_env SSHREMOTE "jgit.${GITREMOTE}.ssh-hostname"

    [ -r "${BRANCH_LIST}" ] || {
        info "Couldn't find ${BRANCH_LIST} branch list file, creating a default"
        touch "${BRANCH_LIST}"
    }

    while getopts "eh" opt; do
      case "${opt}" in
        e) export COMMON_RUN_EXTRA_CMD=1;;
        h | *) _usage;;
      esac
    done
}

_run_extra_cmd() {
    _git_get_conf_to_env REMOTE_POST_PUSH_CMD "jgit.${GITREMOTE}.remote_after_push_cmd"
    ssh "${SSHREMOTE}" -- "${REMOTE_POST_PUSH_CMD}"
}

common_complete_push() {
    [ -n "${COMMON_RUN_EXTRA_CMD:-}" ] && _run_extra_cmd
}
