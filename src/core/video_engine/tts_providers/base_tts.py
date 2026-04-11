"""
TTS Provider Abstract Layer — BaseTTSProvider.

Each TTS backend (Edge TTS, Google TTS, ElevenLabs, OpenAI, etc.)
implements this interface. Engines load TTS providers by name from config.
"""

from abc import ABC, abstractmethod


class BaseTTSProvider(ABC):
    """
    Abstract TTS provider — the inner strategy for audio synthesis.

    Subclasses must implement synthesize() which converts text to an audio file
    and returns the duration in seconds.
    """

    @abstractmethod
    def synthesize(self, text: str, output_path: str, voice: str = "") -> float:
        """
        Convert text to speech and save as an audio file.

        Args:
            text: The narration text to synthesize.
            output_path: Where to save the audio file (MP3).
            voice: Voice identifier (provider-specific).

        Returns:
            Duration of the generated audio in seconds.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Human-readable provider name for logging."""
        pass

    @abstractmethod
    def list_voices(self) -> list:
        """Return available voice identifiers for this provider."""
        pass
