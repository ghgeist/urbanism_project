#!/bin/bash
# Runs after a task is merged. Re-syncs frontend deps so the dev server
# picks up any package.json changes from the merged task. Backend deps
# are managed via the package management tool, not this script.
set -e

if [ -f frontend/package.json ]; then
  (cd frontend && npm install --no-audit --no-fund --prefer-offline)
fi
