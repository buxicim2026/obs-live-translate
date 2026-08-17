# 编译指南

OBS Live Translate 用 Rust 1.74+ 写，跨平台只依赖各系统的标准库。下面按平台给出"装好就能编译"的最短步骤。

## 通用前置

| 工具 | 版本 | 用途 |
| --- | --- | --- |
| Rust toolchain | 1.74+ | 编译器 |
| C 编译器 | 随系统 | cpal FFI |
| pkg-config | 任意 | Linux ALSA/Pulse |
| OpenSSL (开发版) | 任意 | `native-tls` 备用通道（可选） |

如果还没装 Rust：

```bash
# Windows (PowerShell)
winget install Rustlang.Rustup
# 或
irm https://sh.rustup.rs | iex

# macOS
brew install rustup-init && rustup-init -y
# 或
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## 一次性编译（开发用）

```bash
cargo build --release
# 产物 target/release/obs-live-translate
# Windows 下叫 obs-live-translate.exe
```

把 `target/release/obs-live-translate(.exe)` 与 `dist/overlay`、`dist/admin` 两个目录放在同一级，就是完整的"零安装"插件包。

## 跨平台正式版

`scripts/build-all.sh`（macOS / Linux）和 `scripts/build-all.ps1`（Windows）做下面这些事：

1. 调用 `rustup target add <target>`（首次需要联网）；
2. `cargo build --release --target <target>`；
3. 把 `dist/` 目录里的 overlay / admin / 启动器 / 文档复制到 `release/<platform>/`；
4. 把整个目录打成 `.tar.gz` / `.zip` —— **这就是要分发的正式版**。

```bash
# 在 macOS arm64 上
./scripts/build-all.sh
# -> release/macos-arm64/obs-live-translate
# -> release/macos-arm64.tar.gz
```

```powershell
# 在 Windows 上
powershell -ExecutionPolicy Bypass -File scripts\build-all.ps1
# -> release\windows-x64\bin\obs-live-translate.exe
# -> release\windows-x64.zip
```

跨平台产物用 GitHub Actions 自动出：`.github/workflows/release.yml` 在 push `v*` 标签时同时构建 4 个目标并把 `.zip` / `.tar.gz` 附到 release。

## 平台特定坑

### Windows

* 用 MSVC 工具链。装一次 *Build Tools for Visual Studio*（含 "C++ 桌面开发" 即可）。
* WASAPI 系统音频环回在 OBS 之外也能正常工作。
* 如果 OBS 安装在 `C:\Program Files\obs-studio\`，需要把整个 release 目录拷过去 —— 不会有写权限问题，因为二进制不带任何安装逻辑。

### macOS（Apple Silicon）

* 必需 Xcode Command Line Tools：`xcode-select --install`。
* 第一次抓系统音频时会弹"屏幕录制 / 麦克风"权限请求；同意后系统会缓存授权。
* 如果管理员面板上"音频"一直是红灯，进 `系统设置 -> 隐私与安全性 -> 屏幕录制 / 麦克风` 把本程序加白名单。

### Linux

发行版差异较大。下表只列"最少要装的包"：

| 发行版 | apt | dnf | pacman |
| --- | --- | --- | --- |
| Ubuntu / Debian | `libasound2-dev libpulse-dev` | — | — |
| Fedora / RHEL | — | `alsa-lib-devel pulseaudio-libs-devel` | — |
| Arch / Manjaro | — | — | `alsa-lib libpulse` |

PulseAudio / PipeWire 自带 monitor source，系统音频环回就是抓默认 sink 的 monitor。

## 验证编译

```bash
cargo test
```

跑：

```bash
RUST_LOG=info ./target/release/obs-live-translate
# 然后浏览器打开
# http://127.0.0.1:8787/admin
# http://127.0.0.1:8787/overlay
```

能用 mock provider 测：

```toml
[llm]
provider = "mock"
api_key = "any"
model = "mock"
```

## 精简二进制

已经默认开了 `lto = "thin"` + `strip = "symbols"`。再小可以加 UPX：

```bash
upx --best target/release/obs-live-translate
```

## 安装到 OBS 文件夹

最后一步：把 release 产物整个文件夹复制到 OBS 安装位置：

| 平台 | 路径 |
| --- | --- |
| Windows | `C:\Program Files\obs-studio\plugins\obs-live-translate\` |
| macOS | `/Applications/OBS.app/Contents/Resources/obs-live-translate/` |
| Linux | `~/.local/share/obs-studio/plugins/obs-live-translate/` |

然后：

* Windows：双击 `obs-live-translate/launcher.bat`
* macOS：双击 `obs-live-translate/launcher.sh`
* Linux：终端里 `./obs-live-translate/launcher.sh`
