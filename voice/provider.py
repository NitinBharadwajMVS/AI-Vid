"""
Voice Provider Module.

Re-exports BaseVoiceProvider for convenient top-level access within the voice package.
"""

from voice.providers.base import BaseVoiceProvider

__all__ = ["BaseVoiceProvider"]
