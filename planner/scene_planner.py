"""
Scene Planner Module.

Responsible for parsing narration scripts, cleaning text, and splitting them into
semantic concept-based scenes to assemble a SceneSpecification object.
Does NOT generate audio, images, or video rendering.
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional
from planner.scene_spec import SceneSpecification, Scene, Transition, RenderSettings
from planner.providers import PlannerProvider, get_planner_provider

logger = logging.getLogger(__name__)


class ScenePlanner:
    """
    Converts raw narration scripts into a structured SceneSpecification.
    Uses configurable PlannerProviders (heuristic, Groq, Ollama) for scene segmentation.
    """

    AVERAGE_WORDS_PER_MINUTE = 150.0  # 2.5 words per second

    def __init__(self, provider: Optional[PlannerProvider] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initializes ScenePlanner with a config dictionary or an explicit provider.
        If no provider is supplied, it reads `planner.provider` from config (defaulting to 'heuristic').
        """
        self.config = config or {}
        
        if provider:
            self.provider = provider
        else:
            planner_config = self.config.get("planner", {})
            provider_name = planner_config.get("provider", "heuristic") if isinstance(planner_config, dict) else "heuristic"
            self.provider = get_planner_provider(provider_name, config=self.config)

    def plan(self, script_text: str, output_path: Optional[str] = None) -> SceneSpecification:
        """
        Main entry point for scene planning.
        Cleans input script, delegates segmentation to the configured provider,
        enriches scenes, calculates timing boundaries, logs execution metrics,
        and returns a SceneSpecification.
        Optionally saves to JSON if output_path is provided.
        """
        start_time_seconds = time.time()
        provider_class_name = self.provider.__class__.__name__
        logger.info(f"Starting scene planning using provider: {provider_class_name}")

        cleaned_script = self._clean_text(script_text)
        raw_segments = self.provider.plan(cleaned_script)

        scenes: List[Scene] = []
        current_time = 0.0

        for idx, seg in enumerate(raw_segments, 1):
            scene_id = f"scene_{idx:03d}"
            narration = seg.get("narration_text", "")
            duration = self._estimate_duration(narration)
            start_time = current_time
            end_time = start_time + duration
            current_time = end_time

            transition_in = Transition(
                type=seg.get("transition_type", "cut"),
                duration=0.5 if seg.get("transition_type") == "fade" else 0.0
            )

            scene = Scene(
                scene_id=scene_id,
                narration_text=narration,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                visual_description=seg.get("visual_description", ""),
                transition_in=transition_in,
                animation_metadata={
                    "hint": seg.get("animation_hint", "static_focus"),
                    "scene_title": seg.get("scene_title", f"Scene {idx}")
                },
                render_options={
                    "on_screen_text": seg.get("on_screen_text", ""),
                }
            )
            scenes.append(scene)

        spec = SceneSpecification(
            title="Generated Video Scene Specification",
            scenes=scenes,
            total_duration=current_time,
            global_render_settings=RenderSettings(
                resolution=self.config.get("resolution", "1920x1080"),
                aspect_ratio=self.config.get("aspect_ratio", "16:9"),
                fps=self.config.get("fps", 30)
            )
        )

        execution_time = time.time() - start_time_seconds
        logger.info(
            f"Planner '{provider_class_name}' completed execution: "
            f"{len(scenes)} scenes generated, "
            f"estimated total duration {current_time:.2f}s, "
            f"execution time {execution_time:.4f}s"
        )

        if output_path:
            spec.save_json(output_path)

        return spec

    def _clean_text(self, raw_script: str) -> str:
        """
        Cleans and normalizes script text (removes extra spaces, unifies line breaks).
        """
        if not raw_script:
            return ""
        text = raw_script.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        return cleaned.strip()

    def _estimate_duration(self, narration_text: str) -> float:
        """
        Estimates speaking duration in seconds based on word count.
        Assumes average speaking speed of 150 words per minute (2.5 words/sec).
        """
        words = narration_text.split()
        if not words:
            return 2.0
        words_per_second = self.AVERAGE_WORDS_PER_MINUTE / 60.0
        estimated_seconds = len(words) / words_per_second
        return round(max(2.0, estimated_seconds), 2)
