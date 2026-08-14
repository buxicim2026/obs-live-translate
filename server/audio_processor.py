"""语音活动检测(VAD)与音乐检测"""
import logging

import numpy as np

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, sample_rate=16000, silence_threshold=0.02, silence_timeout=2.0):
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_timeout = silence_timeout
        self._silence_frames = 0
        self._frames_per_second = 1
        self._last_rms = 0

    def is_silence(self, audio_chunk):
        """基于RMS能量的静音检测"""
        rms = np.sqrt(np.mean(audio_chunk**2))
        self._last_rms = rms
        rms_db = 20 * np.log10(max(rms, 1e-10))

        if rms < self.silence_threshold:
            self._silence_frames += 1
        else:
            self._silence_frames = max(0, self._silence_frames - 1)

        is_silent = self._silence_frames > self.silence_timeout
        return is_silent, rms_db

    def is_music(self, audio_chunk):
        """基于频谱特征的音乐检测
        
        音乐通常具有：
        1. 更强的谐波结构
        2. 更稳定的基频
        3. 更宽的频谱分布
        4. 更多的周期性峰值
        """
        n = len(audio_chunk)
        if n < 256:
            return False

        fft = np.abs(np.fft.rfft(audio_chunk))
        freqs = np.fft.rfftfreq(n, 1.0 / self.sample_rate)

        # 只分析人声相关频段 (80Hz - 4000Hz)
        voice_mask = (freqs >= 80) & (freqs <= 4000)
        if not voice_mask.any():
            return False

        fft_voice = fft[voice_mask]
        freqs_voice = freqs[voice_mask]

        # 特征1: 频谱平坦度 (Spectral Flatness)
        # 语音通常有较强的共振峰，频谱不平坦
        if len(fft_voice) > 1 and fft_voice.max() > 0:
            geo_mean = np.exp(np.mean(np.log(fft_voice + 1e-10)))
            arith_mean = np.mean(fft_voice)
            spectral_flatness = geo_mean / (arith_mean + 1e-10)
        else:
            spectral_flatness = 1.0

        # 特征2: 峰值数量
        # 音乐通常有更多清晰的峰值
        mean_amp = np.mean(fft_voice)
        std_amp = np.std(fft_voice)
        peaks = fft_voice > (mean_amp + 2 * std_amp)
        peak_ratio = np.sum(peaks) / max(len(peaks), 1)

        # 特征3: 低频能量占比
        low_mask = (freqs_voice >= 80) & (freqs_voice <= 500)
        low_energy = np.sum(fft_voice[low_mask]) if low_mask.any() else 0
        total_energy = np.sum(fft_voice) + 1e-10
        low_energy_ratio = low_energy / total_energy

        # 综合判断
        music_score = 0
        if spectral_flatness < 0.4:
            music_score += 1
        if peak_ratio > 0.05:
            music_score += 1
        if low_energy_ratio > 0.6:
            music_score += 1

        return music_score >= 2

    def get_rms(self):
        """获取最近一次音频块的RMS值"""
        return self._last_rms

    def should_process(self, audio_chunk):
        """判断是否应该处理这个音频块"""
        is_silent, rms_db = self.is_silence(audio_chunk)
        if is_silent:
            return False, "silence"

        is_music = self.is_music(audio_chunk)
        if is_music:
            return False, "music"

        return True, "speech"
