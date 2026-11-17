#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
release_version=$(python scripts/check_version.py)
release_directory="dist/$release_version"
(cd apps/studio && npm ci && npm run build && npm test)
python -m build --outdir "$release_directory"
python -m twine check "$release_directory"/*.whl "$release_directory"/*.tar.gz
python - "$release_directory" <<'PY'
import hashlib
from pathlib import Path
import sys
root=Path(sys.argv[1])
files=sorted([*root.glob('*.whl'),*root.glob('*.tar.gz')])
(root/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files))
PY
