# server/config.py
import json
import os
import sys


def get_app_dir():
    """获取应用数据目录（跨平台）"""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    app_dir = os.path.join(base, "obs-live-translate")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


CONFIG_PATH = os.path.join(get_app_dir(), "config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3.5-livetranslate-flash-realtime",
    "websocket_port": 9559,
    "sample_rate": 16000,
    "chunk_duration": 1.0,
    "silence_threshold": 0.02,
    "silence_timeout": 2.0,
    "music_detection": True,
    "auto_language_detect": True,
    "target_language": "zh",
    "max_subtitle_length": 30,
    "subtitle_display_time": 5.0,
    "font_size": 36,
    "font_color": "#FFFFFF",
    "background_color": "rgba(0,0,0,0.6)",
    "position": "bottom",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(saved)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
