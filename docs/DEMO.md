# 30-second demo recording

Record a short terminal clip (about 30–45 seconds) that shows **learn → recall**.

## Script

From the repo root:

```powershell
# Windows
$env:PYRECALL_DEMO_FAST = "1"   # optional: skip pauses while practicing
./examples/demo.ps1
```

```bash
# Unix
PYRECALL_DEMO_FAST=1 bash examples/demo.sh
```

For the public recording, leave `PYRECALL_DEMO_FAST` unset so the three beats are readable.

## Beats to capture

1. `init` + `harvest` — docs become memories  
2. `learn` — correction becomes a skill  
3. `recall "how should tests be written"` — skill surfaces with a `why:` line  

## Tips

- Use a large font / 120×30 terminal.
- Crop to the three command blocks; cut pip noise if any.
- Upload as a GitHub release asset or GIF and link from the README hero if you replace `docs/demo.png`.
