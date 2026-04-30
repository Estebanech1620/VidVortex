@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0."
if errorlevel 1 (
  echo [Error] Could not switch to this script's folder.
  echo        Open Command Prompt, run:  cd /d "full\path\to\scripts"
  echo        Then run:  setup_windows.bat
  set EC=1
  goto :WAIT_EXIT
)

call :MAIN
set "EC=!ERRORLEVEL!"

:WAIT_EXIT
if /i "%~1"=="nopause" exit /b !EC!
echo.
echo Press any key to close this window...
pause >nul
exit /b !EC!

:MAIN
echo [VidVortex] Windows dependency setup starting...

call :ENSURE_PYTHON
if errorlevel 1 exit /b 1

call :INSTALL_DEP yt-dlp "yt-dlp.yt-dlp" yt-dlp
if errorlevel 1 exit /b 1

call :UPGRADE_YTDLP

call :INSTALL_DEP ffmpeg "Gyan.FFmpeg" ffmpeg
if errorlevel 1 exit /b 1

call :UPGRADE_FFMPEG

echo [VidVortex] Dependency setup complete.
echo [VidVortex] Installed in normal Windows package-manager locations (PATH).
exit /b 0

:HAS_CMD
where "%~1" >nul 2>nul
if errorlevel 1 exit /b 1
exit /b 0

rem Reload PATH from registry so installs in this session stay visible to where.exe
:REFRESH_PATH
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%p"
exit /b 0

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
call :REFRESH_PATH
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:TRY_CHOCO
call :HAS_CMD choco
if errorlevel 1 goto :TRY_SCOOP
echo [VidVortex] Installing %NAME% with chocolatey...
choco install "%PKG_NAME%" -y
call :REFRESH_PATH
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:TRY_SCOOP
call :HAS_CMD scoop
if errorlevel 1 goto :DEP_FAIL
echo [VidVortex] Installing %NAME% with scoop...
scoop install "%PKG_NAME%"
call :REFRESH_PATH
call :HAS_CMD "%NAME%"
if not errorlevel 1 goto :DEP_READY

:DEP_FAIL
echo [Error] Could not install %NAME%.
echo [Error] Install manually and retry.
echo [Hint] If you just installed %NAME%, close this window, open a new one, and run setup again ^(PATH updates apply to new sessions^).
exit /b 1

:DEP_READY
echo [VidVortex] %NAME% is available.
exit /b 0

:UPGRADE_YTDLP
echo [VidVortex] Updating yt-dlp ^(package managers, then built-in -U, then pip^)...
call :HAS_CMD winget
if not errorlevel 1 (
  winget upgrade --id "yt-dlp.yt-dlp" --silent --accept-source-agreements --accept-package-agreements
)
call :HAS_CMD choco
if not errorlevel 1 (
  choco upgrade yt-dlp -y
)
call :HAS_CMD scoop
if not errorlevel 1 (
  scoop update yt-dlp
)
call :REFRESH_PATH
call :HAS_CMD yt-dlp
if not errorlevel 1 (
  echo [VidVortex] yt-dlp self-update ^(-U^)...
  yt-dlp -U
)
call :PIP_UPGRADE_YTDLP
exit /b 0

:PIP_UPGRADE_YTDLP
echo [VidVortex] pip: upgrading yt-dlp ^(gets fixes faster than some store builds^)...
py -3 -m pip --version >nul 2>nul && (
  py -3 -m pip install --upgrade pip 2>nul
  py -3 -m pip install --upgrade yt-dlp 2>nul
  call :REFRESH_PATH
  goto :PIP_YTDLP_DONE
)
python -m pip --version >nul 2>nul && (
  python -m pip install --upgrade pip 2>nul
  python -m pip install --upgrade yt-dlp 2>nul
  call :REFRESH_PATH
)
:PIP_YTDLP_DONE
exit /b 0

:UPGRADE_FFMPEG
echo [VidVortex] Updating ffmpeg if package managers offer a newer build...
call :HAS_CMD winget
if not errorlevel 1 (
  winget upgrade --id "Gyan.FFmpeg" --silent --accept-source-agreements --accept-package-agreements
)
call :HAS_CMD choco
if not errorlevel 1 (
  choco upgrade ffmpeg -y
)
call :HAS_CMD scoop
if not errorlevel 1 (
  scoop update ffmpeg
)
call :REFRESH_PATH
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
call :REFRESH_PATH
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_TRY_CHOCO
call :HAS_CMD choco
if errorlevel 1 goto :PY_TRY_SCOOP
echo [VidVortex] Installing Python with chocolatey...
choco install python -y
call :REFRESH_PATH
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_TRY_SCOOP
call :HAS_CMD scoop
if errorlevel 1 goto :PY_FAIL
echo [VidVortex] Installing Python with scoop...
scoop install python
call :REFRESH_PATH
call :HAS_CMD py
if not errorlevel 1 exit /b 0
call :HAS_CMD python
if not errorlevel 1 exit /b 0

:PY_FAIL
echo [Error] Could not install Python.
echo [Error] Install Python 3 and rerun setup.
exit /b 1
