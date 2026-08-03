"""
Video Renderer Module.

High-level entry point for video rendering.
Iterates over SceneSpecification scenes, delegates layout composition to SceneCompositor,
and invokes BaseRendererProvider to generate the output MP4.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from planner.scene_spec import SceneSpecification
from renderer.compositor import SceneCompositor
from renderer.exceptions import RendererError
from renderer.factory import RendererFactory
from renderer.providers.base import BaseRendererProvider

logger = logging.getLogger(__name__)


class VideoRenderer:
    """
    Coordinates end-to-end video rendering from SceneSpecification.
    """

    def __init__(
        self,
        provider: Optional[BaseRendererProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        compositor: Optional[SceneCompositor] = None,
    ):
        """
        Initializes VideoRenderer with provider and compositor.

        :param provider: Concrete BaseRendererProvider instance. If None, uses RendererFactory.
        :param config: Configuration dictionary.
        :param compositor: SceneCompositor instance. If None, instantiates one.
        """
        self.config = config or {}
        self.provider = provider or RendererFactory.create(self.config)
        self.compositor = compositor or SceneCompositor(config=self.config)
        logger.info("VideoRenderer initialized with provider: %s", self.provider.__class__.__name__)

    def render(self, scene_spec: SceneSpecification, output_path: str) -> str:
        """
        Renders the SceneSpecification into an MP4 video file.

        :param scene_spec: SceneSpecification containing scene details and voice_metadata.
        :param output_path: Target path for the exported MP4 video.
        :return: Absolute file path to exported MP4 video.
        :raises RendererError: If scene_spec is invalid or rendering fails.
        """
        if not scene_spec or not isinstance(scene_spec, SceneSpecification):
            raise RendererError("Invalid SceneSpecification provided to VideoRenderer.")

        if not scene_spec.scenes:
            raise RendererError("SceneSpecification contains 0 scenes. Cannot render video.")

        logger.info("Starting rendering pipeline for %d scenes.", len(scene_spec.scenes))
        export_start_time = time.time()

        temp_dir = Path(self.config.get("paths", {}).get("temp", "./temp")) / "rendered_scenes"
        temp_dir.mkdir(parents=True, exist_ok=True)

        rendered_clip_paths = []

        for idx, scene in enumerate(scene_spec.scenes, 1):
            scene_id = scene.scene_id or f"scene_{idx:03d}"
            logger.info("Scene currently rendering: '%s' (%d/%d)", scene_id, idx, len(scene_spec.scenes))

            # 1. Build layout composition via SceneCompositor (which queries AssetManager)
            comp_data = self.compositor.build_scene_layout(scene, scene_spec.global_render_settings)
            comp_data["total_scenes"] = len(scene_spec.scenes)
            comp_data["scene_index"] = idx

            # 2. Render individual scene clip via provider using comp_data
            scene_clip_path = str(temp_dir / f"{scene_id}_clip.mp4")
            start_scene_time = time.time()

            try:
                rendered_clip = self.provider.render_scene(
                    scene=scene,
                    composition_data=comp_data,
                    output_path=scene_clip_path,
                )
                scene_duration = time.time() - start_scene_time
                logger.info(
                    "Scene rendered: '%s' in %.4fs (Scene duration: %.2fs, Clip: '%s')",
                    scene_id,
                    scene_duration,
                    scene.duration,
                    rendered_clip,
                )
                rendered_clip_paths.append(rendered_clip)
            except Exception as e:
                logger.error("Failed to render scene '%s': %s", scene_id, e)
                raise RendererError(f"Rendering failed for scene '{scene_id}': {e}") from e

        # 3. Composite and export final video
        logger.info("Export started: Concatenating %d scene clips to '%s'...", len(rendered_clip_paths), output_path)
        try:
            final_mp4 = self.provider.composite_video(
                scene_video_paths=rendered_clip_paths,
                output_path=output_path,
                settings=scene_spec.global_render_settings,
            )
            total_export_duration = time.time() - export_start_time
            logger.info("Export completed in %.4fs. Output file: '%s'", total_export_duration, final_mp4)
            return final_mp4
        except Exception as e:
            logger.error("Final export concatenation failed: %s", e)
            raise RendererError(f"Export failed for target file '{output_path}': {e}") from e
