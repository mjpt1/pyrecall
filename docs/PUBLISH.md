# Publishing to PyPI

Distribution name on PyPI: **`py-recall`**  
Import / CLI name: **`pyrecall`**

```bash
pip install py-recall
pyrecall --help
```

## One-time setup

1. Create an account at [pypi.org](https://pypi.org/account/register/).
2. Enable 2FA.
3. Prefer **Trusted Publishing** (no long-lived token):
   - PyPI → Your projects → Publishing → Add a new pending publisher
   - Owner: `mjpt1`
   - Repository: `pyrecall`
   - Workflow: `publish.yml`
   - Environment: `pypi`
4. On GitHub: Settings → Environments → create `pypi` (optional protection rules).

## Local build check

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
```

## Publish

### Recommended: GitHub Release

1. Bump `version` in `pyproject.toml`.
2. Push a tag: `git tag v0.1.0 && git push origin v0.1.0`
3. Create a GitHub Release for that tag — `publish.yml` builds and uploads to PyPI.

### Manual (API token)

```bash
python -m build
twine upload dist/*
```

Use a PyPI API token with permission limited to the `py-recall` project.
