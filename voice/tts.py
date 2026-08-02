"""
TTS Manager Module.

Orchestrates scene-by-scene Text-to-Speech audio synthesis for a SceneSpecification.
Applies per-scene caching logic and updates scene voice metadata directly.
Does NOT perform audio alignment or word timing calculations.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from planner.scene_spec import SceneSpecification, VoiceMetadata
from voice.exceptions import VoiceGenerationError, VoiceProviderError
from voice.factory import VoiceFactory
from voice.providers.base import BaseVoiceProvider

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages scene-level TTS synthesis for the AI Video Generation Pipeline.
    Synthesizes independent audio files for each scene in a SceneSpecification.
    """

    def __init__(
        self, provider: Optional[BaseVoiceProvider] = None, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes TTSManager with a BaseVoiceProvider or configuration.

        :param provider: Concrete BaseVoiceProvider instance. If None, uses VoiceFactory.
        :param config: Configuration dictionary.
        """
        self.config = config or {}
        self.provider = provider or VoiceFactory.create(self.config)
        logger.info("TTSManager initialized with provider: %s", self.provider.__class__.__name__)

    def generate_voice(self, scene_spec: SceneSpecification) -> SceneSpecification:
        """
        Synthesizes audio for every scene in the SceneSpecification.

        :param scene_spec: SceneSpecification instance containing scenes.
        :return: Updated SceneSpecification with populated scene.voice_metadata.
        :raises VoiceGenerationError: If scene_spec is invalid or synthesis fails.
        """
        if not scene_spec or not isinstance(scene_spec, SceneSpecification):
            raise VoiceGenerationError("Invalid SceneSpecification provided to TTSManager.")

        if not scene_spec.scenes:
            logger.warning("SceneSpecification contains 0 scenes. Skipping TTS synthesis.")
            return scene_spec

        temp_dir = self._get_audio_output_directory()
        logger.info(
            "Starting scene-by-scene TTS synthesis for %d scenes (Output dir: '%s')",
            len(scene_spec.scenes),
            temp_dir,
        )

        total_start_time = time.time()

        for scene in scene_spec.scenes:
            scene_id = scene.scene_id or "scene_unknown"
            narration = scene.narration_text.strip() if scene.narration_text else ""

            if not narration:
                logger.warning("Scene '%s' has empty narration text. Skipping audio synthesis.", scene_id)
                continue

            audio_file_path = str(Path(temp_dir) / f"{scene_id}.wav")

            # Check cache
            if self.validate_cache(scene, audio_file_path):
                logger.info(
                    "Cache HIT for Scene ID '%s' (Output file: '%s')",
                    scene_id,
                    audio_file_path,
                )
                if not scene.voice_metadata:
                    scene.voice_metadata = VoiceMetadata(
                        audio_file_path=str(Path(audio_file_path).resolve()),
                        audio_duration=scene.duration,
                        voice_id=getattr(self.provider, "voice_id", "default"),
                        provider="piper",
                    )
                continue

            logger.info("Cache MISS for Scene ID '%s'. Generation started...", scene_id)
            start_gen_time = time.time()

            try:
                # Directly assign strongly-typed VoiceMetadata object returned by provider
                scene.voice_metadata = self.provider.synthesize(text=narration, output_path=audio_file_path)

                gen_duration = time.time() - start_gen_time
                logger.info(
                    "Generation completed for Scene ID '%s' in %.4fs (Audio duration: %.2fs, Output file: '%s')",
                    scene_id,
                    gen_duration,
                    scene.voice_metadata.audio_duration,
                    scene.voice_metadata.audio_file_path,
                )

                # Leave word_timings and captions untouched (reserved for Alignment engine)
                scene.word_timings = scene.word_timings or []
                scene.captions = scene.captions or []

            except Exception as e:
                logger.error("Synthesis error for Scene ID '%s': %s", scene_id, e)
                raise VoiceGenerationError(f"TTS synthesis failed for scene '{scene_id}': {e}") from e

        total_elapsed = time.time() - total_start_time
        logger.info("Completed TTS synthesis for all scenes in %.4fs.", total_elapsed)
        return scene_spec

    # -------------------------------------------------------------------------
    # Helper & Caching Methods
    # -------------------------------------------------------------------------

    def generate_cache_key(self, scene: Any) -> str:
        """
        Generates a unique cache key for a scene based on its narration and parameters.
        Architecture placeholder for future hash-based cache lookup.
        """
        scene_id = getattr(scene, "scene_id", "unknown")
        narration = getattr(scene, "narration_text", "")
        # TODO: Implement SHA256 hashing of narration_text + voice config parameters
        return f"{scene_id}_{len(narration)}"

    def validate_cache(self, scene: Any, audio_file_path: str) -> bool:
        """
        Validates whether the cached audio file for a scene is valid and up-to-date.
        Architecture placeholder for future hash validation.
        """
        path = Path(audio_file_path)
        if path.exists() and path.is_file():
            if scene.voice_metadata and scene.voice_metadata.audio_file_path:
                return True
        return False

    def _get_audio_output_directory(self) -> str:
        """Determines destination directory for temporary scene audio files."""
        paths_cfg = self.config.get("paths", {}) if isinstance(self.config.get("paths"), dict) else {}
        base_temp = paths_cfg.get("temp", "./temp")
        audio_dir = Path(base_temp) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        return str(audio_dir)
