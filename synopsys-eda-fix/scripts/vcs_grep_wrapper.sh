#!/usr/bin/env bash
# Normalize legacy VCS grep syntax without changing the system grep tools.
set -u

case "${0##*/}" in
    grep)  grep_mode=() ;;
    egrep) grep_mode=(-E) ;;
    *)
        printf 'vcs-grep: unsupported entry name: %s\n' "${0##*/}" >&2
        exit 2
        ;;
esac

normalized_args=()
for arg in "$@"; do
    # GNU grep 3.12 warns about the old VCS spelling "\-". Spell the
    # literal hyphen as "[-]" so a pattern that begins with it cannot be
    # mistaken for another grep option.
    normalized_args+=("${arg//\\-/[-]}")
done

exec /usr/bin/grep "${grep_mode[@]}" "${normalized_args[@]}"
