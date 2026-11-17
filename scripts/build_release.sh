#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
(cd apps/studio && npm ci && npm run build && npm test)
python -m build
python -m twine check dist/*
