#!/usr/bin/bash
# One literal argument per line; no shell expansion or evaluation.
set -e
flags=()
flags_file="${XDG_CONFIG_HOME:-$HOME/.config}/chatgpt-flags.conf"
if [[ -r $flags_file ]]; then
  while IFS= read -r flag || [[ -n $flag ]]; do
    flag=${flag%$'\r'}
    flag="${flag#"${flag%%[![:space:]]*}"}"
    flag="${flag%"${flag##*[![:space:]]}"}"
    [[ -z $flag || $flag == \#* ]] && continue
    flags+=("$flag")
  done < "$flags_file"
fi
launcher_dir=$(dirname -- "$(readlink -f -- "$0")")
exec "$launcher_dir/ChatGPT" "${flags[@]}" "$@"
