# AI Task Orchestrator - PowerShell Launcher
# Uso: .\run-orchestrator.ps1 [comando] [args]

# Configurar UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Obtener ruta del script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Cambiar al directorio del proyecto
Set-Location $ProjectDir

# Ejecutar
python run.py @args
