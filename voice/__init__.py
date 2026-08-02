"""
Voice Package.

Exposes TTSManager, VoiceFactory, and BaseVoiceProvider for the AI Video Generation Pipeline.
"""

from voice.factory import VoiceFactory
from voice.provider import BaseVoiceProvider
from voice.tts import TTSManager

__all__ = ["TTSManager", "VoiceFactory", "BaseVoiceProvider"]
