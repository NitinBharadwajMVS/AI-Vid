"""
Ollama Local LLM Planner Provider Placeholder.
"""

from typing import List, Dict, Any
from planner.providers.base import PlannerProvider


class OllamaPlannerProvider(PlannerProvider):
    """
    Ollama local LLM implementation of PlannerProvider.
    Placeholder for future integration.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def plan(self, script: str) -> List[Dict[str, Any]]:
        """
        TODO: Implement LLM script segmentation using local Ollama instance.
        """
        raise NotImplementedError("OllamaPlannerProvider is not yet implemented.")
