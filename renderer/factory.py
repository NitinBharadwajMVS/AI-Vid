"""
Renderer Factory Module.

Implements Factory Pattern to instantiate configured BaseRendererProvider instances dynamically.
Decouples PipelineCoordinator and application code from specific video engines.
"""

import logging
from typing import Any, Dict, Type

from renderer.exceptions import InvalidRendererConfiguration
from renderer.providers.base import BaseRendererProvider
from renderer.providers.moviepy import MoviePyRendererProvider

logger = logging.getLogger(__name__)


class RendererFactory:
    """
    Factory class responsible for instantiating BaseRendererProvider implementations based on config.
    """

    _providers: Dict[str, Type[BaseRendererProvider]] = {
        "moviepy": MoviePyRendererProvider,
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseRendererProvider:
        """
        Creates and returns a BaseRendererProvider instance based on configuration dictionary.

        :param config: Configuration dictionary (reads renderer.provider key).
        :return: Instance of BaseRendererProvider.
        :raises InvalidRendererConfiguration: If the requested renderer provider is unsupported.
        """
        config = config or {}
        renderer_cfg = config.get("renderer", {}) if isinstance(config.get("renderer"), dict) else {}
        provider_name = str(renderer_cfg.get("provider", "moviepy")).lower()

        if provider_name not in cls._providers:
            available = list(cls._providers.keys())
            raise InvalidRendererConfiguration(
                f"Unsupported renderer provider '{provider_name}'. Supported providers: {available}"
            )

        provider_cls = cls._providers[provider_name]
        logger.info("RendererFactory instantiated provider: '%s' (%s)", provider_name, provider_cls.__name__)
        return provider_cls(config=config)

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseRendererProvider]) -> None:
        """
        Registers a new BaseRendererProvider implementation into the factory registry.
        """
        if not issubclass(provider_cls, BaseRendererProvider):
            raise TypeError(f"Provider class {provider_cls} must inherit from BaseRendererProvider.")
        cls._providers[name.lower()] = provider_cls
        logger.info("Registered new renderer provider '%s': %s", name, provider_cls.__name__)
