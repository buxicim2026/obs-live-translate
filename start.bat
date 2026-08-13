@echo off
chcp 65001 >nul
title OBS Live Translate
echo ============================================
echo   OBS Live Translate - 实时字幕翻译
echo ============================================
echo.
echo 正在启动服务...
echo.
cd /d "%~dp0"
obs-live-translate.exe
pause
