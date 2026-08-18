# Stream Live Translate

> 实时 AI 字幕 / 同声传译 OBS 插件 —— 系统级音频环回采集 + 大模型流式翻译 + 浏览器源字幕叠加。

把发布包解压到任意位置即可运行，**无需任何安装器、无需复制到 OBS 目录**。首次启动后填入你自己的大模型 API Key，OBS 里加一个浏览器源指向 `http://127.0.0.1:8787/overlay`，字幕就出现在直播画面上了。

## 功能一览

| 功能 | 说明 |
| --- | --- |
| 跨平台 | Windows 10/11、Debian 11+ / Ubuntu 20.04+、macOS 13+ (Apple Silicon) |
| 单文件分发 | 一个二进制搞定全部功能，前端资源全部内嵌，无需附带任何目录 |
| 便携模式 | 配置文件、缓存、日志都在可执行文件同目录，移动文件夹即可整体迁移 |
| 系统音频环回 | 抓取 OBS 监听输出的声音，无需虚拟声卡 |
| 流式翻译 | Qwen3.5-LiveTranslate-Flash-Realtime WebSocket 流式接口，低延迟 |
| 自动语言检测 | 中文直通不翻译；其它语种自动同传为中文 |
| VAD + 音乐检测 | 检测到静音或音乐时跳过该片段，省 token 也不污染字幕 |
| OBS 内配置 | 自动在 OBS Sources 里创建 `StreamLiveTranslateAdmin` 浏览器源，OBS 主窗口里就能改设置，不用切出去 |
| 浏览器源字幕 | 字幕以 Browser Source 呈现，可自定义字体、颜色、动画 |
| API Key 本地保存 | 配置只存在本地 `config.toml`，不联网回传 |

## 系统要求

| 平台 | 最低版本 | 系统依赖 |
| --- | --- | --- |
| **Windows** | Windows 10 1809+ | 无（MSVC 链接器在 cargo build 阶段就静态进二进制了） |
| **macOS** | macOS 13 (Ventura) | 仅 Apple Silicon（M1 / M2 / M3 / M4） |
| **Linux x64** | Ubuntu 20.04 LTS / Debian 11 (glibc 2.31+) | `libasound2` (alsa) + `ffmpeg`（推荐） |
| **Linux arm64** | Ubuntu 20.04 LTS / Debian 11 (glibc 2.31+) | 同上 |

> 没有 musl 静态版本（alsa 不是 Rust crate，无法静态链）。**glibc ≥ 2.31** 已覆盖目前所有受支持的 Debian / Ubuntu 发行版。

## 快速使用

### 1. 解压

把发布包（`stream-live-translate-<platform>.zip` / `.tar.gz`）解压到**任意目录**，比如：

- Windows：`D:\Tools\stream-live-translate\`
- Linux/macOS：`~/Applications/stream-live-translate/`

**整个文件夹可以自由移动、备份、拷贝到别的机器**，因为所有状态都在这个文件夹内（见下文"便携模式"）。

### 2. 安装系统依赖（仅 Linux）

Debian / Ubuntu：

```bash
sudo apt-get update
sudo apt-get install -y libasound2 ffmpeg
```

- `libasound2` —— cpal（音频采集）通过 alsa 取系统环回，**没有它插件完全起不来**。
- `ffmpeg` —— 可选；用于把多声道音频降采样到 16kHz 单声道喂给大模型。如果不装，插件会用一个纯 Rust 的简易重采样回退，效果稍差。

Fedora / RHEL：

```bash
sudo dnf install -y alsa-lib ffmpeg
```

Arch / Manjaro：

```bash
sudo pacman -S alsa-lib ffmpeg
```

Windows / macOS 跳过这步。

### 3. 启动

| 平台 | 命令 |
| --- | --- |
| Windows | 双击 `stream-live-translate.exe`（或 `launcher.bat`） |
| Linux   | `cd ~/Applications/stream-live-translate && ./stream-live-translate` |
| macOS   | 双击 `stream-live-translate`（或 `launcher.sh`） |

### 4. 首次配置

首次启动会**自动**在可执行文件同目录创建 `config.toml`。两种打开方式：

- **外部浏览器**：访问 <http://127.0.0.1:8787/admin>
- **OBS 内（推荐）**：连上 OBS 之后，Sources 列表里会自动多一个 `StreamLiveTranslateAdmin` 源，右键 → **互动 (Interact)** 就在 OBS 主窗口里打开设置面板；或者在管理页面点"在 OBS 中打开设置面板"按钮。

填入大模型 API Key → 保存。

### 5. OBS 里加字幕源

1. OBS 里加一个"**浏览器**"源。
2. URL 填 `http://127.0.0.1:8787/overlay`
3. 宽 `1920`、高 `240`
4. 勾选"**刷新浏览器源时关闭**"（避免字幕闪断）

