"""
Renderer Package.

Exposes VideoRenderer, RendererFactory, BaseRendererProvider, AssetManager,
SceneCompositor, and custom rendering exceptions.
"""

from renderer.asset_manager import AssetManager
from renderer.compositor import SceneCompositor
from renderer.exceptions import (
    InvalidRendererConfiguration,
    RendererError,
    RendererProviderError,
)
from renderer.factory import RendererFactory
from renderer.providers.base import BaseRendererProvider
from renderer.video_renderer import VideoRenderer

__all__ = [
    "VideoRenderer",
    "RendererFactory",
    "BaseRendererProvider",
    "AssetManager",
    "SceneCompositor",
    "RendererError",
    "InvalidRendererConfiguration",
    "RendererProviderError",
]
