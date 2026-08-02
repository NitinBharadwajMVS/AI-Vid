"""
Logger Utility Module.

Provides centralized logger setup for the AI Video Generation Pipeline,
supporting configurable log levels (INFO, WARNING, ERROR, DEBUG) and formats.
"""

import os
import logging
from typing import Dict, Any, Optional, Union


def setup_logger(config_or_name: Optional[Union[Dict[str, Any], str]] = None) -> logging.Logger:
    """
    Configures and returns the application logger based on provided configuration dictionary or logger name.

    :param config_or_name: Configuration dictionary containing logging settings, or module logger name string.
    :return: Configured logging.Logger instance.
    """
    if isinstance(config_or_name, str):
        return logging.getLogger(config_or_name)

    config = config_or_name or {}
    logging_config = config.get("logging", {}) if isinstance(config, dict) else {}
    if not isinstance(logging_config, dict):
        logging_config = {}

    level_str = str(logging_config.get("level", "INFO")).upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level_str, logging.INFO)

    log_dir = logging_config.get("directory", "./logs")
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
        force=True,
    )

    logger = logging.getLogger("ai_video_pipeline")
    logger.setLevel(log_level)
    return logger
