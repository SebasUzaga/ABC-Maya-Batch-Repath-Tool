@echo off
setlocal

REM Get the folder where this .bat file is located
set SCRIPT_DIR=%~dp0

REM Run repath_ui.py with system Python
python "%SCRIPT_DIR%repath_ui.py"

endlocal
pause
