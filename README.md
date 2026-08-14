# OBS Live Translate - 实时字幕翻译插件

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
