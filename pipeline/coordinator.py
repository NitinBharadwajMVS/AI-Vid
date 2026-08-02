"""
Pipeline Coordinator Module.

Orchestrates the high-level execution flow of the AI Video Generation Pipeline.
Connects independent pipeline components (Planner -> Voice -> Assets -> Alignment -> Renderer)
without coupling directly to their specific internal implementations or providers.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from planner.scene_planner import ScenePlanner
from planner.scene_spec import SceneSpecification
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PipelineCoordinator:
    """
    High-level orchestrator for the AI Video Generation Pipeline.
    Manages stage transitions, environment validation, and execution logging.
    """

    def __init__(self, config: Optional[Union[str, Dict[str, Any]]] = None):
        """
        Initializes the PipelineCoordinator.

        :param config: Either a path to config.yaml (str) or a pre-loaded configuration dictionary (dict).
                       If None, defaults to loading 'config.yaml'.
        """
        self._load_env()
        self.config = self._load_configuration(config or "config.yaml")
        setup_logger(self.config)

    def run(self, script_path: str, output_path: str) -> SceneSpecification:
        """
        Runs the video generation pipeline.

        :param script_path: Path to the raw text script file.
        :param output_path: Destination path for the generated output MP4 video.
        :return: Final SceneSpecification object representing the generated pipeline state.
        """
        logger.info("Initiating pipeline execution for script: '%s'", script_path)

        # 1. Validate inputs and paths
        self._validate_paths(script_path, output_path)

        # 2. Read script content
        script_text = self._read_script(script_path)

        # 3. Stage 1: Scene Planning
        logger.info("Stage 1: Executing Scene Planner...")
        planner = ScenePlanner(config=self.config)

        paths_cfg = self.config.get("paths", {}) if isinstance(self.config.get("paths"), dict) else {}
        spec_save_dir = Path(paths_cfg.get("scene_specs", "./scene_specs"))
        spec_save_dir.mkdir(parents=True, exist_ok=True)
        spec_file_path = str(spec_save_dir / "scene_spec.json")

        try:
            scene_spec = planner.plan(script_text, output_path=spec_file_path)
            logger.info("Scene planning completed. Specification saved to '%s'", spec_file_path)
        except Exception as e:
            logger.error("Scene Planner failed during execution: %s", e)
            raise RuntimeError(f"Pipeline execution aborted due to Scene Planner failure: {e}") from e

        # Future pipeline stages (Placeholders)
        scene_spec = self._generate_voice(scene_spec)
        scene_spec = self._generate_assets(scene_spec)
        scene_spec = self._align_audio(scene_spec)
        self._render_video(scene_spec, output_path)

        logger.info("Pipeline execution completed successfully.")
        return scene_spec

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _load_env(self) -> None:
        """Loads environment variables using python-dotenv."""
        if HAS_DOTENV:
            load_dotenv()
            logger.debug("Environment variables loaded via python-dotenv.")
        else:
            logger.debug("python-dotenv not installed; skipping automatic .env loading.")

    def _load_configuration(self, config_input: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Loads configuration from dictionary or YAML file path."""
        if isinstance(config_input, dict):
            return config_input

        config_path = Path(config_input)
        if not config_path.exists():
            logger.warning("Config file '%s' not found. Using empty default configuration.", config_input)
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            if HAS_YAML:
                loaded_config = yaml.safe_load(content) or {}
            else:
                loaded_config = self._parse_simple_yaml(content)

            logger.info("Loaded configuration from '%s'", config_input)
            return loaded_config if isinstance(loaded_config, dict) else {}
        except Exception as e:
            logger.error("Invalid YAML configuration file '%s': %s", config_input, e)
            raise ValueError(f"Could not parse configuration file '{config_input}': {e}") from e

    def _parse_simple_yaml(self, text: str) -> Dict[str, Any]:
        """Simple fallback YAML parser using stdlib when PyYAML is not installed."""
        result: Dict[str, Any] = {}
        current_section: Optional[str] = None
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if not val:
                    current_section = key
                    result[current_section] = {}
                else:
                    if val.isdigit():
                        typed_val: Any = int(val)
                    elif val.replace(".", "", 1).isdigit():
                        typed_val = float(val)
                    elif val.lower() in ("true", "false"):
                        typed_val = val.lower() == "true"
                    else:
                        typed_val = val

                    if current_section and isinstance(result.get(current_section), dict):
                        result[current_section][key] = typed_val
                    else:
                        result[key] = typed_val
        return result

    def _validate_paths(self, script_path: str, output_path: str) -> None:
        """Validates that input script exists and output directory is writable/creatable."""
        path_script = Path(script_path)
        if not path_script.exists():
            raise FileNotFoundError(f"Input script file not found at path: '{script_path}'")
        if not path_script.is_file():
            raise ValueError(f"Specified script path is not a file: '{script_path}'")

        path_output = Path(output_path)
        output_dir = path_output.parent
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise PermissionError(f"Cannot create or access output directory '{output_dir}': {e}") from e

    def _read_script(self, script_path: str) -> str:
        """Reads input narration script text file."""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                raise ValueError(f"Input script at '{script_path}' is empty.")
            return content
        except Exception as e:
            logger.error("Error reading script file '%s': %s", script_path, e)
            raise

    # -------------------------------------------------------------------------
    # Future Pipeline Stages (Placeholders)
    # -------------------------------------------------------------------------

    def _generate_voice(self, scene_spec: SceneSpecification) -> SceneSpecification:
        """TODO: Generate TTS audio for each scene in future phase."""
        logger.debug("Voice generation stage skipped (Placeholder).")
        return scene_spec

    def _generate_assets(self, scene_spec: SceneSpecification) -> SceneSpecification:
        """TODO: Generate or download visual assets for each scene in future phase."""
        logger.debug("Asset generation stage skipped (Placeholder).")
        return scene_spec

    def _align_audio(self, scene_spec: SceneSpecification) -> SceneSpecification:
        """TODO: Align audio and generate word-level timings/captions in future phase."""
        logger.debug("Audio alignment stage skipped (Placeholder).")
        return scene_spec

    def _render_video(self, scene_spec: SceneSpecification, output_path: str) -> None:
        """TODO: Composite and render final MP4 video in future phase."""
        logger.debug("Video rendering stage skipped (Placeholder).")
        pass
