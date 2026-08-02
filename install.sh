#!/usr/bin/env sh
set -eu

archive_url="https://github.com/claudneysessa/ctx404/archive/refs/heads/main.tar.gz"
temp_root="$(mktemp -d 2>/dev/null || mktemp -d -t ctx404)"

cleanup() {
  rm -rf -- "$temp_root"
}
trap cleanup EXIT HUP INT TERM

curl -fsSL "$archive_url" | tar -xz -C "$temp_root"
set -- "$temp_root"/*
repository_root="$1"

if [ ! -d "$repository_root" ]; then
  echo "CTX404 archive did not contain a repository directory." >&2
  exit 1
fi

python "$repository_root/scripts/install.py" --force
