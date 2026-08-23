#!/usr/bin/env sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
PYTHONPATH=src python3 -m retail_analytics --report "$@"

