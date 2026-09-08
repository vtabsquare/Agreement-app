@echo off
start "Aurelia Backend" cmd /k "%~dp0backend\run_backend.bat"
timeout /t 2 >nul
start "Aurelia Frontend" cmd /k "%~dp0frontend\run_frontend.bat"
