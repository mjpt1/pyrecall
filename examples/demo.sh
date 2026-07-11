#!/usr/bin/env bash
# ~30 second learn → recall demo (throwaway directory).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO="$(mktemp -d "${TMPDIR:-/tmp}/pyrecall-demo.XXXXXX")"
FAST="${PYRECALL_DEMO_FAST:-0}"
pause() { if [ "$FAST" != "1" ]; then sleep "${1:-1}"; fi; }
cleanup() { rm -rf "$DEMO"; }
trap cleanup EXIT

cd "$DEMO"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p src tests
cat > README.md <<'EOF'
# Demo
## Testing
- Prefer pytest with plain assert and fixtures
- Keep unit tests free of network calls
EOF
cat > CONTRIBUTING.md <<'EOF'
# Contributing
## Style
- Prefer pathlib over os.path for new filesystem code
- Do not use bare except
EOF
cat > src/app.py <<'EOF'
def add(a: int, b: int) -> int:
    return a + b
EOF

echo "=== PyRecall 30s demo ==="
echo
echo "1) init + harvest docs"
pause 1
python -m pyrecall init
python -m pyrecall harvest
echo
echo "2) learn a correction"
pause 1
python -m pyrecall learn \
  --rejected "unittest.TestCase" \
  --preferred "pytest assert + fixtures" \
  --reason "Repo standard"
echo
echo "3) recall — skill should surface"
pause 1
python -m pyrecall recall "how should tests be written"
echo
echo "=== done: correction became durable memory ==="
