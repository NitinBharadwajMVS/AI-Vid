"""
Voice Factory Module.

Implements Factory Pattern to instantiate configured VoiceProvider instances dynamically.
Decouples application code and PipelineCoordinator from specific provider implementations.
"""

import logging
from typing import Any, Dict, Type

from voice.exceptions import InvalidVoiceConfiguration
from voice.providers.base import BaseVoiceProvider
from voice.providers.piper import PiperVoiceProvider

logger = logging.getLogger(__name__)


class VoiceFactory:
    """
    Factory class responsible for instantiating BaseVoiceProvider implementations based on configuration.
    """

    _providers: Dict[str, Type[BaseVoiceProvider]] = {
        "piper": PiperVoiceProvider,
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseVoiceProvider:
        """
        Creates and returns a BaseVoiceProvider instance based on the configuration dictionary.

        :param config: Configuration dictionary (reads voice.provider key).
        :return: Instance of BaseVoiceProvider.
        :raises InvalidVoiceConfiguration: If the requested voice provider is unsupported or missing.
        """
        config = config or {}
        voice_cfg = config.get("voice", {}) if isinstance(config.get("voice"), dict) else {}
        provider_name = str(voice_cfg.get("provider", "piper")).lower()

        if provider_name not in cls._providers:
            available = list(cls._providers.keys())
            raise InvalidVoiceConfiguration(
                f"Unsupported voice provider '{provider_name}'. Supported providers: {available}"
            )

        provider_cls = cls._providers[provider_name]
        logger.info("VoiceFactory instantiated provider: '%s' (%s)", provider_name, provider_cls.__name__)
        return provider_cls(config=config)

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseVoiceProvider]) -> None:
        """
        Registers a new BaseVoiceProvider implementation into the factory registry.

        :param name: String key identifier for the provider (e.g., 'elevenlabs', 'azure').
        :param provider_cls: Concrete class inheriting from BaseVoiceProvider.
        """
        if not issubclass(provider_cls, BaseVoiceProvider):
            raise TypeError(f"Provider class {provider_cls} must inherit from BaseVoiceProvider.")
        cls._providers[name.lower()] = provider_cls
        logger.info("Registered new voice provider '%s': %s", name, provider_cls.__name__)
