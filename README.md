# OBS Live Translate

> 实时 AI 字幕 / 同声传译 OBS 插件 —— 系统级音频环回采集 + 大模型流式翻译 + 浏览器源字幕叠加。

把整个 **dist/** 目录复制到 OBS Studio 安装目录即可，**无需任何安装器**。首次启动后填入你自己的大模型 API Key，OBS 里加一个浏览器源指向 `http://127.0.0.1:8787/overlay`，字幕就出现在直播画面上了。

## 功能一览

| 功能 | 说明 |
| --- | --- |
| 跨平台 | Windows 10/11、Linux（PulseAudio/PipeWire）、macOS 13+（Apple Silicon） |
| 免安装 | 单文件二进制 + 静态资源目录，复制即可用，不写注册表、不修改系统 |
| 系统音频环回 | 抓取 OBS 监听输出的声音，无需虚拟声卡 |
| 流式翻译 | Qwen3.5-LiveTranslate-Flash-Realtime WebSocket 流式接口，低延迟 |
| 自动语言检测 | 中文直通不翻译；其它语种自动同传为中文 |
| VAD + 音乐检测 | 检测到静音或音乐时跳过该片段，省 token 也不污染字幕 |
| OBS 侧边栏控制台 | 通过 obs-websocket 注册自定义 dock，OBS 内一键开关 / 看日志 |
| 浏览器源字幕 | 字幕以 Browser Source 呈现，可自定义字体、颜色、动画 |
| 字幕"打字机"动效 | 自动渐入渐出、可选手写体 / 高对比度 / 单行 / 双行布局 |
| API Key 本地保存 | 配置只存在本地 config.toml，不联网回传 |

## 编译

详见 [docs/BUILD.md](docs/BUILD.md)。最短路径：

```bash
# 任何平台都只需要装 Rust 1.74+ 和系统基础依赖
cargo build --release
# 产物在 target/release/obs-live-translate
```

跨平台发布包用 `scripts/build-all.sh` / `scripts/build-all.ps1`。

## 打包正式版

```bash
# Windows
./scripts/build-all.ps1
# Linux / macOS
./scripts/build-all.sh
```

脚本会：

1. 在当前平台编译 release 二进制
2. 把 `dist/` 目录里所有前端资源、配置模板、启动器整合成 `release/<platform>/`
3. 写好 README，输出 `<platform>.tar.gz` / `.zip` —— 这就是直接分发的"正式版"

## 快速使用

1. 把发布包解压，**整个文件夹**复制到 `C:\Program Files\obs-studio\`（或 macOS、Linux 对应位置）。
2. 双击 `obs-live-translate`（或 `obs-live-translate.exe`）启动。
3. 浏览器打开 `http://127.0.0.1:8787/admin`，填入 API Key，选择音频输入设备，保存。
4. OBS 里加一个"浏览器"源，URL 填 `http://127.0.0.1:8787/overlay`，宽 1920、高 240，"刷新浏览器源时关闭"打开。
5. 开播。

## 目录结构

```
obs-live-translate/
├── Cargo.toml
├── src/                  # Rust 主程序
│   ├── main.rs
│   ├── audio/            # 跨平台音频环回
│   ├── vad/              # 静音 / 音乐检测
│   ├── llm/              # 大模型流式客户端
│   ├── lang/             # 语言检测
│   ├── server/           # HTTP / WS 服务 + 字幕广播
│   ├── obs/              # obs-websocket 客户端 / 自定义 dock
│   └── config.rs
├── overlay/              # 浏览器源字幕页面
├── admin/                # 管理面板
├── dist/                 # 打包时复制到 release 目录的资源
│   ├── overlay/  admin/  bin/  README.txt
├── scripts/              # 跨平台编译 + 打包脚本
├── docs/                 # 详细文档
└── release/              # 编译脚本产物（正式版）
```

## 许可

MIT
