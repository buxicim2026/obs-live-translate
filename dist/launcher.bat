@echo off
rem ============================================================
rem  Stream Live Translate - Windows launcher
rem
rem  双击本文件即可启动。会把可执行文件放后台运行，并自动
rem  在默认浏览器里打开管理面板。
rem
rem  想看实时日志：用命令行启动本文件，或加 --console
rem ============================================================

setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

set "EXE=%ROOT%stream-live-translate.exe"
if not exist "%EXE%" (
  echo [错误] 找不到 stream-live-translate.exe，请确认插件目录完整。
  pause
  exit /b 1
)

if "%1"=="--console" goto run
if "%1"=="-c" goto run

rem 后台模式：启动后自动打开管理面板。
start "" "http://127.0.0.1:8787/admin"
start "" /min "%EXE%" %*
exit /b 0

:run
"%EXE%" %*
