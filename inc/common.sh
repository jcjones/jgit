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
    #
    # or
    #
    command = ""
EOF
}

_git_is_key_set() {
    local key
    key="${1}"
    git config --get "${key}" >/dev/null
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

-e COMMAND     Run the command on the remote host after a successful jgit-push.
EOF
    exit 1
}

common_setup_env() {
    REPO_DIR=$(git rev-parse --show-toplevel)
    BRANCH_LIST=${REPO_DIR}/.git/jgit-branches
    _git_get_conf_to_env GITREMOTE "jgit.default"
    _git_get_conf_to_env TRACK_BRANCH "jgit.${GITREMOTE}.tracking-branch" "origin/main"

    if _git_is_key_set "jgit.${GITREMOTE}.command" ; then
        _git_get_conf_to_env MK_COMMAND "jgit.${GITREMOTE}.command"
    else
        _git_get_conf_to_env REMOTE_DIR "jgit.${GITREMOTE}.remote-dir"
        _git_get_conf_to_env REMOTE_CHECKOUT_BRANCH "jgit.${GITREMOTE}.remote-checkout-branch" "main"
        _git_get_conf_to_env REMOTE_NAME_ON_DIR "jgit.${GITREMOTE}.remote-name-on-remote-dir"
        _git_get_conf_to_env SSHREMOTE "jgit.${GITREMOTE}.ssh-hostname"
    fi

    [ -r "${BRANCH_LIST}" ] || {
        info "Couldn't find ${BRANCH_LIST} branch list file, creating a default"
        touch "${BRANCH_LIST}"
    }

    while getopts "e:h" opt; do
      case "${opt}" in
        e) export RUN_EXTRA_CMD="${OPTARG}";;
        h | *) _usage;;
      esac
    done
}

_run_extra_cmd() {
    ssh -t "${SSHREMOTE}" -- "cd ${REMOTE_DIR}; ${RUN_EXTRA_CMD}"
}

common_complete_push() {
    [ -n "${RUN_EXTRA_CMD:-}" ] && _run_extra_cmd
}

branch_apparently_merged() {
    branch_name="${1}"

    if [[ "${branch_name}" =~ (IN-0000) ]] ; then
       echo "# ${branch_name} is a WIP branch"
       return 1
    fi

    if git branch -r | grep "${GITREMOTE}/${branch_name}" >/dev/null ; then
        echo "# Found ${branch_name} in origin branches, probably not merged"
        return 1
    fi

    if [[ "${branch_name}" =~ (IN-[0-9]+) ]] ; then
        ticket_number="${BASH_REMATCH[1]}"

        if git log -n 500 ${TRACK_BRANCH} | grep "${ticket_number}" >/dev/null 2>&1 ; then
            echo "# Found ${ticket_number} in git log, probably merged"
            return 0
        fi
    fi

    # Get the patch-id of the diff of the squash
    patch_id=$(git diff "$(git merge-base "${TRACK_BRANCH}" "${branch_name}")" "${branch_name}" \
        | git patch-id --stable | cut -d' ' -f1)
    result="$(git rev-list "${branch_name}..${TRACK_BRANCH}" | while read -r line ; do
            other_patch_id="$(git diff ${line}~ ${line} | git patch-id --stable | cut -d' ' -f1)"
            if [[ "${patch_id}" = "${other_patch_id}" ]]; then
                echo "${line}"
                exit 0
            fi
        done
    )"

    if [ -n "${result}" ]; then
        echo "# Found squash merge at revision ${result}"
        return 0
    fi

    return 1
}
