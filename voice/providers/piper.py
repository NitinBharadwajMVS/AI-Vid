"""
Piper TTS Voice Provider Implementation.

Implements the BaseVoiceProvider interface for Piper TTS.
Provides standalone, offline speech synthesis capabilities.
"""

import logging
import subprocess
import time
import wave
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

        :param config: Configuration dictionary for voice settings.
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

    def synthesize(
        self, text: str, output_path: str, options: Optional[Dict[str, Any]] = None
    ) -> VoiceMetadata:
        """
        Synthesizes speech for the given text using Piper CLI and saves it to output_path.

        :param text: Narration text to synthesize.
        :param output_path: Destination file path for generated audio.
        :param options: Optional parameter overrides.
        :return: Strongly-typed VoiceMetadata object.
        :raises VoiceGenerationError: If input text is invalid, executable/model missing,
                                       subprocess fails, or WAV creation/parsing fails.
        """
        # 1. Validate narration text
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

        # 2. Validate Piper executable and model files
        if not executable_str:
            reason = "Piper executable path is not configured."
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        executable_path = Path(executable_str)
        if not executable_path.exists() or not executable_path.is_file():
            reason = f"Piper executable missing at path: '{executable_path}'"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        if not model_str:
            reason = "Piper model path is not configured."
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        model_path = Path(model_str)
        if not model_path.exists() or not model_path.is_file():
            reason = f"Piper model file missing at path: '{model_path}'"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        # 3. Create output directory
        out_path = Path(output_path)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            reason = f"Cannot create output directory '{out_path.parent}': {e}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e

        # 4. Construct command
        cmd = [
            str(executable_path),
            "--model",
            str(model_path),
            "--output_file",
            str(out_path),
        ]

        if model_config_str:
            model_config_path = Path(model_config_str)
            if model_config_path.exists() and model_config_path.is_file():
                cmd.extend(["--config", str(model_config_path)])

        if speed > 0 and speed != 1.0:
            length_scale = round(1.0 / speed, 4)
            cmd.extend(["--length_scale", str(length_scale)])

        # 5. Log synthesis attempt
        logger.info("Starting Piper synthesis...")
        logger.info("Model path: '%s'", str(model_path))
        logger.info("Output path: '%s'", str(out_path))

        start_time = time.time()

        # 6. Execute Piper process via stdin
        try:
            subprocess.run(
                cmd,
                input=text.strip().encode("utf-8"),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            reason = f"Piper subprocess execution failed (exit code {e.returncode}): {stderr_msg.strip()}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e
        except Exception as e:
            reason = f"Failed to execute Piper process: {e}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e

        execution_time = time.time() - start_time

        # 7. Verify output WAV file exists
        if not out_path.exists() or not out_path.is_file():
            reason = f"Output WAV file missing after synthesis at '{out_path}'"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason)

        # 8. Calculate duration using Python's wave module
        duration = self._get_wav_duration(out_path)

        logger.info(
            "Piper synthesis success. Execution time: %.4fs, Generated duration: %.2fs",
            execution_time,
            duration,
        )

        # 9. Return VoiceMetadata
        return VoiceMetadata(
            audio_file_path=str(out_path.resolve()),
            audio_duration=duration,
            voice_id=voice_id,
            provider="piper",
            speed=speed,
            pitch=pitch,
        )

    def _get_wav_duration(self, wav_path: Path) -> float:
        """
        Calculates exact audio duration in seconds from a WAV file using stdlib 'wave' module.

        :param wav_path: Path to the generated WAV audio file.
        :return: Duration in seconds rounded to 4 decimal places.
        :raises VoiceGenerationError: If the file is invalid WAV or cannot be read.
        """
        try:
            with wave.open(str(wav_path), "rb") as wave_file:
                frames = wave_file.getnframes()
                rate = wave_file.getframerate()
                if rate <= 0:
                    reason = f"Invalid sample frame rate ({rate}) in WAV file '{wav_path}'"
                    logger.error("Piper synthesis failure: %s", reason)
                    raise VoiceGenerationError(reason)
                return round(frames / float(rate), 4)
        except wave.Error as e:
            reason = f"Invalid WAV file at '{wav_path}': {e}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e
        except VoiceGenerationError:
            raise
        except Exception as e:
            reason = f"Failed to read WAV file duration from '{wav_path}': {e}"
            logger.error("Piper synthesis failure: %s", reason)
            raise VoiceGenerationError(reason) from e

