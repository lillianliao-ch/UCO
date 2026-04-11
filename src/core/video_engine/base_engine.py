"""
Video Engine Abstract Layer — BaseVideoEngine & Data Contracts.

This module defines the rendering contract that ALL video engines must implement.
Swapping the underlying renderer (FFmpeg, Remotion, Revideo, MoviePy, etc.)
requires only a new subclass and a config change in video_engines.yaml.
Pipelines, prompts, and publishers remain completely untouched.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScriptSegment:
    """A single narration segment of the video script."""
    text: str                                    # TTS narration text for this segment
    visual_text: Optional[str] = None            # On-screen display text (shorter version)
    screenshot_path: Optional[str] = None        # Pre-existing screenshot to overlay (optional)
    duration_hint: Optional[float] = None        # Suggested duration in seconds (overridden by TTS length)


@dataclass
class VideoRenderRequest:
    """Standardized rendering payload passed to any video engine."""
    title: str                                   # Video title (used for title card)
    script_segments: List[ScriptSegment]          # Ordered narration segments
    output_path: str                             # Where to write the final MP4
    resolution: tuple = (1080, 1920)             # (width, height) — default 9:16 vertical
    tts_provider: str = "edge_tts"               # Which TTS backend to use
    tts_voice: str = "zh-CN-XiaoxiaoNeural"      # TTS voice identifier
    reference_audio: str = ""                      # Path to reference audio for voice cloning (CosyVoice)
    background_video: Optional[str] = None       # Path to background video (None = generated gradient)
    background_color: tuple = (18, 18, 24)       # Fallback dark background RGB
    badge_text: str = ""                         # Pipeline badge label on title card
    subtitle_text: str = ""                      # Subtitle under the title


@dataclass
class VideoRenderResult:
    """Rendering result returned by any video engine."""
    success: bool
    video_path: str = ""
    duration_seconds: float = 0.0
    thumbnail_path: str = ""
    error_message: str = ""
    segments_rendered: int = 0


class BaseVideoEngine(ABC):
    """
    Abstract video engine — the strategy interface.

    Any new video rendering backend (Remotion, Revideo, MoviePy, cloud API, etc.)
    should subclass this and implement render(). The engine is selected at runtime
    via config/video_engines.yaml without touching pipeline or prompt code.
    """

    @abstractmethod
    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        """
        Render a video from a structured script.

        Args:
            request: Standardized rendering payload with segments, TTS config, etc.

        Returns:
            VideoRenderResult with the output path, duration, and status.
        """
        pass

    @abstractmethod
    def get_supported_tts(self) -> List[str]:
        """Return a list of TTS provider IDs this engine supports."""
        pass

    def get_engine_name(self) -> str:
        """Human-readable name for logging."""
        return self.__class__.__name__
