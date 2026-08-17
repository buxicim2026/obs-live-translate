# 架构总览

```
┌──────────────────────────────────────────────────────────────────────┐
│                       OBS Studio 进程                                  │
│  ┌─────────────────┐    ┌──────────────────┐                          │
│  │ 浏览器源 (Broswer│    │ "Subtitles" 文本  │  ← 由 obs-websocket    │
│  │  Source)        │    │ 源 (GDI+)         │     远程更新             │
│  └────────┬────────┘    └────────▲─────────┘                          │
│           │ http              obs-ws v5                              │
│           ▼                     │                                     │
│  ┌──────────────────────────────┴────────────┐                        │
│  │   obs-live-translate 进程 (我们的)         │                        │
│  │                                              │                    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────┴──┐  ┌──────────────┐  │
│  │  │ 音频环回   │→ │ VAD + 音乐  │→ │ LLM Provider│→│ 字幕 Hub      │  │
│  │  │ (cpal)     │  │ 过滤       │  │ (Qwen / OAI)│  │ (broadcast)  │  │
│  │  └────────────┘  └────────────┘  └───────────┘  └──────┬───────┘  │
│  │                                                          │         │
│  │                                              WS │ HTTP │ /ws  │   │
│  │                                                          ▼         │
│  │                                              ┌────────────────┐    │
│  │                                              │ Admin / Overlay │    │
│  │                                              │ (浏览器源)       │    │
│  │                                              └────────────────┘    │
│  └─────────────────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

## 模块地图（src/）

| 文件 | 职责 |
| --- | --- |
| `main.rs` | CLI 解析、tokio runtime、组装 AppState、起任务 |
| `config.rs` | `Config` 结构、`config.toml` 读写、默认值 |
| `audio.rs` | 跨平台 PCM 环回采集（Windows WASAPI / macOS CoreAudio+SCK / Linux PulseAudio） |
| `vad.rs` | 能量 + 频谱平坦度的静音 / 音乐检测 |
| `lang.rs` | Unicode 区间判断的中 / 英 / 日 / 韩语言检测 |
| `llm.rs` | `LlmProvider` trait + Qwen / OpenAI / Mock 实现 |
| `subtitle.rs` | 字幕事件聚合 + 广播（partial / final / cleared） |
| `pipeline.rs` | 音频 → VAD → LLM 流水线 + 故障重启 |
| `server.rs` | axum HTTP / WS 路由：API、admin、overlay、ws/subtitles |
| `obs.rs` | obs-websocket v5 客户端 + 鉴权 + Text Source 控制 |

## 关键设计点

### 1. 为什么"零安装"

* Rust 默认产出单个静态二进制（`lto + strip` 后约 8-12 MB）；
* 浏览器源 / admin 面板是普通 HTML + JS + CSS，存在 `dist/` 目录里被 axum 当静态文件服务；
* 没有 native dependencies 需要安装（cpal 走系统自带的 WASAPI/CoreAudio/PulseAudio）；
* 配置写在可执行文件同目录的 `config.toml`，不写注册表 / LaunchAgents / systemd unit。

### 2. 为什么用 obs-websocket 而不是 C++ 真插件

C++ 真插件需要：
* 维护三个平台的构建脚本（MSVC / Xcode / autotools）；
* 改一个 dll 接口签名会让插件签名过期；
* 升级 OBS 26 → 28 时常见 ABI 破裂。

而 obs-websocket：
* OBS 28+ 自带、协议稳定；
* 用纯 WebSocket + JSON 通讯，跨语言简单；
* 已能完成"创建文本源 / 改文本源 / 监听事件" 99% 的功能。

唯一 OBS 内深度集成（侧边栏）我们用 *Custom Browser Docks* 实现 —— 这是 OBS 自带的功能，不需要写插件。

### 3. 字幕事件流

字幕事件流是 LLM ↔ 浏览器源唯一通道。事件是 JSON：

```jsonc
// partial：流式 delta
{ "type": "partial", "text": "大家好" }
// final：这一句结束
{ "type": "final", "text": "大家好，欢迎来到直播间。" }
// cleared：用户清空
{ "type": "cleared" }
```

服务端是 tokio `broadcast::channel`，多客户端（多个 OBS 浏览器源 + admin 预览）共享。

### 4. VAD 在哪里跑

* 服务端：Qwen Realtime 内部已经做了 VAD；
* 客户端：我们在 `pipeline.rs` 里用能量 + 频谱平坦度过滤，把静音 / 纯音乐片段在上送之前丢弃；
* 这么做的好处：节省 token，且不会因为背景音乐导致模型"幻觉"出假字幕。

### 5. 自动语言检测

* 客户端 `lang::detect` 用 Unicode 区间做粗判（决定要不要把这段音频发到翻译模型）；
* 服务端 Qwen Realtime 自带 ASR，可以选择只 ASR 不翻译（中文时）或者 ASR + 翻译（其它语种）。
* 服务端的语言判断在指令里已经写好（`instructions` 字段），客户端只是双保险。

### 6. 安全边界

* 默认只绑 `127.0.0.1`，局域网 / 公网不能访问；
* API Key 只写本地 `config.toml`，UI 上以 `type=password` 输入；
* 没有任何 outbound 数据回传作者（除 LLM API 自身的调用）。

## 接下来能加什么

| 想加的东西 | 难度 | 提示 |
| --- | --- | --- |
| 字幕样式：阴影 / 描边 / 渐变 | 容易 | 改 `overlay/style.css` |
| 字幕历史"自动滚动" | 容易 | admin 卡片里加 `setInterval` |
| 双语模式 | 中等 | 增加 `subtitle.current` 之外的 `current_translation`，前端并排渲染 |
| 字幕导出 SRT | 容易 | 在 `subtitle.rs` 里加 `to_srt()`，admin 提供下载按钮 |
| 多语言输出（英 / 日 / 韩） | 中等 | `LlmConfig` 加 `target_lang`，session.update 改 instructions |
| 字幕热词替换 | 中等 | 加 `replace.rs`，在 hub 写入前对 text 做映射 |
| 真 OBS 插件 | 难 | 起新 C++ 子项目，把 server 改成 OBS in-process source |
