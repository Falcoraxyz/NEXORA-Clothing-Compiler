"""
LLM Integration
Converts natural language descriptions to ClothingSpec JSON.
Uses prompt engineering to extract structured specs from text.
"""

import json
import re
from typing import Dict, Any, Optional

# System prompt for LLM to extract clothing specs
SYSTEM_PROMPT = """You are a clothing design expert for Roblox. Convert natural language descriptions into structured JSON specifications.

Available options:
- garment_type: "shirt", "tshirt", "pants"
- fit: "regular", "oversized", "slim"
- fabric: "heavy_cotton", "denim", "leather", "satin", "nylon", "wool"
- zipper_style: "none", "full", "half", "invisible"
- pocket_style: "none", "kangaroo", "chest", "side", "cargo"
- stitch_type: "none", "single", "double", "triple", "overlock"
- logo_style: "embroidery", "print", "patch"
- logo_motif: "skull", "star", "heart", "lightning", "crown", "custom"
- extras: ["chain", "belt", "patch", "hood"]

Output ONLY valid JSON matching this schema:
{
  "version": "1.0",
  "name": "Descriptive name",
  "description": "Short description",
  "theme": "style theme",
  "garment": {
    "type": "shirt|tshirt|pants",
    "fit": "regular|oversized|slim",
    "hood": true/false,
    "sleeve_length": 0.0-1.0,
    "length": 0.0-1.0,
    "color": {"primary": "#hex", "secondary": "#hex", "accent": "#hex"},
    "material": {"fabric": "type", "roughness": 0.0-1.0, "metallic": 0.0-1.0, "normal_strength": 0.0-1.0},
    "zipper": {"style": "type", "color": "#hex", "material": "metal|plastic"},
    "pocket": {"style": "type", "position": "center|side|chest", "size": 0.0-1.0},
    "stitch": {"type": "type", "color": "#hex", "distance_from_edge": 3.0, "spacing": 2.0},
    "logo": {"style": "type", "motif": "type", "position": "left_chest|right_chest|center|back", "scale": 0.1-0.5},
    "extras": ["item1", "item2"]
  }
}

Rules:
- Always include all fields
- Use reasonable defaults for missing info
- Colors should be hex codes
- If logo is not mentioned, set style to "none"
- If zipper is not mentioned, set style to "none"
- If pocket is not mentioned, set style to "none"
"""


