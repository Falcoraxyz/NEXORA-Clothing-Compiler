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
    HOODIE = "hoodie"


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
    FLAP = "flap"
    WELT = "welt"
    PATCH = "patch"


class StitchType(str, Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    OVERLOCK = "overlock"


class LogoStyle(str, Enum):
    NONE = "none"
    EMBROIDERY = "embroidery"
    PRINT = "print"
    PATCH = "patch"
    GRAFFITI = "graffiti"
    THROWUP = "throwup"
    TAG = "tag"
    WILDSTYLE = "wildstyle"


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

    @property
    def is_valid(self) -> bool:
        return self.style != LogoStyle.NONE and self.motif != "none" and self.position != "none"


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

    def __post_init__(self):
        """Ensure colors have good contrast."""
        primary = self.color.primary
        accent = self.color.accent
        
        # If accent is too similar to primary, auto-adjust
        if self._color_distance(primary, accent) < 80:
            # Make accent brighter/more contrasting
            self.color.accent = self._contrast_color(primary)

    def _color_distance(self, c1: str, c2: str) -> float:
        """Calculate distance between two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5

    def _contrast_color(self, hex_color: str) -> str:
        """Generate a contrasting color."""
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        brightness = (r + g + b) / 3
        
        if brightness < 128:
            # Dark color → return bright accent
            return "#FFFFFF" if brightness < 64 else "#FF4444"
        else:
            # Light color → return dark accent
            return "#111111"


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
                style=LogoStyle(logo_data.get("style", "none")),
                motif=logo_data.get("motif", "none"),
                position=logo_data.get("position", "none"),
                scale=logo_data.get("scale", 0.0),
            ) if logo_data and logo_data.get("style") != "none" else None,
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

# T-Shirt example (single 512×512 panel)
EXAMPLE_TSHIRT_SPEC = {
    "version": "1.0",
    "name": "Band Tee",
    "description": "Simple black band t-shirt with logo",
    "theme": "rock",
    "garment": {
        "type": "tshirt",
        "fit": "regular",
        "hood": False,
        "sleeve_length": 1.0,
        "length": 1.0,
        "color": {
            "primary": "#000000",
            "secondary": "#FFFFFF",
            "accent": "#FF0000"
        },
        "material": {
            "fabric": "heavy_cotton",
            "roughness": 0.7,
            "metallic": 0.0,
            "normal_strength": 0.5
        },
        "zipper": {
            "style": "none",
            "color": "#C0C0C0",
            "material": "metal"
        },
        "pocket": {
            "style": "none",
            "position": "center",
            "size": 0.5
        },
        "stitch": {
            "type": "single",
            "color": "#333333",
            "distance_from_edge": 3.0,
            "spacing": 2.0
        },
        "logo": {
            "style": "print",
            "motif": "star",
            "position": "center",
            "scale": 0.4
        },
        "extras": []
    }
}

# Jacket example
EXAMPLE_JACKET_SPEC = {
    "version": "1.0",
    "name": "Bomber Jacket",
    "description": "Classic bomber jacket with ribbed cuffs",
    "theme": "street",
    "garment": {
        "type": "jacket",
        "fit": "regular",
        "hood": False,
        "sleeve_length": 1.0,
        "length": 0.8,
        "color": {
            "primary": "#2F4F2F",
            "secondary": "#1a1a1a",
            "accent": "#C0C0C0"
        },
        "material": {
            "fabric": "nylon",
            "roughness": 0.6,
            "metallic": 0.0,
            "normal_strength": 0.4
        },
        "zipper": {
            "style": "full",
            "color": "#C0C0C0",
            "material": "metal"
        },
        "pocket": {
            "style": "side",
            "position": "side",
            "size": 0.5
        },
        "stitch": {
            "type": "double",
            "color": "#1a1a1a",
            "distance_from_edge": 3.0,
            "spacing": 2.0
        },
        "logo": {
            "style": "patch",
            "motif": "lightning",
            "position": "back",
            "scale": 0.35
        },
        "extras": []
    }
}

# Pants example
EXAMPLE_PANTS_SPEC = {
    "version": "1.0",
    "name": "Cargo Pants",
    "description": "Military-style cargo pants with pockets",
    "theme": "military",
    "garment": {
        "type": "pants",
        "fit": "regular",
        "hood": False,
        "sleeve_length": 1.0,
        "length": 1.0,
        "color": {
            "primary": "#3B5323",
            "secondary": "#2F4F2F",
            "accent": "#8B7355"
        },
        "material": {
            "fabric": "denim",
            "roughness": 0.8,
            "metallic": 0.0,
            "normal_strength": 0.6
        },
        "zipper": {
            "style": "none",
            "color": "#C0C0C0",
            "material": "metal"
        },
        "pocket": {
            "style": "cargo",
            "position": "side",
            "size": 0.7
        },
        "stitch": {
            "type": "single",
            "color": "#8B7355",
            "distance_from_edge": 3.0,
            "spacing": 2.0
        },
        "logo": {
            "style": "none",
            "motif": "none",
            "position": "none",
            "scale": 0.0
        },
        "extras": ["belt"]
    }
}
