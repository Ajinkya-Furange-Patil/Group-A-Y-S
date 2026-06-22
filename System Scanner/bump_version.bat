@echo off
REM Auto Version Bump Batch Script
REM Run this after making changes to auto-increment version

echo.
echo ======================================================================
echo AI DISCOVERY SCANNER - AUTO VERSION BUMP
echo ======================================================================
echo.

if "%1"=="" (
    echo No bump type specified, using default: PATCH
    python auto_version_bump.py patch
) else (
    echo Bump type: %1
    python auto_version_bump.py %1
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Version bump failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Do you want to rebuild the executables now? (Y/N)
set /p REBUILD="Your choice: "

if /i "%REBUILD%"=="Y" (
    echo.
    echo Starting build process...
    python build_both_versions.py
)

echo.
pause
