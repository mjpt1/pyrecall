# Launch kit (48-hour window)

Goal: compress attention into ~48 hours so star velocity can hit GitHub Trending (especially **Python**).

Repo: https://github.com/mjpt1/pyrecall  
Install: `pip install pyrecall-cli`  
CLI: `pyrecall`

Do **not** spread posts across a week. Same day is better.

---

## Pre-flight (15 minutes)

- [ ] README demo image loads on GitHub
- [ ] `pip install pyrecall-cli && pyrecall --help` works on a clean machine/venv
- [ ] CI badge is green
- [ ] Topics set: `python`, `cli`, `pytest`, `developer-tools`, `project-memory`, …
- [ ] You are logged into Hacker News, Reddit, and X/Twitter

---

## Hour 0–6 — niche communities

### Reddit (pick 2–3, do not spam identical text)

**r/Python** — title:

```
PyRecall: local project memory that learns from your corrections (pytest/pathlib/typing)
```

Body:

```
I got tired of re-explaining the same project conventions every session.

PyRecall keeps a local SQLite store in `.pyrecall/`, turns corrections into reusable skills, and serves them back via CLI or a stdio tool bridge.

Install:
pip install pyrecall-cli

Quick start:
pyrecall init
pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures"
pyrecall recall "how should tests be written"

No cloud account for recall. MIT.
https://github.com/mjpt1/pyrecall
```

**r/commandline** / **r/opensource** — shorter:

```
Title: pyrecall — local CLI memory for Python project conventions

Body:
Local-only CLI that stores project decisions and learns from corrections (rejected → preferred → skill). BM25 recall, stdio tool bridge, seeded pytest/pathlib defaults.

pip install pyrecall-cli
https://github.com/mjpt1/pyrecall
```

---

## Hour 6–12 — Hacker News

**Show HN title (≤80 chars):**

```
Show HN: PyRecall – local memory that learns Python project corrections
```

**Text:**

```
PyRecall is a small local tool for Python repos.

Problem: you correct the same mistake twice ("use pytest, not unittest") and the next session forgets.

What it does:
- stores decisions/conventions in .pyrecall/ (SQLite)
- turns corrections into reusable skills
- recalls them with local BM25 ranking
- optional stdio JSON-RPC bridge for coding tools

pip install pyrecall-cli
pyrecall init && pyrecall learn --blob "os.path.join => Path / 'name'"

No network calls for recall. MIT.
https://github.com/mjpt1/pyrecall
```

Post at: https://news.ycombinator.com/submit  
Type: **Show HN**

Reply early to comments. Link the demo image / quick start if asked.

---

## Hour 12–24 — X / Twitter thread

```
1/ PyRecall is out.

Local project memory for Python workflows.
Learns from corrections. Stays on your disk.

pip install pyrecall-cli
https://github.com/mjpt1/pyrecall

2/ You correct once:

pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures"

Next time you ask how tests should be written, it recalls the skill.

3/ Also:
• indexes docs + Python signals
• stdio tool bridge for compatible coding tools
• zero network for recall
• MIT

Star if useful → helps others find it.
```

Attach the README demo PNG (`docs/demo.png`) to tweet 1.

---

## Hour 24–36 — follow-ups

- [ ] Post metrics reply: “X stars in 24h” (only if true)
- [ ] Cross-post a short Dev.to / Hashnode article from README “Why” section
- [ ] Submit to awesome-python / awesome-cli lists (PR), only if rules allow

**Dev.to title:**

```
Local project memory for Python: learn from corrections once
```

---

## Hour 36–48 — secondary channels

- [ ] Persian / local communities if relevant (same facts, your voice)
- [ ] LinkedIn short post (optional)
- [ ] Email 3–5 newsletters only **after** you are on Trending or have clear traction

---

## One-liner (everywhere)

```
Local project memory for Python — learn from corrections, recall conventions. pip install pyrecall-cli
```

---

## Do / Don't

**Do**
- Answer every serious question in the first 12 hours
- Keep claims accurate (local, no network for recall, MIT)
- Point people to `docs/BRIDGE.md` for host wiring

**Don't**
- Buy stars
- Copy-paste the exact same body to 10 subreddits in 10 minutes
- Promise “best coding agent” or cloud magic you do not ship

---

## After launch

1. Watch https://github.com/trending/python?since=daily
2. If you hit Trending, screenshot it and use it in follow-up posts
3. Then set up GitHub Sponsors (next step in the checklist)
