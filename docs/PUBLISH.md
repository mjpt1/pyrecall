# Publishing to PyPI

Distribution name on PyPI: **`py-recall`**  
Import / CLI name: **`pyrecall`**

```bash
pip install py-recall
pyrecall --help
```

## Status

| Piece | Status |
|-------|--------|
| GitHub workflow `publish.yml` | Ready |
| GitHub environment `pypi` | Ready |
| PyPI Trusted Publisher | **Needs one-time setup in your PyPI account** |
| First upload of `py-recall` | Blocked until publisher exists |

Last failure reason: `invalid-publisher` — no matching publisher on PyPI for  
`repo:mjpt1/pyrecall:environment:pypi`.

## One-time setup (you must click this)

1. Log in: https://pypi.org/account/login/
2. Open: https://pypi.org/manage/account/publishing/
3. Under **Add a new pending publisher**, enter **exactly**:

| Field | Value |
|-------|-------|
| PyPI Project Name | `py-recall` |
| Owner | `mjpt1` |
| Repository | `pyrecall` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

4. Click **Add**.

## After you add the publisher

Tell the maintainer / re-run:

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

Use a PyPI API token (create at https://pypi.org/manage/account/token/).
