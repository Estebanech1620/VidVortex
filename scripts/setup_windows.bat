@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo [VidVortex] Windows dependency setup starting...

call :ENSURE_PYTHON
if errorlevel 1 exit /b 1

call :INSTALL_DEP yt-dlp "yt-dlp.yt-dlp" yt-dlp
if errorlevel 1 exit /b 1

call :INSTALL_DEP ffmpeg "Gyan.FFmpeg" ffmpeg
if errorlevel 1 exit /b 1

echo [VidVortex] Dependency setup complete.
echo [VidVortex] Installed in normal Windows package-manager locations (PATH).
exit /b 0

:HAS_CMD
where "%~1" >nul 2>nul
exit /b %errorlevel%

:INSTALL_DEP
set "NAME=%~1"
set "WINGET_ID=%~2"
set "PKG_NAME=%~3"

call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

call :HAS_CMD winget
if errorlevel 1 goto :TRY_CHOCO
echo [VidVortex] Installing %NAME% with winget...
winget install --id "%WINGET_ID%" --silent --accept-source-agreements --accept-package-agreements
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:TRY_CHOCO
call :HAS_CMD choco
if errorlevel 1 goto :TRY_SCOOP
echo [VidVortex] Installing %NAME% with chocolatey...
choco install "%PKG_NAME%" -y
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:TRY_SCOOP
call :HAS_CMD scoop
if errorlevel 1 goto :DEP_FAIL
echo [VidVortex] Installing %NAME% with scoop...
scoop install "%PKG_NAME%"
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:DEP_FAIL
echo [Error] Could not install %NAME%.
echo [Error] Install manually and retry.
exit /b 1

:DEP_READY
echo [VidVortex] %NAME% is available.
exit /b 0

:ENSURE_PYTHON
call :HAS_CMD py
if errorlevel 1 goto :CHECK_PYTHON_CMD
py -3 -V >nul 2>nul
if not errorlevel 1 (
  echo [VidVortex] Python already installed via py launcher.
  exit /b 0
)

:CHECK_PYTHON_CMD
call :HAS_CMD python
if not errorlevel 1 (
  echo [VidVortex] Python already installed via python on PATH.
  exit /b 0
)

call :HAS_CMD winget
if errorlevel 1 goto :PY_TRY_CHOCO
echo [VidVortex] Installing Python with winget...
winget install --id "Python.Python.3.12" --silent --accept-source-agreements --accept-package-agreements
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_TRY_CHOCO
call :HAS_CMD choco
if errorlevel 1 goto :PY_TRY_SCOOP
echo [VidVortex] Installing Python with chocolatey...
choco install python -y
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_TRY_SCOOP
call :HAS_CMD scoop
if errorlevel 1 goto :PY_FAIL
echo [VidVortex] Installing Python with scoop...
scoop install python
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_FAIL
echo [Error] Could not install Python.
echo [Error] Install Python 3 and rerun setup.
exit /b 1
