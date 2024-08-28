#!/bin/bash
# This file should be included, not run on its own
set -euf

error() {
    gum style --border=rounded --foreground="#FF0000" "${*}"
}

info() {
    gum style --border=rounded --foreground="#00FF00" "${*}"
}

notify() {
    case $(uname) in
        "Darwin")
            osascript -e "display notification \"Complete\" with title \"${*}\"";;
        "Linux")
            notify-send "${*}";;
    esac
}

_setup_help() {
    cat <<EOF
Your git config is missing parameters. You'll want to add sections like:
[upsalt]
    default = proxmox
[upsalt "proxmox"]
    ssh-hostname = proxmox.internal
    remote-dir = /srv/nfs/DevEnv
    remote-name-on-remote-dir = proxmox
    tracking-branch = origin/main
EOF
}

_git_get_conf_to_env() {
    local outvar key
    outvar="${1}"
    key="${2}"
    if ! output="$(git config --get "${key}")"; then
        error "Couldn't get Git key ${key}"
        _setup_help
        exit 99
    fi
    if [ -z "${output}" ] ; then
        echo "No results for Git key ${key}"
        _setup_help
        exit 99
    fi
    export ${outvar}="${output}"
}

common_setup_env() {
    if ! hash gum ; then
        error "Missing gum, please install it"
        exit 99
    fi

    REPO_DIR=$(git rev-parse --show-toplevel)
    BRANCH_LIST=${REPO_DIR}/.git/jgit-branches
    _git_get_conf_to_env GITREMOTE "jgit.default"
    _git_get_conf_to_env TRACK_BRANCH "jgit.${GITREMOTE}.tracking-branch"
    _git_get_conf_to_env REMOTE_DIR "jgit.${GITREMOTE}.remote-dir"
    _git_get_conf_to_env REMOTE_NAME_ON_DIR "jgit.${GITREMOTE}.remote-name-on-remote-dir"
    _git_get_conf_to_env SSHREMOTE "jgit.${GITREMOTE}.ssh-hostname"

    [ -r "${BRANCH_LIST}" ] || {
        info "Couldn't find ${BRANCH_LIST} branch list file, creating a default"
        touch "${BRANCH_LIST}"
    }
}
