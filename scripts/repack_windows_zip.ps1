Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "Package-WindowsZip.ps1")

$exe = $null
if ($args.Count -ge 1 -and $args[0]) {
  $exe = $args[0]
}
if (-not $exe) {
  foreach ($c in @(
      (Join-Path $repoRoot "dist\windows\VidVortex.exe"),
      (Join-Path $repoRoot "app\VidVortex.exe")
    )) {
    if (Test-Path -LiteralPath $c) {
      $exe = $c
      break
    }
  }
}

if (-not $exe) {
  throw @"
VidVortex.exe not found. Do one of the following:
  - Run a full build from the application checkout (see CI / scripts\build_windows.ps1).
  - Or repack using an existing exe:
      .\scripts\repack_windows_zip.ps1 path\to\VidVortex.exe
"@
}

Set-Location $repoRoot
Publish-VidVortexWindowsZip -RepoRoot $repoRoot -ExePath $exe
