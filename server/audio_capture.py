"""跨平台系统音频捕获模块"""
import asyncio
import logging
import queue
import sys
import threading

import numpy as np

logger = logging.getLogger(__name__)


class AudioCapture:
    def __init__(self, sample_rate=16000, chunk_duration=1.0):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self._stream = None
        self._running = False
        self._queue = queue.Queue(maxsize=100)
        self._thread = None

    def _get_device_info(self):
        """获取系统音频捕获设备"""
        try:
            import sounddevice as sd

            # 列出所有设备
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()

            candidate = None

            for i, dev in enumerate(devices):
                if dev["max_input_channels"] <= 0:
                    continue

                hostapi = hostapis[dev["hostapi"]]

                if sys.platform == "win32" and "WASAPI" in hostapi["name"]:
                    # Windows: 优先使用 WASAPI 回环设备
                    if "loopback" in dev["name"].lower() or any(
                        kw in dev["name"].lower()
                        for kw in ["立体声混音", "stereo mix", "what u hear"]
                    ):
                        candidate = i
                        break
                    if candidate is None:
                        candidate = i

                elif sys.platform == "darwin":
                    # macOS: 优先使用 BlackHole 或系统音频捕获
                    if any(
                        kw in dev["name"].lower()
                        for kw in ["blackhole", "soundflower", "aggregate"]
                    ):
                        candidate = i
                        break
                    if candidate is None and "macbook" in dev["name"].lower():
                        candidate = i

                else:
                    # Linux: 使用 PulseAudio monitor
                    if "monitor" in dev["name"].lower():
                        candidate = i
                        break
                    if candidate is None:
                        candidate = i

            if candidate is None:
                # 回退到默认输入设备
                candidate = sd.default.device[0] or 0

            return candidate, devices[candidate]

        except ImportError:
            logger.error("sounddevice 未安装，请运行: pip install sounddevice")
            return None, None
        except Exception as e:
            logger.error(f"获取音频设备失败: {e}")
            return None, None

    def _audio_callback(self, indata, frames, time_info, status):
        """音频回调函数"""
        if status:
            logger.warning(f"音频状态: {status}")
        try:
            mono = indata.mean(axis=1) if indata.ndim > 1 else indata.flatten()
            self._queue.put_nowait(mono.copy())
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(mono.copy())

    def start(self):
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice 未安装")
            return False

        device_id, device_info = self._get_device_info()
        if device_id is None:
            logger.error("未找到可用的音频捕获设备")
            return False

        logger.info(f"使用音频设备: [{device_id}] {device_info['name']}")
        logger.info(f"采样率: {self.sample_rate}, 块大小: {self.chunk_size}")

        try:
            self._stream = sd.InputStream(
                device=device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self._audio_callback,
                dtype="float32",
            )
            self._stream.start()
            self._running = True
            logger.info("音频捕获已启动")
            return True
        except Exception as e:
            logger.error(f"启动音频流失败: {e}")
            logger.info(
                "\n提示：\n"
                "  Windows: 请确保启用了立体声混音，或使用 WASAPI 回环\n"
                "  macOS: 请安装 BlackHole (brew install blackhole-2ch)\n"
                "  Linux: 请确保 PulseAudio 正在运行"
            )
            return False

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("音频捕获已停止")

    def read(self, timeout=0.5):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_running(self):
        return self._running
