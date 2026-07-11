# Connect the stdio tool bridge

PyRecall can run as a local **stdio tool server**. Compatible coding tools start it as a subprocess, talk JSON-RPC over stdin/stdout, and call tools like `get_context` or `learn_correction`.

No network. The server only reads/writes the `.pyrecall/` store in the project you point it at.

## 1. Install and initialize the project

```bash
pip install pyrecall-cli
cd /path/to/your/python-project
pyrecall init
pyrecall index
```

Confirm the CLI works:

```bash
pyrecall stats
pyrecall recall "pytest"
```

## 2. Smoke-test the bridge

In one terminal:

```bash
pyrecall serve
```

The process waits on stdin. That is expected. Stop it with `Ctrl+C`.

If `pyrecall` is not on `PATH`, use the module form everywhere below:

```bash
python -m pyrecall serve
```

## 3. Add a host config

Point the host at your **project root** (the folder that contains `.pyrecall/`), not the PyRecall source repo unless that is the project you care about.

### Minimal shape

Most hosts expect something like:

```json
{
  "pyrecall": {
    "command": "pyrecall",
    "args": ["serve"],
    "cwd": "/absolute/path/to/your/python-project"
  }
}
```

Windows example:

```json
{
  "pyrecall": {
    "command": "pyrecall",
    "args": ["serve"],
    "cwd": "C:\\Users\\you\\projects\\myapp"
  }
}
```

If the host needs an explicit interpreter:

```json
{
  "pyrecall": {
    "command": "python",
    "args": ["-m", "pyrecall", "serve"],
    "cwd": "/absolute/path/to/your/python-project"
  }
}
```

Ready-made snippets:

| File | Use |
|------|-----|
| [examples/bridge.client.json](../examples/bridge.client.json) | Generic `toolServers` map |
| [examples/bridge.mcp.json](../examples/bridge.mcp.json) | Common `mcpServers`-style map |
| [examples/bridge.windows.json](../examples/bridge.windows.json) | Windows paths + `python -m` |

After editing the host config, **restart the host tool** so it reloads servers.

## 4. What the host can call

| Tool | When to use it |
|------|----------------|
| `get_context` | Before editing — paste-ready conventions + skills (includes why matched) |
| `search_memory` | Structured search; optional `tags` filter |
| `learn_correction` | User said “don’t do X, do Y instead” — persist it |
| `add_memory` | Save a decision / convention / note |
| `list_skills` | Inspect active skills |
| `install_pack` | Install fastapi / django / sqlalchemy / ruff conventions |
| `harvest_docs` | Import convention bullets from README / CONTRIBUTING / AGENTS |
| `project_stats` | Quick health check of the local store |

### Suggested workflow inside a session

1. Call `get_context` with a short task description (`"add pytest for pathlib helpers"`).
2. Do the work using that context.
3. If the user corrects the approach, call `learn_correction` with `rejected` + `preferred`.
4. Next session, `get_context` / `search_memory` will surface that skill.

Also run `pyrecall setup-host` once so `.pyrecall/HOST_RULES.md`, bridge JSON, and an `AGENTS.md` section document the same loop. Use `pyrecall harvest` after editing project docs. Keep `pyrecall watch` running in a side terminal if docs/config change often.

### Example `learn_correction` arguments

```json
{
  "rejected": "unittest.TestCase",
  "preferred": "pytest assert + fixtures",
  "reason": "Repo standard",
  "context": "tests for pathlib helpers"
}
```

Or free-form:

```json
{
  "blob": "os.path.join => Path / 'name'"
}
```

## 5. Verify from the host

After reconnecting:

1. Call `project_stats` — you should see non-zero `skills` after `pyrecall init`.
2. Call `get_context` with query `"pytest"`.
3. Call `learn_correction`, then `list_skills` — the new skill should appear.

If those three work, the bridge is wired correctly.

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Host says command not found | Use `"command": "python", "args": ["-m", "pyrecall", "serve"]` or put Scripts/`bin` on `PATH` |
| Empty stats / no skills | Wrong `cwd` — must be the project with `.pyrecall/`. Run `pyrecall init` there |
| Server starts then exits | Run `pyrecall serve` manually and check for traceback; ensure Python ≥ 3.10 |
| Changes not visible | Restart the host after config edits; confirm you are in the same project directory |
| Windows path issues | Prefer escaped backslashes `C:\\...` or forward slashes `C:/...` |

## 7. Security notes

- The bridge can read project files only through the indexed/store APIs you already use via CLI.
- It does not open outbound network connections for recall.
- Keep `.pyrecall/store.db` out of public clones if it contains private decisions — use `pyrecall export` for reviewable backups instead.
