"""
NEXORA Clothing DSL Schema
Defines the JSON structure for clothing specifications.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class GarmentType(str, Enum):
    SHIRT = "shirt"
    PANTS = "pants"
    TSHIRT = "tshirt"
    JACKET = "jacket"


class MaterialType(str, Enum):
    HEAVY_COTTON = "heavy_cotton"
    DENIM = "denim"
    LEATHER = "leather"
    SATIN = "satin"
    NYLON = "nylon"
    WOOL = "wool"


class ZipperStyle(str, Enum):
    NONE = "none"
    FULL = "full"
    HALF = "half"
    INVISIBLE = "invisible"


class PocketStyle(str, Enum):
    NONE = "none"
    KANGAROO = "kangaroo"
    SIDE = "side"
    CHEST = "chest"
    CARGO = "cargo"


class StitchType(str, Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    OVERLOCK = "overlock"


class LogoStyle(str, Enum):
    EMBROIDERY = "embroidery"
    PRINT = "print"
    PATCH = "patch"


@dataclass
class ColorSpec:
    primary: str = "#111111"
    secondary: Optional[str] = None
    accent: Optional[str] = None


@dataclass
class MaterialSpec:
    fabric: MaterialType = MaterialType.HEAVY_COTTON
    roughness: float = 0.7
    metallic: float = 0.0
    normal_strength: float = 0.5


@dataclass
class ZipperSpec:
    style: ZipperStyle = ZipperStyle.NONE
    color: str = "#C0C0C0"
    material: str = "metal"


@dataclass
class PocketSpec:
    style: PocketStyle = PocketStyle.NONE
    position: str = "center"
    size: float = 0.5


@dataclass
class StitchSpec:
    type: StitchType = StitchType.SINGLE
    color: str = "#000000"
    distance_from_edge: float = 3.0  # mm
    spacing: float = 2.0  # mm


@dataclass
class LogoSpec:
    style: LogoStyle = LogoStyle.EMBROIDERY
    motif: str = "skull"
    position: str = "left_chest"
    scale: float = 0.3


@dataclass
class GarmentSpec:
    garment_type: GarmentType = GarmentType.SHIRT
    fit: str = "regular"  # regular, oversized, slim
    hood: bool = False
    sleeve_length: float = 1.0  # 0.0 = sleeveless, 1.0 = full
    length: float = 1.0  # 0.0 = crop, 1.0 = full
    color: ColorSpec = field(default_factory=ColorSpec)
    material: MaterialSpec = field(default_factory=MaterialSpec)
    zipper: ZipperSpec = field(default_factory=ZipperSpec)
    pocket: PocketSpec = field(default_factory=PocketSpec)
    stitch: StitchSpec = field(default_factory=StitchSpec)
    logo: Optional[LogoSpec] = None
    extras: List[str] = field(default_factory=list)  # chain, belt, patch, etc.


@dataclass
class ClothingSpec:
    """
    Top-level clothing specification.
    This is what the LLM produces (Creative Director output).
    """
    version: str = "1.0"
    name: str = ""
    description: str = ""
    theme: str = ""
    garment: GarmentSpec = field(default_factory=GarmentSpec)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "theme": self.theme,
            "garment": {
                "type": self.garment.garment_type.value,
                "fit": self.garment.fit,
                "hood": self.garment.hood,
                "sleeve_length": self.garment.sleeve_length,
                "length": self.garment.length,
                "color": {
                    "primary": self.garment.color.primary,
                    "secondary": self.garment.color.secondary,
                    "accent": self.garment.color.accent,
                },
                "material": {
                    "fabric": self.garment.material.fabric.value,
                    "roughness": self.garment.material.roughness,
                    "metallic": self.garment.material.metallic,
                    "normal_strength": self.garment.material.normal_strength,
                },
                "zipper": {
                    "style": self.garment.zipper.style.value,
                    "color": self.garment.zipper.color,
                    "material": self.garment.zipper.material,
                },
                "pocket": {
                    "style": self.garment.pocket.style.value,
                    "position": self.garment.pocket.position,
                    "size": self.garment.pocket.size,
                },
                "stitch": {
                    "type": self.garment.stitch.type.value,
                    "color": self.garment.stitch.color,
                    "distance_from_edge": self.garment.stitch.distance_from_edge,
                    "spacing": self.garment.stitch.spacing,
                },
                "extras": self.garment.extras,
            },
        }
        if self.garment.logo:
            result["garment"]["logo"] = {
                "style": self.garment.logo.style.value,
                "motif": self.garment.logo.motif,
                "position": self.garment.logo.position,
                "scale": self.garment.logo.scale,
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClothingSpec":
        """Parse from dictionary (LLM JSON output)."""
        garment_data = data.get("garment", {})
        color_data = garment_data.get("color", {})
        material_data = garment_data.get("material", {})
        zipper_data = garment_data.get("zipper", {})
        pocket_data = garment_data.get("pocket", {})
        stitch_data = garment_data.get("stitch", {})
        logo_data = garment_data.get("logo")

        garment = GarmentSpec(
            garment_type=GarmentType(garment_data.get("type", "shirt")),
            fit=garment_data.get("fit", "regular"),
            hood=garment_data.get("hood", False),
            sleeve_length=garment_data.get("sleeve_length", 1.0),
            length=garment_data.get("length", 1.0),
            color=ColorSpec(
                primary=color_data.get("primary", "#111111"),
                secondary=color_data.get("secondary"),
                accent=color_data.get("accent"),
            ),
            material=MaterialSpec(
                fabric=MaterialType(material_data.get("fabric", "heavy_cotton")),
                roughness=material_data.get("roughness", 0.7),
                metallic=material_data.get("metallic", 0.0),
                normal_strength=material_data.get("normal_strength", 0.5),
            ),
            zipper=ZipperSpec(
                style=ZipperStyle(zipper_data.get("style", "none")),
                color=zipper_data.get("color", "#C0C0C0"),
                material=zipper_data.get("material", "metal"),
            ),
            pocket=PocketSpec(
                style=PocketStyle(pocket_data.get("style", "none")),
                position=pocket_data.get("position", "center"),
                size=pocket_data.get("size", 0.5),
            ),
            stitch=StitchSpec(
                type=StitchType(stitch_data.get("type", "single")),
                color=stitch_data.get("color", "#000000"),
                distance_from_edge=stitch_data.get("distance_from_edge", 3.0),
                spacing=stitch_data.get("spacing", 2.0),
            ),
            logo=LogoSpec(
                style=LogoStyle(logo_data.get("style", "embroidery")),
                motif=logo_data.get("motif", "skull"),
                position=logo_data.get("position", "left_chest"),
                scale=logo_data.get("scale", 0.3),
            ) if logo_data else None,
            extras=garment_data.get("extras", []),
        )

        return cls(
            version=data.get("version", "1.0"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            theme=data.get("theme", ""),
            garment=garment,
        )


# Example: LLM would produce this JSON
EXAMPLE_SPEC = {
    "version": "1.0",
    "name": "Gangster Hoodie",
    "description": "Oversized black hoodie with silver zipper",
    "theme": "gangster",
    "garment": {
        "type": "shirt",
        "fit": "oversized",
        "hood": True,
        "sleeve_length": 1.0,
        "length": 1.0,
        "color": {
            "primary": "#111111",
            "secondary": "#222222",
            "accent": "#C0C0C0"
        },
        "material": {
            "fabric": "heavy_cotton",
            "roughness": 0.8,
            "metallic": 0.0,
            "normal_strength": 0.6
        },
        "zipper": {
            "style": "full",
            "color": "#C0C0C0",
            "material": "metal"
        },
        "pocket": {
            "style": "kangaroo",
            "position": "center",
            "size": 0.6
        },
        "stitch": {
            "type": "double",
            "color": "#000000",
            "distance_from_edge": 3.0,
            "spacing": 2.0
        },
        "logo": {
            "style": "embroidery",
            "motif": "skull",
            "position": "left_chest",
            "scale": 0.25
        },
        "extras": ["chain"]
    }
}
