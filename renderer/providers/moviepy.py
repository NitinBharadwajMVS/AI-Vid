"""
MoviePy Renderer Provider Implementation.

Implements BaseRendererProvider using the MoviePy engine.
Renders individual scene MP4 clips (solid background, centered title, wrapped narration text,
bottom left scene numbers, bottom right AI-vid branding, and narration audio)
and concatenates scene clips into the final video file.
"""

import logging
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from planner.scene_spec import RenderSettings, Scene
from renderer.exceptions import RendererError, RendererProviderError
from renderer.providers.base import BaseRendererProvider

logger = logging.getLogger(__name__)


class MoviePyRendererProvider(BaseRendererProvider):
    """
    MoviePy implementation of BaseRendererProvider.
    Renders structured educational video layouts:
      - Scene title (top center, wrapped, dynamically scaled)
      - Reserved image / visual asset container area (center)
      - Multiline narration text (bottom center, wrapped, dynamically scaled)
      - Footer (bottom left: Scene X / Total, bottom right: AI-vid)
      - Narration audio attachment & clip concatenation
    """

    # Structured Educational Video Layout Constants (Ratios relative to resolution width/height)
    TITLE_TOP_RATIO = 0.08
    TITLE_MAX_WIDTH_RATIO = 0.80

    IMAGE_AREA_TOP_RATIO = 0.22
    IMAGE_AREA_WIDTH_RATIO = 0.60
    IMAGE_AREA_HEIGHT_RATIO = 0.38
    IMAGE_AREA_BG_COLOR = (24, 28, 38)  # Dark card canvas reserved for visual assets

    BODY_TEXT_TOP_RATIO = 0.64
    BODY_TEXT_MAX_WIDTH_RATIO = 0.70

    FOOTER_BOTTOM_RATIO = 0.91
    FOOTER_MARGIN_RATIO = 0.10
    FOOTER_COLOR = "#A0A0A0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes MoviePyRendererProvider with configuration settings.

        :param config: Configuration dictionary for renderer and styling settings.
        """
        super().__init__(config)
        renderer_cfg = self.config.get("renderer", {}) if isinstance(self.config.get("renderer"), dict) else {}
        styling_cfg = self.config.get("styling", {}) if isinstance(self.config.get("styling"), dict) else {}

        self.resolution_str = str(renderer_cfg.get("resolution", "1920x1080"))
        self.resolution = self._parse_resolution(self.resolution_str)
        self.fps = int(renderer_cfg.get("fps", 30))
        self.codec = str(renderer_cfg.get("codec", "libx264"))
        self.bitrate = str(renderer_cfg.get("bitrate", "5000k"))
        self.bg_color_hex = str(renderer_cfg.get("background_color", "#000000"))
        self.bg_color_rgb = self._hex_to_rgb(self.bg_color_hex)

        self.primary_font = str(styling_cfg.get("primary_font", "Arial"))
        self.secondary_font = str(styling_cfg.get("secondary_font", "Roboto"))
        self.title_font_size = int(styling_cfg.get("title_font_size", 48))
        self.body_font_size = int(styling_cfg.get("body_font_size", 24))
        self.text_color = str(styling_cfg.get("text_color", "#FFFFFF"))

    def render_scene(
        self, scene: Scene, composition_data: Dict[str, Any], output_path: str
    ) -> str:
        """
        Renders a single video scene with responsive educational layout into an MP4 clip.

        :param scene: Scene object containing narration and voice metadata.
        :param composition_data: Complete composition layout dictionary built by SceneCompositor.
        :param output_path: Output file destination for this scene clip.
        :return: Absolute file path to rendered clip.
        :raises RendererError: If audio file is missing, output directory is unwritable, or rendering fails.
        """
        scene_id = scene.scene_id or composition_data.get("scene_id", "scene_unknown")
        logger.info("Scene rendering started for Scene ID '%s'...", scene_id)

        # 1. Verify audio file existence
        audio_path_str = composition_data.get("audio_path")
        if not audio_path_str and scene.voice_metadata:
            audio_path_str = scene.voice_metadata.audio_file_path

        if not audio_path_str:
            reason = f"Audio file is missing for scene '{scene_id}'"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason)

        audio_file_path = Path(audio_path_str)
        if not audio_file_path.exists() or not audio_file_path.is_file():
            reason = f"Audio file missing at path: '{audio_path_str}' for scene '{scene_id}'"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason)

        # 2. Load narration audio clip
        try:
            audio_clip = AudioFileClip(str(audio_file_path))
            logger.info(
                "Audio loaded for scene '%s': '%s' (duration: %.2fs)",
                scene_id,
                audio_path_str,
                audio_clip.duration,
            )
        except Exception as e:
            reason = f"Failed to load audio file '{audio_path_str}' for scene '{scene_id}': {e}"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason) from e

        duration = audio_clip.duration
        if duration <= 0:
            duration = float(composition_data.get("audio_duration", scene.duration))
        if duration <= 0:
            duration = 3.0

        # 3. Solid Background Canvas
        width, height = self.resolution
        bg_clip = ColorClip(size=(width, height), color=self.bg_color_rgb, duration=duration)
        clips = [bg_clip]

        # 4. Render Scene Title (Top Center, Wrapped, Scaled)
        scene_title = composition_data.get("title") or getattr(scene, "title", f"Scene {scene_id}")
        title_font = self._resolve_font(self.primary_font)

        if scene_title and scene_title.strip():
            title_str = scene_title.strip()
            max_title_width_px = int(width * self.TITLE_MAX_WIDTH_RATIO)

            title_font_size = self.title_font_size
            title_char_w = max(1, int(title_font_size * 0.55))
            title_max_chars = max(15, int(max_title_width_px / title_char_w))

            title_lines = textwrap.wrap(title_str, width=title_max_chars, break_long_words=False)
            if not title_lines:
                title_lines = [title_str]

            if len(title_lines) > 2:
                title_font_size = int(self.title_font_size * 0.80)
                title_char_w = max(1, int(title_font_size * 0.55))
                title_max_chars = max(15, int(max_title_width_px / title_char_w))
                title_lines = textwrap.wrap(title_str, width=title_max_chars, break_long_words=False)

            wrapped_title = "\n".join(title_lines)
            logger.info("Title wrapped for scene '%s': %d lines", scene_id, len(title_lines))

            try:
                title_clip = (
                    TextClip(
                        text=wrapped_title,
                        font=title_font,
                        font_size=title_font_size,
                        color=self.text_color,
                        text_align="center",
                    )
                    .with_duration(duration)
                    .with_position(("center", int(height * self.TITLE_TOP_RATIO)))
                )
                clips.append(title_clip)
            except Exception as e:
                logger.warning("Could not render title TextClip for scene '%s': %s", scene_id, e)

        # 5. Reserved Center Image / Visual Asset Region
        img_area_w = int(width * self.IMAGE_AREA_WIDTH_RATIO)
        img_area_h = int(height * self.IMAGE_AREA_HEIGHT_RATIO)
        img_area_top = int(height * self.IMAGE_AREA_TOP_RATIO)

        bg_asset = composition_data.get("background_asset", {})
        image_clip = None

        if isinstance(bg_asset, dict) and bg_asset.get("image_path") and Path(bg_asset["image_path"]).exists():
            try:
                from moviepy import ImageClip
                image_clip = (
                    ImageClip(bg_asset["image_path"])
                    .with_duration(duration)
                    .resized(height=img_area_h)
                    .with_position(("center", img_area_top))
                )
                clips.append(image_clip)
            except Exception as e:
                logger.warning("Could not load image asset '%s': %s", bg_asset.get("image_path"), e)

        if not image_clip:
            # Reserved placeholder card for future AI-generated visual assets
            placeholder_clip = (
                ColorClip(size=(img_area_w, img_area_h), color=self.IMAGE_AREA_BG_COLOR, duration=duration)
                .with_position(("center", img_area_top))
            )
            clips.append(placeholder_clip)

        # 6. Narration Text Wrapping & Dynamic Font Scaling (Bottom Portion)
        raw_narration = (
            composition_data.get("on_screen_text")
            or composition_data.get("narration")
            or scene.narration_text
            or ""
        ).strip()

        body_font = self._resolve_font(self.secondary_font)

        if raw_narration:
            max_body_width_px = int(width * self.BODY_TEXT_MAX_WIDTH_RATIO)
            body_font_size = self.body_font_size

            char_w = max(1, int(body_font_size * 0.55))
            max_chars_per_line = max(20, int(max_body_width_px / char_w))

            wrapped_lines = []
            for paragraph in raw_narration.splitlines():
                para_clean = paragraph.strip()
                if para_clean:
                    wrapped_lines.extend(
                        textwrap.wrap(para_clean, width=max_chars_per_line, break_long_words=False)
                    )

            if not wrapped_lines:
                wrapped_lines = [raw_narration]

            if len(wrapped_lines) > 3:
                body_font_size = int(self.body_font_size * 0.85)
                char_w = max(1, int(body_font_size * 0.55))
                max_chars_per_line = max(20, int(max_body_width_px / char_w))
                wrapped_lines = []
                for paragraph in raw_narration.splitlines():
                    para_clean = paragraph.strip()
                    if para_clean:
                        wrapped_lines.extend(
                            textwrap.wrap(para_clean, width=max_chars_per_line, break_long_words=False)
                        )

            wrapped_narration = "\n".join(wrapped_lines)
            logger.info("Wrapped narration generated for scene '%s': %d lines", scene_id, len(wrapped_lines))

            try:
                body_clip = (
                    TextClip(
                        text=wrapped_narration,
                        font=body_font,
                        font_size=body_font_size,
                        color=self.text_color,
                        text_align="center",
                    )
                    .with_duration(duration)
                    .with_position(("center", int(height * self.BODY_TEXT_TOP_RATIO)))
                )
                clips.append(body_clip)
            except Exception as e:
                logger.warning("Could not render narration TextClip for scene '%s': %s", scene_id, e)

        # 7. Render Footer Overlay (Bottom Left: Scene Counter, Bottom Right: AI-vid)
        scene_idx = composition_data.get("scene_index")
        total_scenes = composition_data.get("total_scenes")

        if not scene_idx:
            digits = re.findall(r"\d+", str(scene_id))
            scene_num_str = str(int(digits[0])) if digits else "1"
        else:
            scene_num_str = str(scene_idx)

        footer_left_text = (
            f"Scene {scene_num_str} / {total_scenes}" if total_scenes else f"Scene {scene_num_str}"
        )
        footer_right_text = "AI-vid"

        footer_font_size = max(14, int(self.body_font_size * 0.70))
        footer_y = int(height * self.FOOTER_BOTTOM_RATIO)
        margin_x = int(width * self.FOOTER_MARGIN_RATIO)

        try:
            footer_left_clip = (
                TextClip(
                    text=footer_left_text,
                    font=body_font,
                    font_size=footer_font_size,
                    color=self.FOOTER_COLOR,
                    text_align="left",
                )
                .with_duration(duration)
                .with_position((margin_x, footer_y))
            )
            clips.append(footer_left_clip)

            footer_right_clip = (
                TextClip(
                    text=footer_right_text,
                    font=body_font,
                    font_size=footer_font_size,
                    color=self.FOOTER_COLOR,
                    text_align="right",
                )
                .with_duration(duration)
            )
            right_x = width - margin_x - footer_right_clip.w
            footer_right_clip = footer_right_clip.with_position((right_x, footer_y))
            clips.append(footer_right_clip)
        except Exception as e:
            logger.warning("Could not render footer TextClips for scene '%s': %s", scene_id, e)

        logger.info("Text rendered for scene '%s'", scene_id)
        logger.info("Scene layout prepared successfully for scene '%s'", scene_id)

        # 7. Composite scene elements and attach audio clip
        composite = CompositeVideoClip(clips).with_duration(duration).with_audio(audio_clip)

        out_path = Path(output_path)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            reason = f"Output directory cannot be created at '{out_path.parent}': {e}"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason) from e

        # 8. Export scene MP4 video clip atomically
        tmp_out_path = out_path.with_suffix(".tmp.mp4")
        if tmp_out_path.exists():
            try:
                tmp_out_path.unlink()
            except Exception:
                pass

        try:
            composite.write_videofile(
                str(tmp_out_path),
                fps=self.fps,
                codec=self.codec,
                bitrate=self.bitrate,
                logger=None,
            )
            if out_path.exists():
                try:
                    out_path.unlink()
                except Exception:
                    pass
            tmp_out_path.replace(out_path)
        except Exception as e:
            if tmp_out_path.exists():
                try:
                    tmp_out_path.unlink()
                except Exception:
                    pass
            reason = f"MoviePy export failed for scene clip '{output_path}': {e}"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason) from e
        finally:
            try:
                composite.close()
                audio_clip.close()
            except Exception:
                pass

        if not out_path.exists() or not out_path.is_file():
            reason = f"Output scene clip file was not generated at '{output_path}'"
            logger.error("Scene render failure: %s", reason)
            raise RendererError(reason)

        logger.info("Scene exported for Scene ID '%s' to '%s'", scene_id, str(out_path.resolve()))
        return str(out_path.resolve())

    def composite_video(
        self, scene_video_paths: List[str], output_path: str, settings: RenderSettings
    ) -> str:
        """
        Concatenates individual scene clips and exports final MP4 video.

        :param scene_video_paths: List of rendered scene video paths.
        :param output_path: Target path for the final MP4 video.
        :param settings: RenderSettings object.
        :return: Absolute file path to the completed MP4.
        :raises RendererError: If scene_video_paths is empty or export fails.
        """
        if not scene_video_paths:
            reason = "Cannot composite empty list of scene video paths."
            logger.error("Video concatenation failure: %s", reason)
            raise RendererProviderError(reason)

        clips: List[VideoFileClip] = []
        for p in scene_video_paths:
            path = Path(p)
            if not path.exists() or not path.is_file():
                reason = f"Scene clip file missing at path: '{p}'"
                logger.error("Video concatenation failure: %s", reason)
                raise RendererError(reason)
            try:
                clips.append(VideoFileClip(str(path)))
            except Exception as e:
                # Remove corrupted scene clip file (e.g. missing moov atom from aborted run)
                logger.warning(
                    "Corrupted scene clip detected at '%s' (%s). Removing corrupted clip file.", p, e
                )
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
                reason = f"Failed to load scene clip file '{p}': {e}. Corrupted file removed."
                logger.error("Video concatenation failure: %s", reason)
                raise RendererError(reason) from e

        fps = getattr(settings, "fps", self.fps) or self.fps
        out_path = Path(output_path)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            reason = f"Output directory cannot be created at '{out_path.parent}': {e}"
            logger.error("Video concatenation failure: %s", reason)
            raise RendererError(reason) from e

        tmp_out_path = out_path.with_suffix(".tmp.mp4")
        if tmp_out_path.exists():
            try:
                tmp_out_path.unlink()
            except Exception:
                pass

        try:
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(
                str(tmp_out_path),
                fps=fps,
                codec=self.codec,
                bitrate=self.bitrate,
                logger=None,
            )
            if out_path.exists():
                try:
                    out_path.unlink()
                except Exception:
                    pass
            tmp_out_path.replace(out_path)
        except Exception as e:
            if tmp_out_path.exists():
                try:
                    tmp_out_path.unlink()
                except Exception:
                    pass
            reason = f"MoviePy concatenation export failed for target video '{output_path}': {e}"
            logger.error("Video concatenation failure: %s", reason)
            raise RendererError(reason) from e
        finally:
            for clip in clips:
                try:
                    clip.close()
                except Exception:
                    pass
            try:
                final_clip.close()
            except Exception:
                pass

        if not out_path.exists() or not out_path.is_file():
            reason = f"Final output video file was not generated at '{output_path}'"
            logger.error("Video concatenation failure: %s", reason)
            raise RendererError(reason)

        logger.info("Final video exported to '%s'", str(out_path.resolve()))
        return str(out_path.resolve())

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _parse_resolution(self, res_str: str) -> Tuple[int, int]:
        """Parses resolution string formatted as 'WIDTHxHEIGHT'."""
        try:
            w, h = res_str.lower().split("x")
            return int(w), int(h)
        except Exception:
            return 1920, 1080

    def _hex_to_rgb(self, hex_str: str) -> Tuple[int, int, int]:
        """Converts HEX color string (e.g. '#000000') into an RGB tuple."""
        clean_hex = hex_str.lstrip("#")
        if len(clean_hex) == 6:
            try:
                return (
                    int(clean_hex[0:2], 16),
                    int(clean_hex[2:4], 16),
                    int(clean_hex[4:6], 16),
                )
            except ValueError:
                pass
        return (0, 0, 0)

    def _resolve_font(self, font_name: str) -> Optional[str]:
        """
        Resolves font family name into a valid font specification for MoviePy/Pillow.
        Fallback to standard system fonts if requested font is not directly resolvable.
        """
        candidates = [
            font_name,
            f"{font_name.lower()}.ttf",
            f"{font_name}.ttf",
            "arial.ttf",
            "calibri.ttf",
        ]
        for candidate in candidates:
            try:
                _ = TextClip(text="test", font=candidate, font_size=12, color="white")
                return candidate
            except Exception:
                pass
        return None


