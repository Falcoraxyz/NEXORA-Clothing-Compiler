import sys
sys.path.insert(0, '.')
from src.compiler.nl_to_spec import convert_nl_to_spec
from main import compile_clothing

# Test dengan graffiti style
spec = {
    "version": "1.0",
    "name": "Graffiti Hoodie",
    "description": "Black hoodie with graffiti logo",
    "theme": "street",
    "garment": {
        "type": "shirt",
        "fit": "oversized",
        "hood": True,
        "sleeve_length": 1.0,
        "length": 1.0,
        "color": {
            "primary": "#111111",
            "secondary": "#333333",
            "accent": "#FF0000"
        },
        "material": {
            "fabric": "heavy_cotton",
            "roughness": 0.7,
            "metallic": 0.0,
            "normal_strength": 0.5
        },
        "zipper": {"style": "full", "color": "#C0C0C0", "material": "metal"},
        "pocket": {"style": "kangaroo", "position": "center", "size": 0.6},
        "stitch": {"type": "double", "color": "#000000", "distance_from_edge": 3.0, "spacing": 2.0},
        "logo": {"style": "graffiti", "motif": "FLEX", "position": "center", "scale": 0.4},
        "extras": []
    }
}

output_path = "output/graffiti_hoodie.png"
template = compile_clothing(spec, output_path)
print(f"\nGenerated: {output_path} ({template.size[0]}x{template.size[1]})")
