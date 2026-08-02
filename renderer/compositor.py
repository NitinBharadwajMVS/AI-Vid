"""
Scene Compositor Module.

Responsible for constructing renderable scene layouts.
Queries AssetManager to select and attach visual assets (backgrounds, overlays, icons)
and formats font, text layout, and timing information for rendering.
"""

import logging
from typing import Any, Dict, Optional

from planner.scene_spec import RenderSettings, Scene
from renderer.asset_manager import AssetManager

logger = logging.getLogger(__name__)


class SceneCompositor:
    """
    Constructs renderable layout compositions for individual scenes by coordinating with AssetManager.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        asset_manager: Optional[AssetManager] = None,
    ):
        """
        Initializes SceneCompositor with configuration and AssetManager.

        :param config: Configuration dictionary.
        :param asset_manager: AssetManager instance. If None, instantiates one.
        """
        self.config = config or {}
        self.asset_manager = asset_manager or AssetManager(config=self.config)
        styling = self.config.get("styling", {}) if isinstance(self.config.get("styling"), dict) else {}
        self.font = styling.get("primary_font", "Arial")

    def build_scene_layout(self, scene: Scene, settings: RenderSettings) -> Dict[str, Any]:
        """
        Constructs and returns a complete layout composition dictionary for a scene.
        Queries AssetManager for required visual assets (background, overlays, icons).

        :param scene: Scene object.
        :param settings: RenderSettings object.
        :return: Complete composition layout dictionary.
        """
        scene_id = scene.scene_id or "scene_unknown"
        logger.debug("SceneCompositor building scene layout for Scene ID: '%s'", scene_id)

        # 1. Query AssetManager for required visual assets
        background_asset = self.asset_manager.get_background(scene)
        overlay_asset = self.asset_manager.get_overlay("default")

        # 2. Extract timing and voice info
        audio_path = scene.voice_metadata.audio_file_path if scene.voice_metadata else None
        audio_duration = (
            scene.voice_metadata.audio_duration
            if (scene.voice_metadata and scene.voice_metadata.audio_duration > 0)
            else scene.duration
        )

        scene_title = (
            scene.animation_metadata.get("scene_title", f"Scene {scene_id}")
            if scene.animation_metadata
            else f"Scene {scene_id}"
        )
        on_screen_text = scene.render_options.get("on_screen_text", "") if scene.render_options else ""

        # 3. Assemble complete layout composition data
        return {
            "scene_id": scene_id,
            "title": scene_title,
            "narration": scene.narration_text,
            "on_screen_text": on_screen_text,
            "font": self.font,
            "resolution": settings.resolution,
            "fps": settings.fps,
            "transition_in": scene.transition_in.type if scene.transition_in else "cut",
            "transition_duration": scene.transition_in.duration if scene.transition_in else 0.0,
            "background_asset": background_asset,
            "overlay_asset": overlay_asset,
            "audio_path": audio_path,
            "audio_duration": audio_duration,
            "visual_elements": scene.visual_elements,
        }
