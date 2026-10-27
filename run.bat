@echo off
title Student Management System (Google UI)
color 0A
cls
echo ============================================================
echo      STUDENT MANAGEMENT SYSTEM - WORKING MODEL
echo ============================================================
echo.
echo [1/2] Launching Web Browser at http://localhost:8080/ ...
start "" "http://localhost:8080/"
echo.
echo [2/2] Starting REST API Backend & Real-time Logs ...
echo       Press Ctrl + C anytime in this window to stop.
echo.
python -m app.server
pause
