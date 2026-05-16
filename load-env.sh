#!/bin/bash
# Usage: source load-env.sh [filename]

file="${1:-.env}"

if [ -f "$file" ]; then
  # Export variables from .env, ignoring comments and empty lines
  export $(grep -v '^#' "$file" | xargs)
  echo "[OK] Environment variables from ${file} exported to current shell."
else
  echo "[ERROR] $file file not found."
fi
