"""
Voice Package Custom Exceptions.

Defines dedicated exceptions for voice provider initialization, configuration,
and speech synthesis failures.
"""


class VoiceProviderError(Exception):
    """Base exception for all errors occurring within the Voice module."""
    pass


class InvalidVoiceConfiguration(VoiceProviderError):
    """Raised when voice configuration is missing, invalid, or malformed."""
    pass


class VoiceGenerationError(VoiceProviderError):
    """Raised when speech synthesis fails during audio generation."""
    pass
