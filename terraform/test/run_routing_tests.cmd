@echo off
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0validate_routing_configuration.ps1"
exit /b %ERRORLEVEL%
