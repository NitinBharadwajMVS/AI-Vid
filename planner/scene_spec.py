"""
Scene Specification Module.

Defines the central schema and data structures representing the entire video structure.
This specification acts as the single source of truth passed across pipeline stages
(Planner, Voice, Alignment, Asset Generation, Renderer).
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


@dataclass
class WordTiming:
    """Represents precise start and end timing for an individual word."""
    word: str
    start_time: float = 0.0
    end_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converts WordTiming to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WordTiming":
        """Instantiates WordTiming from a dictionary."""
        return cls(
            word=data.get("word", ""),
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
        )


@dataclass
class VoiceMetadata:
    """Metadata regarding text-to-speech voice generation for a scene."""
    audio_file_path: Optional[str] = None
    audio_duration: float = 0.0
    voice_id: str = ""
    provider: str = ""
    speed: float = 1.0
    pitch: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Converts VoiceMetadata to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceMetadata":
        """Instantiates VoiceMetadata from a dictionary."""
        return cls(
            audio_file_path=data.get("audio_file_path"),
            audio_duration=float(data.get("audio_duration", 0.0)),
            voice_id=data.get("voice_id", ""),
            provider=data.get("provider", ""),
            speed=float(data.get("speed", 1.0)),
            pitch=float(data.get("pitch", 1.0)),
        )


@dataclass
class AssetReference:
    """Reference to an external visual or audio asset used in a scene."""
    asset_id: str
    asset_type: str  # e.g., 'image', 'video', 'audio'
    file_path: Optional[str] = None
    prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts AssetReference to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetReference":
        """Instantiates AssetReference from a dictionary."""
        return cls(
            asset_id=data.get("asset_id", ""),
            asset_type=data.get("asset_type", "image"),
            file_path=data.get("file_path"),
            prompt=data.get("prompt"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VisualElement:
    """Defines layout, positioning, and animation of a visual asset on frame."""
    element_id: str
    asset_reference: Optional[AssetReference] = None
    position: Dict[str, float] = field(default_factory=dict)
    animation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts VisualElement to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualElement":
        """Instantiates VisualElement from a dictionary."""
        asset_ref_data = data.get("asset_reference")
        asset_ref = AssetReference.from_dict(asset_ref_data) if asset_ref_data else None
        return cls(
            element_id=data.get("element_id", ""),
            asset_reference=asset_ref,
            position=data.get("position", {}),
            animation=data.get("animation", {}),
        )


@dataclass
class Transition:
    """Transition settings between scenes or elements."""
    type: str = "cut"  # e.g., fade, dissolve, cut, slide
    duration: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts Transition to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transition":
        """Instantiates Transition from a dictionary."""
        return cls(
            type=data.get("type", "cut"),
            duration=float(data.get("duration", 0.0)),
            parameters=data.get("parameters", {}),
        )


@dataclass
class Caption:
    """Subtitle or caption overlay data for a scene."""
    text: str
    start_time: float = 0.0
    end_time: float = 0.0
    word_timings: List[WordTiming] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts Caption to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Caption":
        """Instantiates Caption from a dictionary."""
        word_timings_raw = data.get("word_timings", [])
        return cls(
            text=data.get("text", ""),
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
            word_timings=[WordTiming.from_dict(wt) for wt in word_timings_raw],
            style=data.get("style", {}),
        )


@dataclass
class RenderSettings:
    """Global configuration settings for rendering the final video."""
    resolution: str = "1920x1080"
    aspect_ratio: str = "16:9"
    fps: int = 30
    theme: str = "dark"
    font: str = "Arial"
    background_color: str = "#000000"
    extra_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts RenderSettings to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderSettings":
        """Instantiates RenderSettings from a dictionary."""
        return cls(
            resolution=data.get("resolution", "1920x1080"),
            aspect_ratio=data.get("aspect_ratio", "16:9"),
            fps=int(data.get("fps", 30)),
            theme=data.get("theme", "dark"),
            font=data.get("font", "Arial"),
            background_color=data.get("background_color", "#000000"),
            extra_options=data.get("extra_options", {}),
        )


@dataclass
class Scene:
    """
    Data model representing a single discrete video scene and all its parameters.
    """
    scene_id: str
    narration_text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    visual_description: str = ""
    assets: List[AssetReference] = field(default_factory=list)
    visual_elements: List[VisualElement] = field(default_factory=list)
    captions: List[Caption] = field(default_factory=list)
    transition_in: Optional[Transition] = None
    transition_out: Optional[Transition] = None
    animation_metadata: Dict[str, Any] = field(default_factory=dict)
    word_timings: List[WordTiming] = field(default_factory=list)
    voice_metadata: Optional[VoiceMetadata] = None
    render_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts Scene to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scene":
        """Instantiates Scene from a dictionary."""
        t_in_data = data.get("transition_in")
        t_out_data = data.get("transition_out")
        v_meta_data = data.get("voice_metadata")

        return cls(
            scene_id=data.get("scene_id", ""),
            narration_text=data.get("narration_text", ""),
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
            duration=float(data.get("duration", 0.0)),
            visual_description=data.get("visual_description", ""),
            assets=[AssetReference.from_dict(a) for a in data.get("assets", [])],
            visual_elements=[VisualElement.from_dict(ve) for ve in data.get("visual_elements", [])],
            captions=[Caption.from_dict(c) for c in data.get("captions", [])],
            transition_in=Transition.from_dict(t_in_data) if t_in_data else None,
            transition_out=Transition.from_dict(t_out_data) if t_out_data else None,
            animation_metadata=data.get("animation_metadata", {}),
            word_timings=[WordTiming.from_dict(wt) for wt in data.get("word_timings", [])],
            voice_metadata=VoiceMetadata.from_dict(v_meta_data) if v_meta_data else None,
            render_options=data.get("render_options", {}),
        )


@dataclass
class SceneSpecification:
    """
    Central specification containing the complete description of the video to render.
    Serves as the sole contract between upstream components (planner, voice, alignment, asset generator)
    and downstream components (renderer).
    """
    title: str = "Untitled Scene Spec"
    version: str = "1.0"
    scenes: List[Scene] = field(default_factory=list)
    global_render_settings: RenderSettings = field(default_factory=RenderSettings)
    total_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the SceneSpecification object and all nested entities to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneSpecification":
        """Instantiates a SceneSpecification object from a dictionary."""
        scenes_data = data.get("scenes", [])
        render_settings_data = data.get("global_render_settings", {})
        return cls(
            title=data.get("title", "Untitled Scene Spec"),
            version=data.get("version", "1.0"),
            scenes=[Scene.from_dict(s) for s in scenes_data],
            global_render_settings=RenderSettings.from_dict(render_settings_data),
            total_duration=float(data.get("total_duration", 0.0)),
            metadata=data.get("metadata", {}),
        )

    def save_json(self, path: str) -> None:
        """Serializes the SceneSpecification object to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_json(cls, path: str) -> "SceneSpecification":
        """Deserializes a JSON file into a SceneSpecification object."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
