# Publishing to PyPI

Distribution name on PyPI: **`pyrecall-cli`**  
Import / CLI name: **`pyrecall`**

> Why not `pyrecall` / `py-recall`? PyPI treats hyphen/underscore as the same
> normalized name. `pyrecall` is already taken, so `py-recall` is rejected as
> "too similar".

```bash
pip install pyrecall-cli
pyrecall --help
```

## Status

| Piece | Status |
|-------|--------|
| GitHub workflow `publish.yml` | Ready |
| GitHub environment `pypi` | Ready |
| PyPI Trusted Publisher | Add pending publisher for `pyrecall-cli` |
| First upload | After publisher is added |

## One-time setup

1. Log in: https://pypi.org/account/login/
2. Open: https://pypi.org/manage/account/publishing/
3. Under **Add a new pending publisher**, enter **exactly**:

| Field | Value |
|-------|-------|
| PyPI Project Name | `pyrecall-cli` |
| Owner | `mjpt1` |
| Repository | `pyrecall` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

4. Click **Add**.

## After you add the publisher

```bash
gh run rerun 29109465401 --failed
```

Or:

```bash
gh workflow run publish.yml
```

## Local build check

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
```

## Manual upload (API token fallback)

```bash
python -m build
twine upload dist/*
```
