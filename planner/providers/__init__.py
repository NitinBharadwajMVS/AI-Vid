"""
Planner Providers Package.
Exposes available provider classes and factory function.
"""

from typing import Dict, Any
from planner.providers.base import PlannerProvider
from planner.providers.heuristic import HeuristicPlannerProvider
from planner.providers.groq import GroqPlannerProvider
from planner.providers.ollama import OllamaPlannerProvider


PROVIDERS = {
    "heuristic": HeuristicPlannerProvider,
    "groq": GroqPlannerProvider,
    "ollama": OllamaPlannerProvider,
}


def get_planner_provider(provider_name: str, config: Dict[str, Any] = None) -> PlannerProvider:
    """
    Factory function to instantiate the requested planner provider based on name.
    """
    name = (provider_name or "heuristic").lower()
    if name not in PROVIDERS:
        raise ValueError(f"Unknown planner provider '{provider_name}'. Supported providers: {list(PROVIDERS.keys())}")
    
    provider_cls = PROVIDERS[name]
    if name == "heuristic":
        return provider_cls()
    return provider_cls(config=config)
