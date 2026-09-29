@echo off
REM Wrapper-Skript fuer die Windows-Aufgabenplanung: aktiviert die virtuelle
REM Umgebung und fuehrt den Agenten aus.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
