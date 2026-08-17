# 故障排查

## 状态条一直是红色

| 灯 | 含义 | 排查 |
| --- | --- | --- |
| 🔴 音频 | cpal 打开音频设备失败 | 平台章节有具体命令；一般是权限/驱动问题 |
| 🔴 大模型 | WebSocket 握手失败 | API Key 错、模型名错、计费欠费、地区封禁 |
| 🔴 OBS | obs-websocket 没开或密码错 | OBS -> 工具 -> WebSocket Server Settings |

## 启动报 "no suitable audio device found"

* Windows：检查 *设置 -> 系统 -> 声音 -> 输出设备* 是否至少有一个能用的设备。
* macOS：先在 OBS 里观察能不能听到系统声音，再回这里看；权限没给时 cpal 也会装作没有设备。
* Linux：跑 `pactl list short sinks`，确认至少一个 sink。`pavucontrol` 装一下最直观。

## macOS 上抓不到系统声音

* 打开 *系统设置 -> 隐私与安全性 -> 屏幕录制*，把 `obs-live-translate` 加进去。
* 第一次启动时 macOS 会弹一次授权，没弹就是被静默拒绝 —— 重新进系统设置勾上。
* 如果你的 OBS 是从 App Store 装的，权限可能挂在 App Store 自己的进程上；以非 App Store 渠道装的 OBS 通常没问题。

## 字幕一直在抖动 / 出现重复字符

* 你的 Provider 是 `openai-realtime` 且服务端没开 server-side VAD 的话会出现"重复听写"。把模型换成 `qwen-realtime` 或者把音频流开大 2s 缓冲。
* 管理员面板把 `min_segment_ms` 调到 600，`max_segment_ms` 调到 6000 试试。

## 字幕延迟 3-5 秒

流式翻译本来就有不可避免的端到端延迟（音频→服务端 VAD→ ASR → 翻译 → 流式输出）。常见优化：

1. 用 Qwen Realtime 走最近区域（杭州/新加坡）；
2. 关闭音乐 / 静音时的字幕（默认已开）；
3. 把 `min_segment_ms` 调到 300 左右。

## obs-websocket 一直连不上

1. 确认 OBS -> 工具 -> WebSocket Server Settings 勾了 *Enable WebSocket server*；
2. 端口默认 `4455`；如果你改过，把 `obs.port` 同步改一下；
3. 如果 OBS 端启用了密码，管理面板里 *OBS 密码* 也要填。

## 端口被占用

```bash
# 找占用
lsof -i :8787        # macOS / Linux
netstat -ano | findstr 8787   # Windows
```

改 `--port` 重启，或者到 *config.toml* 里改 `server.port`。

## 我不想每次都填 API Key

`config.toml` 里的 `llm.api_key` 字段是明文保存的。如果想"出厂就把 Key 烧进去"：

* 改 `dist/config.toml`（打包时覆盖）；
* 或者写一个环境变量读取器，扩展 `LlmConfig` 接受 `OLT_API_KEY`。

## 二进制能装进 OBS 目录但 OBS 不认

本插件不是"真正的" OBS 插件（不导出 `.obs-plugin` 元数据），所以 OBS 启动时不会自动加载它。它通过 obs-websocket 跟 OBS 对话，因此**不注册为 OBS 插件也没关系**。如果想要这个效果，可改成 C++ 写一个真正的 OBS 插件作为壳，工作量较大且失去"零安装"。

## LLM 报 "input_audio_format unsupported"

* Qwen Realtime 需要 16kHz/16bit 单声道 PCM。在管理面板里 `audio.sample_rate = 16000`，`audio.channels = 1`。
* 如果仍然报，先把 Provider 切到 `mock` 验证整条管线是通的，再切回 Qwen 排除环境问题。

## log 在哪里

* 默认打到 stderr（启动器用 `start /min` 时被 Windows 静默，需要看日志请用 `launcher.bat --console`）。
* 自定义：`set RUST_LOG=debug` (Windows) / `export RUST_LOG=debug` (macOS / Linux) 后再启动。
* 想持久化：`obs-live-translate 2>>plugin.log`（POSIX）或 `obs-live-translate.exe 2> plugin.log`（cmd）。
