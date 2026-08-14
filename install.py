#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBS Live Translate - 一键安装脚本
==================================
将插件文件安装到 OBS 配置目录，实现"复制即用"

用法:
    python install.py

支持平台:
    - Windows
    - Linux
    - macOS (Apple Silicon)
"""

import os
import sys
import shutil
import platform


def get_obs_config_dir():
    """获取 OBS 配置目录"""
    system = platform.system()
    home = os.path.expanduser("~")

    if system == "Windows":
        appdata = os.environ.get("APPDATA", home)
        return os.path.join(appdata, "obs-studio")
    elif system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "obs-studio")
    else:
        config_home = os.environ.get("XDG_CONFIG_HOME", os.path.join(home, ".config"))
        return os.path.join(config_home, "obs-studio")


def install():
    """安装插件到 OBS 目录"""
    print("=" * 60)
    print("  OBS Live Translate - 安装程序")
    print("=" * 60)
    print()

    # 获取路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    obs_dir = get_obs_config_dir()

    print(f"检测到操作系统: {platform.system()}")
    print(f"OBS 配置目录: {obs_dir}")
    print(f"插件目录: {script_dir}")
    print()

    # 检查 OBS 目录是否存在
    if not os.path.exists(obs_dir):
        print(f"⚠️  OBS 配置目录不存在: {obs_dir}")
        print("    请确保已安装 OBS Studio 并运行过一次")
        response = input("    是否继续? (y/N): ")
        if response.lower() != 'y':
            print("安装已取消")
            return
        os.makedirs(obs_dir, exist_ok=True)

    # 安装 OBS Python 脚本
    scripts_dir = os.path.join(obs_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    script_src = os.path.join(script_dir, "obs-script", "obs_live_translate.py")
    script_dst = os.path.join(scripts_dir, "obs_live_translate.py")

    if os.path.exists(script_src):
        shutil.copy2(script_src, script_dst)
        print(f"✅ 已安装 OBS 脚本: {script_dst}")
    else:
        print(f"⚠️  找不到 OBS 脚本: {script_src}")

    # 安装后端程序
    backend_dir = os.path.join(script_dir, "backend")
    if os.path.exists(backend_dir):
        # 找到后端可执行文件
        backend_name = "obs-live-translate"
        if platform.system() == "Windows":
            backend_name += ".exe"

        backend_src = os.path.join(backend_dir, backend_name)
        if os.path.exists(backend_src):
            # 复制整个插件目录到 OBS 配置目录
            plugin_dst = os.path.join(obs_dir, "obs-live-translate")
            if os.path.exists(plugin_dst):
                shutil.rmtree(plugin_dst)
            shutil.copytree(script_dir, plugin_dst, ignore=shutil.ignore_patterns(
                '.git', '__pycache__', '*.pyc', '.github', 'build'
            ))
            print(f"✅ 已安装插件到: {plugin_dst}")
        else:
            print(f"⚠️  找不到后端程序，请先编译")
            print(f"   预期路径: {backend_src}")
    else:
        print(f"⚠️  找不到后端目录: {backend_dir}")
        print("   请先运行编译脚本生成可执行文件")

    print()
    print("=" * 60)
    print("  安装完成!")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. 重启 OBS Studio")
    print("  2. 在 OBS 中打开「工具 → 脚本」")
    print("  3. 加载 obs_live_translate.py")
    print("  4. 配置 API Key 并启动服务")
    print()


if __name__ == "__main__":
    try:
        install()
    except KeyboardInterrupt:
        print("\n安装已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        sys.exit(1)
