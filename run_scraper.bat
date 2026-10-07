@echo off
rem Double-click to run the scraper. Works from any folder.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python main.py
echo.
pause
