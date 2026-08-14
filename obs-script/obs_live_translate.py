#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBS Live Translate - OBS Python 脚本
=====================================
将此文件复制到 OBS 脚本目录即可使用：
  - Windows: %APPDATA%\obs-studio\scripts\
  - macOS: ~/Library/Application Support/obs-studio/scripts/
  - Linux: ~/.config/obs-studio/scripts/

功能：
  - 在 OBS 内启动/停止实时字幕翻译后端服务
  - 提供配置界面（API Key、模型选择等）
  - 自动创建浏览器源和停靠窗口
"""

import obspython as obs
import os
import sys
import subprocess
import json

# ============================================================
# 全局状态
# ============================================================
_backend_proc = None
_script_path = ""
_backend_path = ""
_browser_source_name = "实时字幕"
_dock_name = "字幕控制面板"

# 默认配置
default_settings = {
    "api_key": "",
    "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3.5-livetranslate-flash-realtime",
    "websocket_port": 9559,
    "silence_threshold": 0.02,
    "music_detection": True,
    "auto_language_detect": True,
}

# ============================================================
# 脚本元信息
# ============================================================
def script_description():
    return (
        "<h2>OBS Live Translate - 实时字幕翻译</h2>"
        "<p>将直播音频实时识别并翻译为中文显示在画面上。</p>"
        "<p><b>特性：</b></p>"
        "<ul>"
        "<li>中文内容直接显示，外语自动翻译为中文</li>"
        "<li>音乐检测与静音检测</li>"
        "<li>OBS 浏览器源 + 侧边栏控制面板</li>"
        "</ul>"
    )


def script_properties():
    props = obs.obs_properties_create()

    # API 设置组
    api_group = obs.obs_properties_create()
    obs.obs_properties_add_text(api_group, "api_key", "API Key", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_text(api_group, "api_base_url", "API Base URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(api_group, "model", "模型名称", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_group(props, "api_group", "API 设置", obs.OBS_GROUP_NORMAL, api_group)

    # 音频设置组
    audio_group = obs.obs_properties_create()
    silence = obs.obs_properties_add_float_slider(audio_group, "silence_threshold", "静音阈值", 0.001, 0.5, 0.001)
    obs.obs_property_float_set_suffix(silence, "")
    obs.obs_properties_add_bool(audio_group, "music_detection", "启用音乐检测")
    obs.obs_properties_add_group(props, "audio_group", "音频设置", obs.OBS_GROUP_NORMAL, audio_group)

    # 功能开关组
    feature_group = obs.obs_properties_create()
    obs.obs_properties_add_bool(feature_group, "auto_language_detect", "自动语言检测")
    obs.obs_properties_add_int(feature_group, "websocket_port", "WebSocket 端口", 1024, 65535, 1)
    obs.obs_properties_add_group(props, "feature_group", "功能设置", obs.OBS_GROUP_NORMAL, feature_group)

    # 操作按钮
    obs.obs_properties_add_button(props, "btn_save", "保存配置并启动服务", on_save_clicked)
    obs.obs_properties_add_button(props, "btn_stop", "停止服务", on_stop_clicked)
    obs.obs_properties_add_button(props, "btn_create_source", "创建浏览器源", on_create_source_clicked)
    obs.obs_properties_add_button(props, "btn_create_dock", "打开控制面板", on_create_dock_clicked)

    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "api_key", default_settings["api_key"])
    obs.obs_data_set_default_string(settings, "api_base_url", default_settings["api_base_url"])
    obs.obs_data_set_default_string(settings, "model", default_settings["model"])
    obs.obs_data_set_default_int(settings, "websocket_port", default_settings["websocket_port"])
    obs.obs_data_set_default_double(settings, "silence_threshold", default_settings["silence_threshold"])
    obs.obs_data_set_default_bool(settings, "music_detection", default_settings["music_detection"])
    obs.obs_data_set_default_bool(settings, "auto_language_detect", default_settings["auto_language_detect"])


def script_update(settings):
    """设置变更时调用"""
    pass


def script_load(settings):
    """脚本加载时调用"""
    global _script_path, _backend_path
    _script_path = os.path.dirname(os.path.realpath(__file__))
    _backend_path = os.path.join(_script_path, "..", "backend", "obs-live-translate")

    if sys.platform == "win32":
        _backend_path += ".exe"

    obs.script_log(obs.LOG_INFO, "OBS Live Translate 脚本已加载")
    obs.script_log(obs.LOG_INFO, f"后端路径: {_backend_path}")


def script_unload():
    """脚本卸载时调用"""
    stop_backend()
    obs.script_log(obs.LOG_INFO, "OBS Live Translate 脚本已卸载")


# ============================================================
# 后端服务管理
# ============================================================
def start_backend(settings):
    """启动后端服务"""
    global _backend_proc, _backend_path

    if _backend_proc is not None and _backend_proc.poll() is None:
        obs.script_log(obs.LOG_WARNING, "后端服务已在运行")
        return True

    if not os.path.exists(_backend_path):
        obs.script_log(obs.LOG_ERROR, f"找不到后端程序: {_backend_path}")
        obs.script_log(obs.LOG_INFO, "请确保已将插件文件夹完整复制到 OBS 目录")
        return False

    config = {
        "api_key": obs.obs_data_get_string(settings, "api_key"),
        "api_base_url": obs.obs_data_get_string(settings, "api_base_url"),
        "model": obs.obs_data_get_string(settings, "model"),
        "websocket_port": obs.obs_data_get_int(settings, "websocket_port"),
        "silence_threshold": obs.obs_data_get_double(settings, "silence_threshold"),
        "music_detection": obs.obs_data_get_bool(settings, "music_detection"),
        "auto_language_detect": obs.obs_data_get_bool(settings, "auto_language_detect"),
    }

    config_dir = os.path.join(os.path.expanduser("~"), ".config", "obs-live-translate")
    if sys.platform == "win32":
        config_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "obs-live-translate")
    elif sys.platform == "darwin":
        config_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "obs-live-translate")

    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.json")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        obs.script_log(obs.LOG_ERROR, f"保存配置失败: {e}")

    try:
        env = os.environ.copy()
        env["OBS_LIVE_TRANSLATE_CONFIG"] = config_path

        if sys.platform == "win32":
            _backend_proc = subprocess.Popen(
                [_backend_path],
                cwd=os.path.dirname(_backend_path),
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            _backend_proc = subprocess.Popen(
                [_backend_path],
                cwd=os.path.dirname(_backend_path),
                env=env,
            )

        obs.script_log(obs.LOG_INFO, f"后端服务已启动 (PID: {_backend_proc.pid})")
        return True
    except Exception as e:
        obs.script_log(obs.LOG_ERROR, f"启动后端服务失败: {e}")
        return False


def stop_backend():
    """停止后端服务"""
    global _backend_proc
    if _backend_proc is not None:
        try:
            _backend_proc.terminate()
            _backend_proc.wait(timeout=5)
            obs.script_log(obs.LOG_INFO, "后端服务已停止")
        except Exception:
            try:
                _backend_proc.kill()
            except Exception:
                pass
        _backend_proc = None


# ============================================================
# 按钮回调
# ============================================================
def on_save_clicked(props, prop):
    """保存配置并启动服务"""
    obs.script_log(obs.LOG_INFO, "配置已保存，请确保已填写 API Key")
    obs.script_log(obs.LOG_INFO, "请手动运行后端程序 obs-live-translate")
    return True


def on_stop_clicked(props, prop):
    """停止服务"""
    stop_backend()
    return True


def on_create_source_clicked(props, prop):
    """创建浏览器源"""
    global _script_path

    current_scene = obs.obs_frontend_get_current_scene()
    if not current_scene:
        obs.script_log(obs.LOG_ERROR, "没有活跃的场景")
        return False

    scene = obs.obs_scene_from_source(current_scene)

    existing = obs.obs_scene_find_source(scene, _browser_source_name)
    if existing:
        obs.script_log(obs.LOG_WARNING, f"'{_browser_source_name}' 已存在")
        obs.obs_source_release(current_scene)
        return False

    source_settings = obs.obs_data_create()
    browser_source_path = os.path.join(_script_path, "..", "browser_source", "subtitle.html")
    browser_source_url = "file:///" + browser_source_path.replace("\\", "/")

    obs.obs_data_set_string(source_settings, "url", browser_source_url)
    obs.obs_data_set_int(source_settings, "width", 1920)
    obs.obs_data_set_int(source_settings, "height", 200)
    obs.obs_data_set_bool(source_settings, "shutdown", True)
    obs.obs_data_set_bool(source_settings, "restart_when_active", False)

    source = obs.obs_source_create("browser_source", _browser_source_name, source_settings, None)
    if source:
        obs.obs_scene_add(scene, source)
        obs.script_log(obs.LOG_INFO, f"已创建浏览器源: {_browser_source_name}")
        obs.obs_source_release(source)
    else:
        obs.script_log(obs.LOG_ERROR, "创建浏览器源失败")

    obs.obs_data_release(source_settings)
    obs.obs_source_release(current_scene)
    return True


def on_create_dock_clicked(props, prop):
    """打开控制面板"""
    global _script_path
    dock_path = os.path.join(_script_path, "..", "dock", "control_panel.html")
    dock_url = "file:///" + dock_path.replace("\\", "/")

    try:
        obs.obs_frontend_add_dock_widget(_dock_name, dock_url)
        obs.script_log(obs.LOG_INFO, f"已打开控制面板: {_dock_name}")
    except AttributeError:
        obs.script_log(obs.LOG_WARNING, "当前 OBS 版本不支持自动创建停靠窗口")
        obs.script_log(obs.LOG_INFO, f"请手动在 OBS 中打开浏览器停靠窗口，URL: {dock_url}")

    return True
