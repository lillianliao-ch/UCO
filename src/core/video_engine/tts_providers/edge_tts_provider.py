"""
Edge TTS Provider — Microsoft Edge Text-to-Speech.

Free, high quality, supports Chinese and English with many voice options.
No API key required. Uses the edge-tts Python package.
"""

import asyncio
import os
from .base_tts import BaseTTSProvider


class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge TTS — free, high quality, excellent Chinese support.
    
    Default voice: zh-CN-XiaoxiaoNeural (female, natural, sweet)
    Alternative voices:
        - zh-CN-YunxiNeural (male, mature, steady)
        - zh-CN-YunjianNeural (male, authoritative)
        - en-US-JennyNeural (English female)
        - en-US-GuyNeural (English male)
    """

    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

    def synthesize(self, text: str, output_path: str, voice: str = "") -> float:
        """Synthesize text to MP3 using Edge TTS. Returns duration in seconds."""
        import edge_tts

        voice = voice or self.DEFAULT_VOICE
        print(f"   🎙️ [Edge TTS] 合成语音: voice={voice}, 文本长度={len(text)} 字")

        communicate = edge_tts.Communicate(text, voice)
        asyncio.run(communicate.save(output_path))

        # Get duration from the generated file
        duration = self._get_audio_duration(output_path)
        print(f"   ✓ [Edge TTS] 音频生成完毕: {duration:.1f}s → {output_path}")
        return duration

    def _get_audio_duration(self, path: str) -> float:
        """Get audio duration using ffprobe."""
        try:
            import ffmpeg
            probe = ffmpeg.probe(path)
            return float(probe['format']['duration'])
        except Exception:
            # Fallback: estimate from file size (~16kbps for edge-tts MP3)
            size = os.path.getsize(path)
            return size / 2000.0

    def get_provider_name(self) -> str:
        return "Microsoft Edge TTS"

    def list_voices(self) -> list:
        return [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-YunxiNeural",
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoyiNeural",
            "en-US-JennyNeural",
            "en-US-GuyNeural",
            "en-US-AriaNeural",
            "ja-JP-NanamiNeural",
        ]
