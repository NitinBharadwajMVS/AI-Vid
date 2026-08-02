"""
Heuristic / Rule-based Planner Provider.
"""

import re
from typing import List, Dict, Any
from planner.providers.base import PlannerProvider


class HeuristicPlannerProvider(PlannerProvider):
    """
    Rule-based semantic planner provider.
    Detects concept shifts using double newlines, sentence structure, and transition keywords.
    """

    TRANSITION_WORDS = [
        "however", "furthermore", "moreover", "meanwhile", "next", "then",
        "finally", "in conclusion", "on the other hand", "consequently",
        "in addition", "for example", "as a result", "suddenly", "firstly", "secondly"
    ]

    def plan(self, script: str) -> List[Dict[str, Any]]:
        """
        Splits script into semantic segments based on structural breaks and transition keywords.
        """
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', script) if p.strip()]

        raw_chunks: List[str] = []
        for p in paragraphs:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', p) if s.strip()]
            current_chunk = []

            for sentence in sentences:
                lower = sentence.lower()
                is_transition = any(lower.startswith(tw) for tw in self.TRANSITION_WORDS)
                if is_transition and current_chunk:
                    raw_chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                else:
                    current_chunk.append(sentence)

            if current_chunk:
                raw_chunks.append(" ".join(current_chunk))

        segments: List[Dict[str, Any]] = []
        for i, chunk in enumerate(raw_chunks, 1):
            title = self._extract_title(chunk, i)
            visual_desc = self._generate_visual_description(chunk, title)
            on_screen_text = self._suggest_on_screen_text(chunk, title)

            segments.append({
                "narration_text": chunk,
                "scene_title": title,
                "visual_description": visual_desc,
                "on_screen_text": on_screen_text,
                "animation_hint": self._suggest_animation_hint(i),
                "transition_type": "fade" if i > 1 else "cut"
            })

        return segments

    def _extract_title(self, chunk: str, index: int) -> str:
        """Extracts a short scene title from text chunk."""
        words = chunk.split()
        if len(words) <= 5:
            return chunk.strip(".!?")
        return f"Scene {index}: {' '.join(words[:4])}..."

    def _generate_visual_description(self, chunk: str, title: str) -> str:
        """Generates a visual concept description for the scene."""
        return f"Visual representation showcasing: '{title}'. Key concept focus."

    def _suggest_on_screen_text(self, chunk: str, title: str) -> str:
        """Suggests text to display on screen during the scene."""
        words = chunk.split()
        if len(words) >= 3:
            return " ".join(words[:4]).upper()
        return title.upper()

    def _suggest_animation_hint(self, index: int) -> str:
        """Suggests camera/element animation hints."""
        hints = ["slow_pan_right", "zoom_in", "static_focus", "slow_pan_left"]
        return hints[index % len(hints)]
