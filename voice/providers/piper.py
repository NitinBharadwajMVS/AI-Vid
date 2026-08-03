"""
Piper TTS Voice Provider Implementation.

Implements the BaseVoiceProvider interface for Piper TTS.
Provides standalone, offline speech synthesis capabilities.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from planner.scene_spec import VoiceMetadata
from voice.exceptions import InvalidVoiceConfiguration, VoiceGenerationError
from voice.providers.base import BaseVoiceProvider

logger = logging.getLogger(__name__)


class PiperVoiceProvider(BaseVoiceProvider):
    """
    Piper TTS Voice Provider implementation.
    Synthesizes narration text into audio files using Piper executable.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes PiperVoiceProvider with configuration parameters.
        Validates paths for executable, model, and config files upon initialization.

        :param config: Configuration dictionary for voice settings.
        :raises VoiceGenerationError: If executable, model, or config path is missing or invalid.
        :raises InvalidVoiceConfiguration: If numeric voice parameters are invalid.
        """
        super().__init__(config)
        voice_cfg = self.config.get("voice", {}) if isinstance(self.config.get("voice"), dict) else {}

        self.executable = str(voice_cfg.get("executable", "")).strip()
        self.model = str(voice_cfg.get("model", "")).strip()
        self.model_config = str(voice_cfg.get("config", "")).strip()
        self.voice_id = voice_cfg.get("voice_id", self.model or "piper_voice")

        try:
            self.speed = float(voice_cfg.get("speed", 1.0))
            self.pitch = float(voice_cfg.get("pitch", 1.0))
        except (ValueError, TypeError) as e:
            raise InvalidVoiceConfiguration(f"Invalid numeric voice configuration parameters: {e}") from e

        # Validate configuration paths
        self._validate_configuration()

        # Log resolved absolute paths
        executable_abs = Path(self.executable).resolve()
        model_abs = Path(self.model).resolve()
        config_abs = Path(self.model_config).resolve()

        logger.info("PiperVoiceProvider initialized successfully.")
        logger.info("Resolved Piper Executable Path: '%s'", executable_abs)
        logger.info("Resolved Voice Model Path: '%s'", model_abs)
        logger.info("Resolved Voice Config Path: '%s'", config_abs)

    def _validate_configuration(self) -> None:
        """
        Validates that configured executable, model, and config paths exist on disk.

        :raises VoiceGenerationError: If any path is missing or invalid.
        """
        if not self.executable:
            reason = "Piper executable path is not configured in voice settings."
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

        executable_path = Path(self.executable)
        if not executable_path.exists() or not executable_path.is_file():
            reason = f"Piper executable path is invalid or file does not exist: '{self.executable}'"
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

        if not self.model:
            reason = "Piper voice model path is not configured in voice settings."
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

        model_path = Path(self.model)
        if not model_path.exists() or not model_path.is_file():
            reason = f"Piper voice model path is invalid or file does not exist: '{self.model}'"
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

        if not self.model_config:
            reason = "Piper voice config path is not configured in voice settings."
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

        config_path = Path(self.model_config)
        if not config_path.exists() or not config_path.is_file():
            reason = f"Piper voice config path is invalid or file does not exist: '{self.model_config}'"
            logger.error("Configuration validation failed: %s", reason)
            raise VoiceGenerationError(reason)

    def synthesize(
        self, text: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> VoiceMetadata:
        """
        Synthesizes speech for the given text using Piper CLI and saves it to output_path.

        :param text: Narration text to synthesize.
        :param output_path: Destination file path for generated audio.
        :param options: Optional parameter overrides.
        :return: Strongly-typed VoiceMetadata object.
        :raises VoiceGenerationError: If input text is invalid, subprocess fails, or output file is missing.
        """
        import subprocess
        import time
        import wave

        if not text or not text.strip():
            reason = "Cannot synthesize speech for empty or whitespace narration text."
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        opts = options or {}
        executable_str = str(opts.get("executable", self.executable)).strip()
        model_str = str(opts.get("model", self.model)).strip()
        model_config_str = str(opts.get("config", self.model_config)).strip()
        speed = float(opts.get("speed", self.speed))
        pitch = float(opts.get("pitch", self.pitch))
        voice_id = str(opts.get("voice_id", self.voice_id))

        executable_path = Path(executable_str)
        model_path = Path(model_str)
        out_path = Path(output_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(executable_path),
            "--model",
            str(model_path),
            "--output_file",
            str(out_path),
        ]

        if model_config_str:
            config_path = Path(model_config_str)
            if config_path.exists():
                cmd.extend(["--config", str(config_path)])

        if speed > 0 and speed != 1.0:
            cmd.extend(["--length_scale", str(round(1.0 / speed, 4))])

        logger.info("Starting Piper synthesis...")
        logger.info("Model path: '%s'", str(model_path))
        logger.info("Output path: '%s'", str(out_path))

        start_time = time.time()

        try:
            subprocess.run(
                cmd,
                input=text.strip(),
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr.strip() if e.stderr else str(e)
            reason = f"Piper synthesis failed:\n{stderr_msg}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e
        except FileNotFoundError as e:
            reason = f"Piper executable not found:\n{executable_path}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e
        except Exception as e:
            reason = f"Failed to execute Piper process: {e}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e

        execution_time = time.time() - start_time

        if not out_path.exists() or not out_path.is_file():
            reason = "Piper finished without producing an output file."
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        duration = self._get_wav_duration(out_path)

        logger.info(
            "Piper synthesis success. Execution time: %.4fs, Generated duration: %.2fs",
            execution_time,
            duration,
        )

        return VoiceMetadata(
            audio_file_path=str(out_path.resolve()),
            audio_duration=duration,
            voice_id=voice_id,
            provider="piper",
            speed=speed,
            pitch=pitch,
        )

    def _get_wav_duration(self, wav_path: Path) -> float:
        """Calculates exact audio duration in seconds from a WAV file using stdlib 'wave' module."""
        import wave

        try:
            with wave.open(str(wav_path), "rb") as wave_file:
                frames = wave_file.getnframes()
                rate = wave_file.getframerate()
                if rate <= 0:
                    return 0.0
                return round(frames / float(rate), 2)
        except Exception:
            return 0.0



