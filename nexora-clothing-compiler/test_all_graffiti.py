import sys
sys.path.insert(0, '.')
from main import compile_clothing

# Test semua graffiti styles
specs = [
    {
        "name": "Graffiti FLEX",
        "spec": {
            "version": "1.0",
            "name": "Graffiti FLEX",
            "theme": "street",
            "garment": {
                "type": "shirt", "fit": "oversized", "hood": True,
                "sleeve_length": 1.0, "length": 1.0,
                "color": {"primary": "#111111", "secondary": "#333333", "accent": "#FF0000"},
                "material": {"fabric": "heavy_cotton", "roughness": 0.7, "metallic": 0.0, "normal_strength": 0.5},
                "zipper": {"style": "full", "color": "#C0C0C0", "material": "metal"},
                "pocket": {"style": "kangaroo", "position": "center", "size": 0.6},
                "stitch": {"type": "double", "color": "#000000", "distance_from_edge": 3.0, "spacing": 2.0},
                "logo": {"style": "graffiti", "motif": "FLEX", "position": "center", "scale": 0.4},
                "extras": []
            }
        }
    },
    {
        "name": "Throwup KING",
        "spec": {
            "version": "1.0",
            "name": "Throwup KING",
            "theme": "street",
            "garment": {
                "type": "tshirt", "fit": "regular", "hood": False,
                "sleeve_length": 1.0, "length": 1.0,
                "color": {"primary": "#000000", "secondary": "#222222", "accent": "#00FF00"},
                "material": {"fabric": "heavy_cotton", "roughness": 0.7, "metallic": 0.0, "normal_strength": 0.5},
                "zipper": {"style": "none", "color": "#C0C0C0", "material": "metal"},
                "pocket": {"style": "none", "position": "center", "size": 0.5},
                "stitch": {"type": "single", "color": "#333333", "distance_from_edge": 3.0, "spacing": 2.0},
                "logo": {"style": "throwup", "motif": "KING", "position": "center", "scale": 0.5},
                "extras": []
            }
        }
    },
    {
        "name": "Tag ACE",
        "spec": {
            "version": "1.0",
            "name": "Tag ACE",
            "theme": "street",
            "garment": {
                "type": "tshirt", "fit": "slim", "hood": False,
                "sleeve_length": 0.5, "length": 1.0,
                "color": {"primary": "#FFFFFF", "secondary": "#CCCCCC", "accent": "#0000FF"},
                "material": {"fabric": "heavy_cotton", "roughness": 0.7, "metallic": 0.0, "normal_strength": 0.5},
                "zipper": {"style": "none", "color": "#C0C0C0", "material": "metal"},
                "pocket": {"style": "none", "position": "center", "size": 0.5},
                "stitch": {"type": "none", "color": "#000000", "distance_from_edge": 3.0, "spacing": 2.0},
                "logo": {"style": "tag", "motif": "ACE", "position": "left_chest", "scale": 0.3},
                "extras": []
            }
        }
    },
    {
        "name": "Wildstyle VOLT",
        "spec": {
            "version": "1.0",
            "name": "Wildstyle VOLT",
            "theme": "cyberpunk",
            "garment": {
                "type": "jacket", "fit": "oversized", "hood": False,
                "sleeve_length": 1.0, "length": 0.8,
                "color": {"primary": "#1a1a1a", "secondary": "#333333", "accent": "#00FFFF"},
                "material": {"fabric": "nylon", "roughness": 0.6, "metallic": 0.0, "normal_strength": 0.4},
                "zipper": {"style": "full", "color": "#C0C0C0", "material": "metal"},
                "pocket": {"style": "side", "position": "side", "size": 0.5},
                "stitch": {"type": "double", "color": "#333333", "distance_from_edge": 3.0, "spacing": 2.0},
                "logo": {"style": "wildstyle", "motif": "VOLT", "position": "back", "scale": 0.4},
                "extras": []
            }
        }
    },
]

for item in specs:
    output_path = f"output/graffiti_{item['name'].replace(' ', '_').lower()}.png"
    template = compile_clothing(item['spec'], output_path)
    print(f"Generated: {output_path} ({template.size[0]}x{template.size[1]})")
