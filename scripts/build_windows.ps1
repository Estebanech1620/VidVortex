Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

# Prefer `python` on PATH (matches actions/setup-python on CI); `py -3` can point at a different install without deps.
if (Get-Command python -ErrorAction SilentlyContinue) {
  $python = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $python = "py -3"
} else {
  throw "Python was not found on PATH."
}

function Invoke-VidVortexPython {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  if ($python -eq "py -3") {
    & py -3 @Args
  } else {
    & $python @Args
  }
}

Write-Host "[VidVortex] Installing build dependencies..."
Invoke-VidVortexPython -Args @("-m", "pip", "install", "--upgrade", "pip")
Invoke-VidVortexPython -Args @("-m", "pip", "install", "-r", "requirements-desktop.txt")

$distDir = Join-Path $repoRoot "dist\windows"
if (Test-Path $distDir) {
  Remove-Item $distDir -Recurse -Force
}
New-Item -ItemType Directory -Path $distDir | Out-Null

if (-not (Test-Path "app_logo.ico")) {
  if (Test-Path "app_logo.png") {
    Write-Host "[VidVortex] Generating app_logo.ico from app_logo.png..."
    $icoGen = @"
from PIL import Image
img = Image.open('app_logo.png').convert('RGBA')
img.save(
    'app_logo.ico',
    format='ICO',
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
"@
    Invoke-VidVortexPython -Args @("-c", $icoGen)
  } else {
    throw "Missing branding assets: need app_logo.ico in the application repo root (or app_logo.png to generate it)."
  }
}

if (-not (Test-Path "app_logo.ico")) {
  throw "app_logo.ico was not created. Check app_logo.png and Pillow install."
}

Write-Host "[VidVortex] Building Windows executable..."
Invoke-VidVortexPython -Args @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--name", "VidVortex",
  "--onefile",
  "--windowed",
  "--distpath", $distDir,
  "--icon", "app_logo.ico",
  "--add-data", "yt-dlp.conf.example;.",
  "--add-data", "profiles.json.example;.",
  "--add-data", "queue.json.example;.",
  "--add-data", "app_logo.ico;.",
  "--collect-all", "ttkbootstrap",
  "vidvortex_app.py"
)

$exePath = Join-Path $distDir "VidVortex.exe"
if (-not (Test-Path $exePath)) {
  throw "Build completed but executable was not found at $exePath"
}

Write-Host "[VidVortex] Windows package ready: $exePath"

# Zip for GitHub Releases: exe + setup (Windows has no RUN_FIRST launcher; use setup_windows.bat then VidVortex.exe)
$pkgDir = Join-Path $repoRoot "package\windows"
if (Test-Path $pkgDir) {
  Remove-Item $pkgDir -Recurse -Force
}
New-Item -ItemType Directory -Path $pkgDir | Out-Null

Copy-Item $exePath (Join-Path $pkgDir "VidVortex.exe")
Copy-Item (Join-Path $repoRoot "scripts\setup_windows.bat") (Join-Path $pkgDir "setup_windows.bat")

$distOut = Join-Path $repoRoot "dist"
if (-not (Test-Path $distOut)) {
  New-Item -ItemType Directory -Path $distOut | Out-Null
}
$zipPath = Join-Path $distOut "VidVortex-windows.zip"
if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $pkgDir "*") -DestinationPath $zipPath

Write-Host "[VidVortex] Release zip (same layout as CI): $zipPath"
