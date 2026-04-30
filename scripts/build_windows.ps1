Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

if (Get-Command py -ErrorAction SilentlyContinue) {
  $python = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $python = "python"
} else {
  throw "Python was not found on PATH."
}

Write-Host "[VidVortex] Installing build dependencies..."
Invoke-Expression "$python -m pip install --upgrade pip"
Invoke-Expression "$python -m pip install -r requirements-desktop.txt"

$distDir = Join-Path $repoRoot "dist\windows"
if (Test-Path $distDir) {
  Remove-Item $distDir -Recurse -Force
}
New-Item -ItemType Directory -Path $distDir | Out-Null

$iconArg = ""
if (Test-Path "app_logo.ico") {
  $iconArg = "--icon app_logo.ico"
}

Write-Host "[VidVortex] Building Windows executable..."
Invoke-Expression "$python -m PyInstaller --noconfirm --clean --name VidVortex --onefile --windowed --distpath ""$distDir"" $iconArg --add-data ""yt-dlp.conf.example;."" --add-data ""profiles.json.example;."" --add-data ""queue.json.example;."" --collect-all ttkbootstrap vidvortex_app.py"

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
