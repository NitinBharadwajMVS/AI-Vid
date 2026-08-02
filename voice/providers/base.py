"""
Base Voice Provider Interface.

Defines the abstract interface that all Text-to-Speech (TTS) engine providers
(e.g., Piper, ElevenLabs, Azure, Google, Coqui) must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from planner.scene_spec import VoiceMetadata


class BaseVoiceProvider(ABC):
    """
    Abstract Base Class for Voice / TTS Providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the provider with configuration settings.

        :param config: Configuration dictionary for voice settings.
        """
        self.config = config or {}

    @abstractmethod
    def synthesize(
        self, text: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> VoiceMetadata:
        """
        Synthesizes speech for the given narration text and outputs an audio file.

        :param text: Narration text to synthesize.
        :param output_path: File path where the output audio file should be written.
        :param options: Optional per-generation parameter overrides.
        :return: Populated VoiceMetadata object containing generation results.
        """
        pass
