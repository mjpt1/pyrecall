# Reproduce the README demo session in a throwaway directory (Windows PowerShell).
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Demo = Join-Path ([System.IO.Path]::GetTempPath()) ("pyrecall-demo-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Demo | Out-Null
Push-Location $Demo
try {
    python -m pip install -e "$Root" -q
    New-Item -ItemType Directory -Path src, tests | Out-Null
    Set-Content -Path README.md -Value "# Demo`nUse pytest for tests.`n"
    Set-Content -Path src/app.py -Value "def add(a: int, b: int) -> int:`n    return a + b`n"

    Write-Host '$ pyrecall init'
    pyrecall init
    Write-Host ''
    Write-Host '$ pyrecall index'
    pyrecall index
    Write-Host ''
    Write-Host '$ pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures" --reason "Repo standard"'
    pyrecall learn --rejected "unittest.TestCase" --preferred "pytest assert + fixtures" --reason "Repo standard"
    Write-Host ''
    Write-Host '$ pyrecall recall "how should tests be written"'
    pyrecall recall "how should tests be written"
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $Demo
}
