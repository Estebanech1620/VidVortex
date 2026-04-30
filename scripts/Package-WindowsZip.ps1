Set-StrictMode -Version Latest

function Publish-VidVortexWindowsZip {
  param(
    [Parameter(Mandatory)][string]$RepoRoot,
    [Parameter(Mandatory)][string]$ExePath
  )
  if (-not (Test-Path -LiteralPath $ExePath)) {
    throw "Executable not found: $ExePath"
  }
  $setupBat = Join-Path $RepoRoot "scripts\setup_windows.bat"
  if (-not (Test-Path -LiteralPath $setupBat)) {
    throw "Missing scripts\setup_windows.bat under $RepoRoot"
  }

  $pkgDir = Join-Path $RepoRoot "package\windows"
  if (Test-Path $pkgDir) {
    Remove-Item $pkgDir -Recurse -Force
  }
  New-Item -ItemType Directory -Path $pkgDir | Out-Null

  Copy-Item -LiteralPath $ExePath -Destination (Join-Path $pkgDir "VidVortex.exe")
  Copy-Item -LiteralPath $setupBat -Destination (Join-Path $pkgDir "setup_windows.bat")

  $distOut = Join-Path $RepoRoot "dist"
  if (-not (Test-Path $distOut)) {
    New-Item -ItemType Directory -Path $distOut | Out-Null
  }
  $zipPath = Join-Path $distOut "VidVortex-windows.zip"
  if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
  }
  Compress-Archive -Path (Join-Path $pkgDir "*") -DestinationPath $zipPath

  Write-Host "[VidVortex] Release zip (same layout as CI): $zipPath"
}
