"""
Google TTS Provider — gTTS fallback.

Zero-config, no API key, basic quality.
Serves as the last-resort fallback when Edge TTS is unavailable.
"""

import os
from .base_tts import BaseTTSProvider


class GTTSProvider(BaseTTSProvider):
    """
    Google Translate TTS — simple, free, zero-config fallback.
    
    Quality is lower than Edge TTS but works anywhere with internet.
    """

    def synthesize(self, text: str, output_path: str, voice: str = "") -> float:
        """Synthesize text to MP3 using Google TTS. Returns duration in seconds."""
        from gtts import gTTS

        lang = "zh-cn" if voice.startswith("zh") or not voice else "en"
        print(f"   🎙️ [gTTS] 合成语音: lang={lang}, 文本长度={len(text)} 字")

        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)

        duration = self._get_audio_duration(output_path)
        print(f"   ✓ [gTTS] 音频生成完毕: {duration:.1f}s → {output_path}")
        return duration

    def _get_audio_duration(self, path: str) -> float:
        """Get audio duration using ffprobe."""
        try:
            import ffmpeg
            probe = ffmpeg.probe(path)
            return float(probe['format']['duration'])
        except Exception:
            size = os.path.getsize(path)
            return size / 2000.0

    def get_provider_name(self) -> str:
        return "Google Translate TTS"

    def list_voices(self) -> list:
        return ["zh-cn", "en", "ja", "ko"]
