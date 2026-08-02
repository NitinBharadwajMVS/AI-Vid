"""
TTS Manager Module.

Orchestrates scene-by-scene Text-to-Speech audio generation for a SceneSpecification.
Applies per-scene caching logic and updates scene voice metadata.
Does NOT perform audio alignment or word timing calculations.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from planner.scene_spec import SceneSpecification, VoiceMetadata
from voice.factory import VoiceFactory
from voice.providers.base import BaseVoiceProvider

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages scene-level TTS generation for the AI Video Generation Pipeline.
    Generates independent audio files for each scene in a SceneSpecification.
    """

    def __init__(
        self, provider: Optional[BaseVoiceProvider] = None, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes TTSManager with a VoiceProvider or configuration.

        :param provider: Concrete VoiceProvider instance. If None, uses VoiceFactory.
        :param config: Configuration dictionary.
        """
        self.config = config or {}
        self.provider = provider or VoiceFactory.create(self.config)

    def generate_voice(self, scene_spec: SceneSpecification) -> SceneSpecification:
        """
        Generates audio for every scene in the SceneSpecification.

        :param scene_spec: SceneSpecification instance containing scenes.
        :return: Updated SceneSpecification with populated scene.voice_metadata.
        :raises ValueError: If scene_spec or scenes are missing/invalid.
        """
        if not scene_spec or not isinstance(scene_spec, SceneSpecification):
            raise ValueError("Invalid SceneSpecification provided to TTSManager.")

        if not scene_spec.scenes:
            logger.warning("SceneSpecification contains 0 scenes. Skipping TTS generation.")
            return scene_spec

        temp_dir = self._get_audio_output_directory()
        logger.info(
            "Starting scene-by-scene TTS generation for %d scenes (Output dir: '%s')",
            len(scene_spec.scenes),
            temp_dir,
        )

        total_start_time = time.time()

        for scene in scene_spec.scenes:
            scene_id = scene.scene_id or "scene_unknown"
            narration = scene.narration_text.strip() if scene.narration_text else ""

            if not narration:
                logger.warning("Scene '%s' has empty narration text. Skipping audio generation.", scene_id)
                continue

            audio_file_path = str(Path(temp_dir) / f"{scene_id}.wav")

            # Check cache
            if self._is_cached(scene, audio_file_path):
                logger.info("Cache HIT for scene '%s' (File: '%s')", scene_id, audio_file_path)
                # Keep or refresh metadata if already present
                if not scene.voice_metadata:
                    scene.voice_metadata = VoiceMetadata(
                        audio_file_path=str(Path(audio_file_path).resolve()),
                        audio_duration=scene.duration,
                        voice_id=getattr(self.provider, "voice_id", "default"),
                        provider=getattr(self.provider, "provider_name", "piper"),
                    )
                continue

            logger.info("Cache MISS for scene '%s'. Synthesizing audio...", scene_id)
            start_gen_time = time.time()

            try:
                meta = self.provider.generate_audio(text=narration, output_path=audio_file_path)
                gen_duration = time.time() - start_gen_time
                logger.info(
                    "Generated audio for scene '%s' in %.4fs (Audio length: %.2fs, File: '%s')",
                    scene_id,
                    gen_duration,
                    meta.get("audio_duration", 0.0),
                    meta.get("audio_file_path"),
                )

                # Populate scene voice_metadata
                scene.voice_metadata = VoiceMetadata(
                    audio_file_path=meta.get("audio_file_path"),
                    audio_duration=float(meta.get("audio_duration", 0.0)),
                    voice_id=str(meta.get("voice_id", "")),
                    provider=str(meta.get("provider", "piper")),
                    speed=float(meta.get("speed", 1.0)),
                    pitch=float(meta.get("pitch", 1.0)),
                )

                # Leave word_timings and captions untouched (reserved for Alignment engine)
                scene.word_timings = scene.word_timings or []
                scene.captions = scene.captions or []

            except Exception as e:
                logger.error("Failed to generate audio for scene '%s': %s", scene_id, e)
                raise RuntimeError(f"TTS generation failed for scene '{scene_id}': {e}") from e

        total_elapsed = time.time() - total_start_time
        logger.info("Completed TTS generation for all scenes in %.4fs.", total_elapsed)
        return scene_spec

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_audio_output_directory(self) -> str:
        """Determines destination directory for temp scene audio files."""
        paths_cfg = self.config.get("paths", {}) if isinstance(self.config.get("paths"), dict) else {}
        base_temp = paths_cfg.get("temp", "./temp")
        audio_dir = Path(base_temp) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        return str(audio_dir)

    def _is_cached(self, scene: Any, audio_file_path: str) -> bool:
        """
        Placeholder cache validator.
        Checks if audio file exists on disk and is non-empty.
        """
        path = Path(audio_file_path)
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            # If scene already has voice_metadata pointing to a valid file
            if scene.voice_metadata and scene.voice_metadata.audio_file_path:
                return True
        return False
