@echo off
chcp 65001 >nul
echo ============================================
echo   OBS Live Translate - Windows 构建脚本
echo ============================================
echo.

cd /d "%~dp0.."

echo [1/4] 清理旧构建...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [2/4] 安装依赖...
pip install -r requirements.txt

echo [3/4] 构建可执行文件...
pyinstaller --onefile --console ^
    --name "obs-live-translate" ^
    --add-data "browser_source;browser_source" ^
    --add-data "dock;dock" ^
    --add-data "obs-script;obs-script" ^
    --hidden-import sounddevice ^
    --hidden-import numpy ^
    --hidden-import websockets ^
    --hidden-import aiohttp ^
    --collect-all sounddevice ^
    server/main.py

echo [4/4] 准备发布文件...
if not exist "release\obs-live-translate" mkdir "release\obs-live-translate"
copy "dist\obs-live-translate.exe" "release\obs-live-translate\"
xcopy /E /I "browser_source" "release\obs-live-translate\browser_source"
xcopy /E /I "dock" "release\obs-live-translate\dock"
xcopy /E /I "obs-script" "release\obs-live-translate\obs-script"
copy "start.bat" "release\obs-live-translate\"
copy "install.py" "release\obs-live-translate\"

echo.
echo ============================================
echo   构建完成!
echo   输出目录: release\obs-live-translate\
echo ============================================
echo.
echo 使用方法:
echo   1. 将 release\obs-live-translate\ 文件夹复制到任意位置
echo   2. 双击 start.bat 或 obs-live-translate.exe
echo   3. 在OBS中添加浏览器源
echo ============================================
pause
