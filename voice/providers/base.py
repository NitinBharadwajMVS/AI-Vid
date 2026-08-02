"""
Base Voice Provider Interface.

Defines the abstract interface that all Text-to-Speech (TTS) engine providers
(e.g., Piper, ElevenLabs, Azure, Google, Coqui) must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseVoiceProvider(ABC):
    """
    Abstract Base Class for Voice / TTS Providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the provider with configuration.

        :param config: Configuration dictionary for voice settings.
        """
        self.config = config or {}

    @abstractmethod
    def generate_audio(
        self, text: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates audio for the given text script and writes to output_path.

        :param text: Narration text to synthesize.
        :param output_path: File path where the output WAV/MP3 file should be saved.
        :param options: Optional per-generation override parameters.
        :return: Dictionary containing generation metadata (e.g. audio_file_path, audio_duration, sample_rate, provider, voice_id).
        """
        pass
