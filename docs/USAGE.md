# 使用指南

## 1. 准备

1. 下载/解压对应平台的 release 包。
2. 把整个文件夹复制到 OBS Studio 安装目录（任意子目录都行，不会写注册表）。
3. 准备一个大模型 API Key：
   * **阿里云百炼（DashScope）**：开通 *实时语音翻译* 服务后，在控制台拿到 `sk-...` 形式的 key。
   * **OpenAI**：拿到 `sk-...` 形式的 key，并保证账号开通了 Realtime API 权限。
   * **Mock**：随便填，不消耗额度，只用来调试 UI。

## 2. 启动

* Windows：双击 `launcher.bat`
* macOS / Linux：终端里 `./launcher.sh`（或者 `open launcher.sh`）

启动器会：
1. 后台拉起 `obs-live-translate(.exe)`；
2. 自动打开 `http://127.0.0.1:8787/admin`；
3. 写一份 `config.toml` 到可执行文件同目录（第一次），里面是默认值。

## 3. 在管理面板里填 Key

打开 `http://127.0.0.1:8787/admin`（OBS 内也支持钉到侧边栏，见 §6）。

把 API Key 粘到 **大模型** 那张卡里：

* Provider 选 `Qwen Realtime (DashScope)` 或 `OpenAI Realtime`；
* Model 填模型名（默认 `qwen3.5-livetranslate-flash-realtime`，要换别的直接改）；
* API Key 填你自己的 key；
* **保存配置**。

填完 Key 后会自动重启音频→LLM 管线。状态条会显示：

* 🟢 音频 — 抓取到声音
* 🟢 大模型 — 与 Qwen / OpenAI 握手成功
* 🟢 OBS — 与 OBS Studio 连接成功（如果 OBS 在跑）

## 4. 在 OBS 里加字幕源

OBS 主界面 -> 底部"来源" -> **+** -> **浏览器**：

* URL：`http://127.0.0.1:8787/overlay`
* 宽度：`1920`，高度：`240`（按你的直播分辨率调）
* 勾上"控件"里的"当源显示时刷新"
* "自定义 CSS"留空（我们用自己写的样式）

把这个源放在最上面的图层（字幕要在画面顶部），拖到画面下沿。

> 💡 想换样式？在 URL 后面加 hash 参数，例如：
> `#size=56&color=%23ffe66d&bg=%23000000ff&position=bottom&animation=typewriter`

## 5. 听一下

打开任意有声内容（电影、音乐、自己的麦克风都行）。字幕窗口会：

* **中文输入**：原样输出（不调用翻译，省 token）；
* **英文 / 日文 / 韩文 / 其它语种**：自动同传成中文。

静音 / 纯音乐片段会被过滤，不会上送 token。

## 6. 把控制台钉到 OBS 侧边栏

OBS 顶部菜单 -> **工具** -> **自定义浏览器停靠面板 (Custom Browser Docks...)**：
* 名称：`Live Translate`
* URL：管理面板里"自动生成"那一行已写好（形如 `http://127.0.0.1:8787/admin?obsDock=1`）

确定之后，OBS 主界面会多一个侧边标签页，OBS 重启后还会保留。

## 7. 让字幕同时显示在 OBS 文本源里

如果想要字幕"硬"显示在画面（不是浏览器源），管理面板里打开"通过 OBS Text Source 镜像"开关（`obs.mirror_to_text_source`）。插件会：

* 自动在你的当前场景里新建一个名为 `Subtitles` 的 GDI+ 文本源；
* 每次字幕更新就同步写入这个文本源；
* 失败（场景名含中文 / 名字冲突）会显示在状态条上。

## 8. 关掉插件

* 直接关终端窗口 / 任务管理器结束 `obs-live-translate(.exe)`。
* 想"暂停字幕"但保留进程：在管理面板里把 API Key 清空并保存，LLM 会自动断开，音频继续抓但不上送。

## 9. 跨设备跑

默认服务只绑 `127.0.0.1`，别的机器访问不到。想跨设备看（很常见的远程直播场景）：

```bash
obs-live-translate --host 0.0.0.0 --port 8787
```

⚠️ 这种模式 API Key 会以 URL 不带 query 的方式走明文 HTTP（127.0.0.1 之外不安全）。生产场景建议接 nginx / Caddy 反向代理 + TLS。