### 6. 开播

## 便携模式（Portable Mode）

插件启动时**总是**优先把 `config.toml` 放在可执行文件同目录：

```
my-folder/
├── stream-live-translate(.exe)    ← 主程序
├── config.toml                     ← 自动生成；填了 API Key 之后所有设置都保存在这里
├── stream-live-translate.log       ← 运行日志（可选，tracing 控制）
└── dist/                           ← 可选；如果存在且包含 admin/overlay 子目录，优先用本地版本
                                      （用于自定义前端界面；不影响单文件分发的核心）
```

要点：

- **移动整个文件夹 = 迁移所有设置**。`config.toml` 不会被藏到 `%APPDATA%` 或 `~/.config/`，跟你看到的文件在一起。
- 如果安装目录是只读（例如 `/usr/local/bin/` 或 `C:\Program Files\`），插件会**自动回退**到系统用户配置目录：`%APPDATA%\stream-live-translate\config.toml`（Windows）或 `~/.config/stream-live-translate/config.toml`（Linux/macOS）。日志会打印实际使用的路径。
- 用 `--config <path>` 命令行参数可以强行指定 config 路径（覆盖上述所有规则）。
- `SLT_CONFIG=<path>` 环境变量也行（CI 友好）。

> 旧版本会把 config 写到 `%TEMP%` 之类的临时目录，每次启动都重置。**已经修了**——升级后请把旧 config 内容复制进新位置一次。

## 编译

详见 [docs/BUILD.md](docs/BUILD.md)。最短路径：

```bash
# 任何平台都只需要装 Rust 1.74+ 和系统基础依赖
cargo build --release
# 产物在 target/release/stream-live-translate(.exe)
```

跨平台发布包走 GitHub Actions（见 `.github/workflows/release.yml`），打 tag `v*` 自动构建 4 个目标（Linux x64 / arm64 / Windows x64 / macOS arm64）并发布到 Releases。

## 本地打发布包

```bash
# Windows
./scripts/build-all.ps1
# Linux / macOS
./scripts/build-all.sh
```

脚本会：

1. 在当前平台编译 release 二进制
2. 输出一个**只包含单文件二进制 + README + SHA256** 的发布包（zip 或 tar.gz）

发布包结构（举例 Linux）：

```
linux-x64.tar.gz
└── linux-x64/
    ├── stream-live-translate      ← 主程序（HTML/CSS/JS 已内嵌）
    └── README.txt                 ← Debian/Ubuntu 装依赖一行命令
```

## 目录结构

```
stream-live-translate/
├── Cargo.toml
├── src/                  # Rust 主程序（单二进制）
│   ├── main.rs           # CLI / 启动 / 便携模式 config 解析
│   ├── audio.rs          # cpal 跨平台音频环回
│   ├── vad.rs            # 静音 / 音乐检测
│   ├── llm.rs            # 大模型流式客户端
│   ├── lang.rs           # 语言检测
│   ├── server.rs         # HTTP / WS 服务 + 字幕广播
│   ├── obs.rs            # obs-websocket 客户端 + 自动 dock 源
│   ├── pipeline.rs       # audio -> LLM -> subtitle 管线
│   ├── subtitle.rs       # 字幕事件总线
│   ├── config.rs         # toml 配置（load / save / merge patch）
│   └── embedded.rs       # compile-time 内嵌 dist/ 资源
├── overlay/              # 浏览器源字幕页面
├── admin/                # 管理面板
├── dist/                 # 内嵌资源 + 启动器 + 默认 config.toml
├── scripts/              # 跨平台打包脚本
├── docs/                 # 详细文档
└── .github/workflows/    # CI: 打 tag 自动构建 4 平台
```

## 文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) —— 模块拓扑、数据流
- [docs/BUILD.md](docs/BUILD.md) —— 各种环境下从源码编译
- [docs/USAGE.md](docs/USAGE.md) —— 完整使用文档、API 列表
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) —— 常见问题

## 许可

MIT
