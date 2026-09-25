@echo off
REM Starts every Smart Ration service for local development in its own window:
REM C# API (5188), AI service (8001), Python API (8000 - the frontend calls this) and the frontend (5173).
REM Same as scripts\development\start-all.ps1, which does the work (and skips anything already running).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\development\start-all.ps1"
