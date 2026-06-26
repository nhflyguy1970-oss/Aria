#!/usr/bin/env bash
# Deprecated alias — use launch-jarvis.sh (same behavior, includes launch lock).
exec "$(cd "$(dirname "$0")" && pwd)/launch-jarvis.sh" "$@"
