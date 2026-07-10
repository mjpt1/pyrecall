#!/usr/bin/env bash
# Reproduce the README demo session in a throwaway directory.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO="$(mktemp -d "${TMPDIR:-/tmp}/pyrecall-demo.XXXXXX")"
cleanup() { rm -rf "$DEMO"; }
trap cleanup EXIT

cd "$DEMO"
python -m pip install -e "$ROOT" -q
mkdir -p src tests
cat > README.md <<'EOF'
# Demo
Use pytest for tests.
EOF
cat > src/app.py <<'EOF'
"""Demo app."""

def add(a: int, b: int) -> int:
    return a + b
EOF

echo "$ pyrecall init"
pyrecall init
echo
echo "$ pyrecall index"
pyrecall index
echo
echo "$ pyrecall learn --rejected \"unittest.TestCase\" --preferred \"pytest assert + fixtures\" --reason \"Repo standard\""
pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures" --reason "Repo standard"
echo
echo "$ pyrecall recall \"how should tests be written\""
pyrecall recall "how should tests be written"
