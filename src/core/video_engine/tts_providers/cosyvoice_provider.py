"""
CosyVoice TTS Provider — Alibaba DashScope Voice Cloning.

Key insight: DashScope clone voices get UNDEPLOYED quickly on free tier.
Strategy: register a FRESH voice at the start of each render session, then
synthesize all segments immediately while it's still in DEPLOYING state.
"""

import os
import json
import time
import random
import string
import requests
from .base_tts import BaseTTSProvider


class CosyVoiceTTSProvider(BaseTTSProvider):
    """
    DashScope CosyVoice — voice cloning with your own voice.

    Each render session creates a fresh voice enrollment to avoid
    the UNDEPLOYED issue on free tier.
    """

    MODEL = "cosyvoice-v3.5-plus"
    VOICE_CACHE_FILE = "cosyvoice_voice_id.json"

    def __init__(self, reference_audio_path: str = "", voice_name: str = "lilian_voice"):
        self.reference_audio_path = os.path.abspath(reference_audio_path) if reference_audio_path else ""
        self.voice_name = voice_name
        self._voice_id = None
        self._session_enrolled = False  # Track if we enrolled this session

        # Cache path
        self._cache_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "..", "..",
            "data", "voices", self.VOICE_CACHE_FILE
        )
        self._cache_path = os.path.normpath(self._cache_path)

        # WAV version of the reference audio
        self._wav_path = ""
        if self.reference_audio_path:
            self._wav_path = self.reference_audio_path.rsplit('.', 1)[0] + '.wav'

    def _ensure_wav(self):
        """Convert reference audio to WAV if needed."""
        if os.path.exists(self._wav_path):
            return self._wav_path
        if not self.reference_audio_path or not os.path.exists(self.reference_audio_path):
            raise RuntimeError(f"参考音频不存在: {self.reference_audio_path}")

        print(f"   🔄 转换格式: {os.path.basename(self.reference_audio_path)} → wav")
        import ffmpeg as ffmpeg_lib
        (
            ffmpeg_lib
            .input(self.reference_audio_path)
            .output(self._wav_path, acodec='pcm_s16le', ar=16000, ac=1)
            .overwrite_output()
            .run(quiet=True)
        )
        return self._wav_path

    def _upload_audio(self, wav_path: str) -> str:
        """Upload WAV to a temporary public URL."""
        print(f"   📤 上传参考音频到临时文件服务...")
        with open(wav_path, 'rb') as f:
            r = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': f}, timeout=30)
            r.raise_for_status()
            url = r.json()['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
            print(f"   ✅ 上传完成: {url}")
            return url

    def _fresh_enroll(self):
        """Create a FRESH voice enrollment for this session."""
        from dashscope.audio.tts_v2 import VoiceEnrollmentService

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY 环境变量")

        # Prepare audio
        wav_path = self._ensure_wav()
        audio_url = self._upload_audio(wav_path)

        # Random prefix to avoid collision
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        prefix = f"ll{suffix}"

        print(f"   🎤 注册声音 → {self.MODEL} (prefix={prefix})...")
        service = VoiceEnrollmentService(api_key=api_key)
        voice_id = service.create_voice(
            target_model=self.MODEL,
            prefix=prefix,
            url=audio_url,
            language_hints=['zh'],
        )

        self._voice_id = voice_id
        self._session_enrolled = True
        print(f"   ✅ 声音注册成功: {voice_id}")

        # Brief wait for deployment activation
        time.sleep(1)

        # Save to cache (for reference, though we re-enroll each session)
        os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
        with open(self._cache_path, 'w') as f:
            json.dump({
                'voice_name': self.voice_name,
                'voice_id': voice_id,
                'model': self.MODEL,
            }, f, indent=2)

        return voice_id

    def synthesize(self, text: str, output_path: str, voice: str = "") -> float:
        """Synthesize text using the cloned voice.

        On free tier, each cloned voice can only be used ~1 time before
        becoming UNDEPLOYED. So we re-enroll before each synthesis call.
        """
        from dashscope.audio.tts_v2 import SpeechSynthesizer, VoiceEnrollmentService

        api_key = os.getenv("DASHSCOPE_API_KEY")

        # Ensure audio URL is uploaded (only once per session)
        if not hasattr(self, '_audio_url') or not self._audio_url:
            wav_path = self._ensure_wav()
            self._audio_url = self._upload_audio(wav_path)

        # Create fresh voice enrollment for THIS synthesis call
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        prefix = f"l{suffix}"

        service = VoiceEnrollmentService(api_key=api_key)
        voice_id = service.create_voice(
            target_model=self.MODEL,
            prefix=prefix,
            url=self._audio_url,
            language_hints=['zh'],
        )

        vid_display = voice_id[:35] + "..." if len(voice_id) > 35 else voice_id
        print(f"   🎙️ [CosyVoice] 注册+合成: voice={vid_display}, 文本={len(text)}字")

        # Immediately synthesize (while voice is still DEPLOYING)
        synth = SpeechSynthesizer(model=self.MODEL, voice=voice_id)
        audio_data = synth.call(text)

        if not audio_data or len(audio_data) == 0:
            raise RuntimeError(
                f"CosyVoice 合成失败。"
                f"\nlast_response: {synth.last_response}"
                f"\nvoice_id: {voice_id}"
            )

        with open(output_path, "wb") as f:
            f.write(audio_data)

        duration = self._get_audio_duration(output_path)
        print(f"   ✓ [CosyVoice] 音频生成完毕: {duration:.1f}s → {output_path}")
        return duration

    def _get_audio_duration(self, path: str) -> float:
        """Get audio duration using ffprobe."""
        try:
            import ffmpeg as ffmpeg_lib
            probe = ffmpeg_lib.probe(path)
            return float(probe['format']['duration'])
        except Exception:
            return os.path.getsize(path) / 2000.0

    def get_provider_name(self) -> str:
        return "Alibaba CosyVoice v3.5+ (声音克隆)"

    def list_voices(self) -> list:
        if self._voice_id:
            return [self._voice_id]
        return ["(每次渲染时自动注册)"]
