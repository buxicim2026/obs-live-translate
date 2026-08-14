"""大模型API调用模块 - 支持Qwen等兼容OpenAI接口的模型"""
import asyncio
import base64
import io
import json
import logging
import wave

import aiohttp

logger = logging.getLogger(__name__)


class LiveTranslator:
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._session = None
        self._target_language = "zh"

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    def _audio_to_base64(self, audio_data, sample_rate=16000):
        """将numpy音频数据转换为WAV格式的base64"""
        import numpy as np

        audio_int16 = (audio_data * 32767).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def transcribe_and_translate(self, audio_data, source_lang=None):
        """
        发送音频到API进行转录和翻译
        返回: {"text": "识别/翻译文本", "source_lang": "源语言", "is_translated": bool}
        """
        session = await self._get_session()
        audio_b64 = self._audio_to_base64(audio_data)

        # 构建系统提示词
        system_prompt = (
            "你是一个实时语音翻译助手。你的任务是：\n"
            "1. 如果输入是中文，直接输出中文原文\n"
            "2. 如果输入是其他语言，翻译成中文输出\n"
            "3. 只输出翻译结果，不要添加任何解释\n"
            "4. 保持口语化，适合字幕显示"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:audio/wav;base64,{audio_b64}",
                            "format": "wav",
                        },
                    },
                    {
                        "type": "text",
                        "text": "请将这段音频转换成中文文本。如果是中文就直接输出，如果是其他语言就翻译成中文。",
                    },
                ],
            },
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.1,
            "stream": False,
        }

        try:
            url = f"{self.base_url}/chat/completions"
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    text = result["choices"][0]["message"]["content"].strip()

                    is_translated = False
                    detected_lang = source_lang or "auto"
                    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
                        if source_lang and source_lang != "zh":
                            is_translated = True
                    else:
                        is_translated = True

                    return {
                        "text": text,
                        "source_lang": detected_lang,
                        "is_translated": is_translated,
                    }
                else:
                    error_text = await resp.text()
                    logger.error(f"API错误 ({resp.status}): {error_text[:500]}")
                    return None

        except asyncio.TimeoutError:
            logger.error("API请求超时")
            return None
        except Exception as e:
            logger.error(f"API请求异常: {e}")
            return None

    async def detect_language(self, text):
        """检测文本语言"""
        chinese_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        japanese_chars = sum(
            1 for ch in text if "\u3040" <= ch <= "\u309f" or "\u30a0" <= ch <= "\u30ff"
        )
        korean_chars = sum(1 for ch in text if "\uac00" <= ch <= "\ud7af")

        if chinese_chars > len(text) * 0.3:
            return "zh"
        if japanese_chars > len(text) * 0.3:
            return "ja"
        if korean_chars > len(text) * 0.3:
            return "ko"

        if any("\u0041" <= ch <= "\u007a" for ch in text):
            return "en"

        return "unknown"

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
