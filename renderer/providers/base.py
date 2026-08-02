"""
Base Renderer Provider Interface.

Defines the abstract interface for all video rendering engines (MoviePy, FFmpeg, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from planner.scene_spec import RenderSettings, Scene


class BaseRendererProvider(ABC):
    """
    Abstract base class for video renderer providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes BaseRendererProvider with configuration settings.
        """
        self.config = config or {}

    @abstractmethod
    def render_scene(
        self, scene: Scene, composition_data: Dict[str, Any], output_path: str
    ) -> str:
        """
        Renders a single scene into an intermediate video clip file using composition layout.

        :param scene: Scene specification object.
        :param composition_data: Complete layout and asset metadata dictionary from SceneCompositor.
        :param output_path: Destination path for rendered scene clip.
        :return: Absolute path to rendered scene video clip file.
        """
        pass

    @abstractmethod
    def composite_video(
        self, scene_video_paths: List[str], output_path: str, settings: RenderSettings
    ) -> str:
        """
        Concatenates rendered scene video clips and applies global render settings to export final MP4.

        :param scene_video_paths: List of file paths to individual scene clips.
        :param output_path: Final MP4 file destination.
        :param settings: RenderSettings object.
        :return: Absolute path to final output video file.
        """
        pass
