# OBS Live Translate - 实时字幕翻译插件
#由不息传播制作
[![Build](https://github.com/buxicim2026/obs-live-translate/actions/workflows/build.yml/badge.svg)](https://github.com/buxicim2026/obs-live-translate/actions/workflows/build.yml)

将直播音频实时识别并翻译为中文显示在 OBS 画面上。中文内容直接输出，外语自动"同声传译"成中文。

## ✨ 功能特性

- 🎙️ **实时字幕** - 捕获系统音频，实时显示字幕
- 🌐 **同声传译** - 中文直出，外语自动翻译为中文
- 🎵 **音乐检测** - 自动跳过音乐播放时段
- 🔇 **静音检测** - 无人声时自动停止发送请求
- 🖥️ **OBS 集成** - 浏览器源显示 + 侧边栏控制面板
- 🔑 **多模型支持** - 支持兼容 OpenAI 接口的各类大模型

## 📥 下载安装

### 方式一：下载预编译版本（推荐）

从 [GitHub Releases](../../releases) 下载对应平台的压缩包：

| 平台 | 文件 |
|------|------|
| 🪟 Windows x64 | `obs-live-translate-windows-x64.zip` |
| 🐧 Linux x64 | `obs-live-translate-linux-x64.tar.gz` |
| 🍎 macOS Apple Silicon | `obs-live-translate-macos-arm64.zip` |

解压后即可使用，无需安装。

### 方式二：OBS 脚本安装（免独立运行）

1. 将 `obs-script/obs_live_translate.py` 复制到 OBS 脚本目录：
   - **Windows**: `%APPDATA%\obs-studio\scripts\`
   - **macOS**: `~/Library/Application Support/obs-studio/scripts/`
   - **Linux**: `~/.config/obs-studio/scripts/`

2. 将后端程序放在脚本同级目录的 `backend/` 文件夹中

3. 在 OBS 中「工具 → 脚本」加载并配置

## 🚀 使用说明

### 1. 准备 API Key

本插件需要大模型 API Key 进行语音识别和翻译。推荐使用：
- **阿里云百炼** - `qwen3.5-livetranslate-flash-realtime` 模型
- 或其他兼容 OpenAI 接口的模型

### 2. 启动服务

**Windows**:
```bash
双击 启动.bat
```
**Linux**:
```bash
chmod +x obs-live-translate ./start.sh
```

**macOS**:
```bash
chmod +x obs-live-translate ./start.command

```
### 3. OBS 设置

#### 添加字幕浏览器源

1. 在 OBS 中点击「来源」→「+」→「浏览器」
2. 名称填写：`实时字幕`
3. URL 填写插件目录下的 `browser_source/subtitle.html` 文件路径：file:///C:/obs-live-translate/browser_source/subtitle.html（视乎你电脑的实际情况）
4. 宽度：`1920`，高度：`200`
5. 勾选「通过OC关闭源时刷新浏览器」

#### 打开控制面板

1. OBS 菜单「视图 → 停靠部件 → 自定义浏览器停靠部件」
2. 名称：`字幕控制面板`
3. URL：`file:///C:/obs-live-translate/dock/control_panel.html`
4. 在控制面板中填入你的 API Key 并保存

### 4. 音频捕获准备

**Windows**:
- 右键任务栏音量图标 → 声音设置 → 更多声音设置
- 在「录制」选项卡中启用「立体声混音」
- 如果没有，可能需要更新声卡驱动或使用 [VB-Cable](https://vb-audio.com/Cable/)

**macOS**:
```bash
brew install blackhole-2ch
```
- 在「音频 MIDI 设置」中创建多输出设备
- 将 BlackHole 和输出设备同时勾选

**Linux**:
```bash
pactl list sources | grep monitor
```
确保 PulseAudio 正在运行

使用 monitor 源进行捕获

## ⚙️ 配置说明

配置文件位于用户数据目录：
- **Windows**: `%APPDATA%\obs-live-translate\config.json`
- **macOS**: `~/Library/Application Support/obs-live-translate/config.json`
- **Linux**: `~/.config/obs-live-translate/config.json`

```json
{ "api_key": "your-api-key-here", "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen3.5-livetranslate-flash-realtime", "websocket_port": 9559, "sample_rate": 16000, "chunk_duration": 1.0, "silence_threshold": 0.02, "silence_timeout": 2.0, "music_detection": true, "auto_language_detect": true, "target_language": "zh" }
```
## 📁 项目结构
obs-live-translate/ ├── backend/ # Python 后端服务（编译后） │ └── obs-live-translate ├── browser_source/ # OBS 浏览器源（字幕显示） │ └── subtitle.html ├── dock/ # OBS 侧边栏控制面板 │ └── control_panel.html ├── obs-script/ # OBS Python 脚本 │ └── obs_live_translate.py ├── server/ # Python 源代码 │ ├── main.py # 主程序入口 │ ├── audio_capture.py # 音频捕获 │ ├── audio_processor.py # 音频处理（VAD/音乐检测） │ ├── translator.py # 大模型 API 调用 │ ├── websocket_server.py # WebSocket 服务 │ └── config.py # 配置管理 ├── build/ # 编译脚本 │ ├── build_windows.bat │ ├── build_linux.sh │ └── build_macos.sh └── .github/workflows/ # GitHub Actions CI/CD └── build.yml
