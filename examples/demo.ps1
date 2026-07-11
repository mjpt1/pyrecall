# ~30 second learn -> recall demo (throwaway directory).
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Demo = Join-Path ([System.IO.Path]::GetTempPath()) ("pyrecall-demo-" + [guid]::NewGuid().ToString("N"))
$Fast = $env:PYRECALL_DEMO_FAST -eq "1"
function Pause-Demo([int]$Seconds = 1) {
    if (-not $Fast) { Start-Sleep -Seconds $Seconds }
}
New-Item -ItemType Directory -Path $Demo | Out-Null
Push-Location $Demo
try {
    $env:PYTHONPATH = (Join-Path $Root "src")
    New-Item -ItemType Directory -Path src, tests | Out-Null
    @"
# Demo
## Testing
- Prefer pytest with plain assert and fixtures
- Keep unit tests free of network calls
"@ | Set-Content -Path README.md -Encoding utf8
    @"
# Contributing
## Style
- Prefer pathlib over os.path for new filesystem code
- Do not use bare except
"@ | Set-Content -Path CONTRIBUTING.md -Encoding utf8
    "def add(a: int, b: int) -> int:`n    return a + b`n" | Set-Content -Path src/app.py -Encoding utf8

    Write-Host "=== PyRecall 30s demo ==="
    Write-Host ""
    Write-Host "1) init + harvest docs"
    Pause-Demo 1
    python -m pyrecall init
    python -m pyrecall harvest
    Write-Host ""
    Write-Host "2) learn a correction"
    Pause-Demo 1
    python -m pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures" --reason "Repo standard"
    Write-Host ""
    Write-Host "3) recall - skill should surface"
    Pause-Demo 1
    python -m pyrecall recall "how should tests be written"
    Write-Host ""
    Write-Host "=== done: correction became durable memory ==="
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $Demo -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
}
