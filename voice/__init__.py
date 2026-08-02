"""
Voice Package.

Exposes TTSManager, VoiceFactory, BaseVoiceProvider, and custom Voice exceptions.
"""

from voice.exceptions import (
    InvalidVoiceConfiguration,
    VoiceGenerationError,
    VoiceProviderError,
)
from voice.factory import VoiceFactory
from voice.provider import BaseVoiceProvider
from voice.tts import TTSManager

__all__ = [
    "TTSManager",
    "VoiceFactory",
    "BaseVoiceProvider",
    "VoiceProviderError",
    "InvalidVoiceConfiguration",
    "VoiceGenerationError",
]