class NLToSpecConverter:
    """Converts natural language to ClothingSpec JSON."""
    
    def __init__(self):
        self.fallback_rules = self._build_fallback_rules()
    
    def convert(self, text: str) -> Dict[str, Any]:
        """
        Convert natural language to spec JSON.
        Uses rule-based extraction (no LLM API needed).
        """
        text_lower = text.lower()
        
        # Extract garment type
        garment_type = self._extract_garment_type(text_lower)
        
        # Extract colors
        colors = self._extract_colors(text)
        
        # Extract material
        material = self._extract_material(text_lower)
        
        # Extract features
        features = self._extract_features(text_lower)
        
        # Build spec
        spec = {
            "version": "1.0",
            "name": self._generate_name(text_lower, garment_type),
            "description": text[:100],
            "theme": self._extract_theme(text_lower),
            "garment": {
                "type": garment_type,
                "fit": self._extract_fit(text_lower),
                "hood": "hood" in text_lower or "hoodie" in text_lower,
                "sleeve_length": self._extract_sleeve_length(text_lower),
                "length": 1.0,
                "color": colors,
                "material": material,
                "zipper": self._extract_zipper(text_lower, features),
                "pocket": self._extract_pocket(text_lower),
                "stitch": self._extract_stitch(text_lower),
                "logo": self._extract_logo(text_lower),
                "extras": self._extract_extras(text_lower)
            }
        }
        
        return spec
    
    def _extract_garment_type(self, text: str) -> str:
        if "t-shirt" in text or "tshirt" in text or "tee" in text:
            return "tshirt"
        elif "pant" in text or "jean" in text or "trouser" in text:
            return "pants"
        else:
            return "shirt"
    
    def _extract_colors(self, text: str) -> Dict[str, str]:
        color_map = {
            "black": "#111111",
            "white": "#FFFFFF",
            "red": "#FF0000",
            "blue": "#0000FF",
            "green": "#00FF00",
            "yellow": "#FFFF00",
            "purple": "#800080",
            "orange": "#FFA500",
            "pink": "#FFC0CB",
            "gray": "#808080",
            "grey": "#808080",
            "brown": "#8B4513",
            "navy": "#000080",
            "maroon": "#800000",
            "olive": "#808000",
            "teal": "#008080",
            "cyan": "#00FFFF",
            "silver": "#C0C0C0",
            "gold": "#FFD700",
            "bronze": "#CD7F32",
            "burgundy": "#800020",
            "charcoal": "#36454F",
            "dark": "#111111",
            "light": "#EEEEEE",
        }
        
        found_colors = []
        for name, hex_code in color_map.items():
            if name in text.lower():
                found_colors.append((name, hex_code))
        
        # Default colors
        primary = "#111111"
        secondary = "#222222"
        accent = "#FFFFFF"
        
        if found_colors:
            primary = found_colors[0][1]
        if len(found_colors) > 1:
            secondary = found_colors[1][1]
        if len(found_colors) > 2:
            accent = found_colors[2][1]
        
        return {
            "primary": primary,
            "secondary": secondary,
            "accent": accent
        }
    
    def _extract_material(self, text: str) -> Dict[str, Any]:
        fabric_map = {
            "cotton": "heavy_cotton",
            "denim": "denim",
            "jeans": "denim",
            "leather": "leather",
            "satin": "satin",
            "silk": "satin",
            "nylon": "nylon",
            "polyester": "nylon",
            "wool": "wool",
            "knit": "wool",
        }
        
        fabric = "heavy_cotton"
        for keyword, fabric_type in fabric_map.items():
            if keyword in text:
                fabric = fabric_type
                break
        
        return {
            "fabric": fabric,
            "roughness": 0.7,
            "metallic": 0.0,
            "normal_strength": 0.5
        }
    
    def _extract_features(self, text: str) -> Dict[str, bool]:
        return {
            "hood": "hood" in text or "hoodie" in text,
            "zipper": "zipper" in text or "zip" in text,
            "pocket": "pocket" in text,
            "logo": "logo" in text or "print" in text or "graphic" in text,
            "chain": "chain" in text,
            "belt": "belt" in text,
        }
    
    def _extract_fit(self, text: str) -> str:
        if "oversized" in text or "baggy" in text or "loose" in text:
            return "oversized"
        elif "slim" in text or "tight" in text or "fitted" in text:
            return "slim"
        return "regular"
    
    def _extract_sleeve_length(self, text: str) -> float:
        if "sleeveless" in text or "no sleeve" in text:
            return 0.0
        elif "short sleeve" in text:
            return 0.5
        elif "long sleeve" in text or "full sleeve" in text:
            return 1.0
        return 1.0
    
    def _extract_zipper(self, text: str, features: Dict[str, bool]) -> Dict[str, Any]:
        if not features["zipper"]:
            return {"style": "none", "color": "#C0C0C0", "material": "metal"}
        
        style = "full"
        if "half" in text:
            style = "half"
        
        return {
            "style": style,
            "color": "#C0C0C0",
            "material": "metal"
        }
    
    def _extract_pocket(self, text: str) -> Dict[str, Any]:
        if "kangaroo" in text:
            return {"style": "kangaroo", "position": "center", "size": 0.6}
        elif "chest" in text and "pocket" in text:
            return {"style": "chest", "position": "chest", "size": 0.4}
        elif "cargo" in text:
            return {"style": "cargo", "position": "side", "size": 0.7}
        elif "side" in text and "pocket" in text:
            return {"style": "side", "position": "side", "size": 0.5}
        elif "pocket" in text:
            return {"style": "kangaroo", "position": "center", "size": 0.5}
        
        return {"style": "none", "position": "center", "size": 0.5}
    
    def _extract_stitch(self, text: str) -> Dict[str, Any]:
        if "double stitch" in text:
            stitch_type = "double"
        elif "triple stitch" in text:
            stitch_type = "triple"
        else:
            stitch_type = "single"
        
        return {
            "type": stitch_type,
            "color": "#000000",
            "distance_from_edge": 3.0,
            "spacing": 2.0
        }
    
    def _extract_logo(self, text: str) -> Optional[Dict[str, Any]]:
        logo_keywords = ["logo", "print", "graphic", "design", "emblem", "patch"]
        if not any(kw in text for kw in logo_keywords):
            return None
        
        # Extract motif
        motifs = ["skull", "star", "heart", "lightning", "crown", "dragon", "flame", "rose", "cross"]
        motif = "skull"
        for m in motifs:
            if m in text:
                motif = m
                break
        
        # Extract position
        position = "left_chest"
        if "back" in text:
            position = "back"
        elif "center" in text or "chest" in text:
            position = "center"
        elif "right" in text:
            position = "right_chest"
        
        # Extract style
        style = "embroidery"
        if "print" in text:
            style = "print"
        elif "patch" in text:
            style = "patch"
        
        return {
            "style": style,
            "motif": motif,
            "position": position,
            "scale": 0.3
        }
    
    def _extract_extras(self, text: str) -> list:
        extras = []
        if "chain" in text:
            extras.append("chain")
        if "belt" in text:
            extras.append("belt")
        if "patch" in text and "logo" not in text:
            extras.append("patch")
        return extras
    
    def _extract_theme(self, text: str) -> str:
        themes = ["gangster", "rock", "military", "sport", "casual", "street", "gothic", "cyberpunk", "vintage", "minimal"]
        for theme in themes:
            if theme in text:
                return theme
        return "casual"
    
    def _generate_name(self, text: str, garment_type: str) -> str:
        # Generate a name from the description
        words = text.split()[:5]
        name = " ".join(words).title()
        if not name:
            name = f"Custom {garment_type.title()}"
        return name
    
    def _build_fallback_rules(self) -> Dict:
        """Build fallback rules for common patterns."""
        return {
            "hoodie": {
                "garment_type": "shirt",
                "hood": True,
                "zipper": {"style": "full", "color": "#C0C0C0", "material": "metal"}
            },
            "t-shirt": {
                "garment_type": "tshirt",
                "hood": False,
                "zipper": {"style": "none", "color": "#C0C0C0", "material": "metal"}
            },
            "cargo": {
                "pocket": {"style": "cargo", "position": "side", "size": 0.7},
                "extras": ["belt"]
            }
        }


def convert_nl_to_spec(text: str) -> Dict[str, Any]:
    """Convert natural language to spec JSON."""
    converter = NLToSpecConverter()
    return converter.convert(text)


if __name__ == "__main__":
    import json
    
    # Test examples
    test_cases = [
        "oversized black hoodie with silver zipper and kangaroo pocket, skull logo on chest",
        "slim fit white t-shirt with red star print in the center",
        "military cargo pants with belt, dark green denim, side pockets",
    ]
    
    for text in test_cases:
        print(f"\nInput: {text}")
        spec = convert_nl_to_spec(text)
        print(f"Output: {json.dumps(spec, indent=2)}")
