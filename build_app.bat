@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [VidVortex] Please wait... starting build setup.

set "LOG_FILE=%SCRIPT_DIR%build.log"
if exist "%LOG_FILE%" del /f /q "%LOG_FILE%" >nul 2>nul

set "DOUBLECLICKED="
for %%x in (%cmdcmdline%) do (
  if /I "%%~x"=="/c" set "DOUBLECLICKED=1"
)

call :RUN_BUILD > "%LOG_FILE%" 2>&1
set "RC=%ERRORLEVEL%"

echo.
echo [VidVortex] Build output saved to:
echo %LOG_FILE%
echo.
echo [VidVortex] Build log:
echo ------------------------------------------------------------
type "%LOG_FILE%"
echo ------------------------------------------------------------
echo.

if "%RC%"=="0" (
  echo [Success] Build completed.
) else (
  echo [Error] Build failed with exit code %RC%.
  echo Check build.log for details.
)

if not "%RC%"=="0" pause
if defined DOUBLECLICKED pause
exit /b %RC%

:RUN_BUILD
echo [VidVortex] Preparing desktop app build...

call :ENSURE_PYTHON
if errorlevel 1 exit /b 1

%PY_CMD% -m pip install --upgrade pip
if errorlevel 1 (
  echo [Error] Failed to upgrade pip.
  exit /b 1
)

%PY_CMD% -m pip install -r requirements-desktop.txt
if errorlevel 1 (
  echo [Error] Failed to install desktop build dependencies.
  exit /b 1
)

set "ICON_PATH=%SCRIPT_DIR%app_logo.ico"
if exist "app_logo.png" (
  echo [VidVortex] Converting app_logo.png to app_logo.ico...
  %PY_CMD% -c "from PIL import Image; img=Image.open('app_logo.png').convert('RGBA'); img.save('app_logo.ico', format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
  if errorlevel 1 (
    echo [Error] Failed to convert app_logo.png to app_logo.ico.
    exit /b 1
  )
)
if not exist "%ICON_PATH%" (
  echo [Error] Icon file missing. Provide app_logo.png or app_logo.ico.
  exit /b 1
)

if exist "app\VidVortex.exe" (
  echo [VidVortex] Found existing app\VidVortex.exe. Checking if it is running...
  taskkill /IM "VidVortex.exe" /F >nul 2>nul
  timeout /t 1 /nobreak >nul
  del /f /q "app\VidVortex.exe" >nul 2>nul
  if exist "app\VidVortex.exe" (
    echo [Error] app\VidVortex.exe is locked by another process.
    echo [Error] Close VidVortex and try again.
    exit /b 1
  )
)

echo [VidVortex] Building executable with PyInstaller...
%PY_CMD% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --name VidVortex ^
  --onefile ^
  --windowed ^
  --distpath "app" ^
  --icon "%ICON_PATH%" ^
  --add-data "yt-dlp.conf.example;." ^
  --add-data "profiles.json.example;." ^
  --add-data "queue.json.example;." ^
  --collect-all ttkbootstrap ^
  vidvortex_app.py

if errorlevel 1 (
  echo [Error] Build failed.
  exit /b 1
)

echo [Success] Executable created: app\VidVortex.exe
exit /b 0

:LOCATE_PYTHON
set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -V >nul 2>nul
  if not errorlevel 1 (
    set "PY_CMD=py -3"
    exit /b 0
  )
)
where python >nul 2>nul
if not errorlevel 1 (
  set "PY_CMD=python"
  exit /b 0
)
exit /b 1

:ENSURE_PYTHON
call :LOCATE_PYTHON
if not errorlevel 1 (
  echo [VidVortex] Python detected: %PY_CMD%
  exit /b 0
)

echo [VidVortex] Python not found. Attempting auto-install...
where winget >nul 2>nul
if not errorlevel 1 (
  winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
)

call :LOCATE_PYTHON
if not errorlevel 1 (
  echo [VidVortex] Python installed successfully: %PY_CMD%
  exit /b 0
)

where choco >nul 2>nul
if not errorlevel 1 (
  choco install python -y
)

call :LOCATE_PYTHON
if not errorlevel 1 (
  echo [VidVortex] Python installed successfully: %PY_CMD%
  exit /b 0
)

echo [Error] Could not auto-install Python.
echo [Error] Install Python 3.10+ and run build_app.bat again.
exit /b 1
