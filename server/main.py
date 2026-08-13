# server/main.py
"""OBS Live Translate - 实时字幕翻译插件主程序"""
import asyncio
import json
import logging
import os
import signal
import sys
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("obs-live-translate")


async def main():
    from audio_capture import AudioCapture
    from audio_processor import AudioProcessor
    from config import DEFAULT_CONFIG, load_config, save_config
    from translator import LiveTranslator
    from websocket_server import SubtitleWebSocketServer

    print("=" * 60)
    print("  OBS Live Translate - 实时字幕翻译插件")
    print("=" * 60)

    config = load_config()

    # 检查API Key
    if not config.get("api_key"):
        print("\n⚠️  未配置API Key!")
        print("请通过控制面板或编辑配置文件设置API Key")
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
        )
        print(f"配置文件位置: {config_path}")
        print()

    # 启动WebSocket服务器
    ws_server = SubtitleWebSocketServer(
        host="127.0.0.1", port=config["websocket_port"]
    )
    await ws_server.start()

    # 初始化翻译器
    translator = LiveTranslator(
        api_key=config.get("api_key", ""),
        base_url=config["api_base_url"],
        model=config["model"],
    )

    # 初始化音频处理器
    audio_proc = AudioProcessor(
        sample_rate=config["sample_rate"],
        silence_threshold=config["silence_threshold"],
        silence_timeout=config["silence_timeout"],
    )

    # 初始化音频捕获
    audio_capture = AudioCapture(
        sample_rate=config["sample_rate"],
        chunk_duration=config["chunk_duration"],
    )

    if not audio_capture.start():
        logger.error("无法启动音频捕获，请检查音频设备配置")
        print("\n按 Ctrl+C 退出...")
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        return

    logger.info("实时字幕翻译服务已就绪!")
    logger.info(f"WebSocket: ws://127.0.0.1:{config['websocket_port']}")
    print()
    print("📋 OBS 设置步骤:")
    print("  1. 添加「浏览器」源")
    print(f"  2. URL 设为: http://127.0.0.1:{config['websocket_port']}/subtitle")
    print("  3. 宽度: 1920, 高度: 200")
    print("  4. 勾选「通过OC关闭源时刷新浏览器」")
    print()
    print("按 Ctrl+C 停止服务...")
    print()

    # 主循环
    loop = asyncio.get_event_loop()
    running = True

    def shutdown():
        nonlocal running
        running = False
        logger.info("正在关闭服务...")

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass

    last_text = ""
    audio_buffer = []
    buffer_max_chunks = 5

    try:
        while running:
            audio_chunk = audio_capture.read(timeout=0.1)

            if audio_chunk is not None:
                should_proc, reason = audio_proc.should_process(audio_chunk)

                if should_proc:
                    audio_buffer.append(audio_chunk)
                    if len(audio_buffer) >= buffer_max_chunks:
                        import numpy as np

                        combined = np.concatenate(audio_buffer)
                        audio_buffer.clear()

                        result = await translator.transcribe_and_translate(combined)
                        if result and result["text"]:
                            text = result["text"].strip()
                            if text and text != last_text:
                                last_text = text
                                await ws_server.broadcast_subtitle(text, is_final=True)
                                logger.info(
                                    f"字幕: {text} [{result['source_lang']}]"
                                )

                await ws_server.broadcast_status(
                    {
                        "status": "running",
                        "audio_level": float(audio_proc.get_rms()),
                        "detection": reason,
                    }
                )

            await asyncio.sleep(0.01)

    except asyncio.CancelledError:
        pass
    finally:
        logger.info("正在停止服务...")
        audio_capture.stop()
        await translator.close()
        await ws_server.stop()
        logger.info("服务已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
