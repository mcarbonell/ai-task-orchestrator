@echo off
REM AI Task Orchestrator - Windows CMD Launcher
REM Usage: run.bat [command] [args]

chcp 65001 >nul
set PYTHONIOENCODING=utf-8

python run.py %*
