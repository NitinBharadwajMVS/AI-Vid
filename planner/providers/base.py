"""
Base Planner Provider Interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PlannerProvider(ABC):
    """
    Abstract base interface for script planning providers.
    All concrete providers (heuristic, Groq, Ollama, etc.) must implement this class.
    """

    @abstractmethod
    def plan(self, script: str) -> List[Dict[str, Any]]:
        """
        Parses a narration script and returns a list of raw scene segment dictionaries.

        :param script: Cleaned narration script string.
        :return: List of dicts containing segment details (narration_text, scene_title, visual_description, etc.).
        """
        pass
