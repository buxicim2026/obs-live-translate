#!/bin/bash
echo "============================================"
echo "  OBS Live Translate - macOS 构建脚本"
echo "============================================"
echo ""

cd "$(dirname "$0")/.."

echo "[1/4] 清理旧构建..."
rm -rf dist build

echo "[2/4] 安装依赖..."
pip3 install -r requirements.txt

echo "[3/4] 构建可执行文件..."
pyinstaller --onefile --console \
    --name "obs-live-translate" \
    --add-data "browser_source:browser_source" \
    --add-data "dock:dock" \
    --hidden-import sounddevice \
    --hidden-import numpy \
    --hidden-import websockets \
    --hidden-import aiohttp \
    --target-arch arm64 \
    --collect-all sounddevice \
    server/main.py

echo "[4/4] 准备发布文件..."
mkdir -p release/obs-live-translate
cp dist/obs-live-translate release/obs-live-translate/
cp -r browser_source release/obs-live-translate/
cp -r dock release/obs-live-translate/

echo ""
echo "============================================"
echo "  构建完成!"
echo "  输出目录: release/obs-live-translate/"
echo "============================================"
echo ""
echo "使用方法:"
echo "  1. 将 release/obs-live-translate/ 复制到任意位置"
echo "  2. 运行 ./obs-live-translate"
echo "  3. 在OBS中添加浏览器源"
echo ""
echo "macOS 音频捕获设置:"
echo "  需要安装 BlackHole: brew install blackhole-2ch"
echo "  然后在系统设置中创建多输出设备"
echo "============================================"
