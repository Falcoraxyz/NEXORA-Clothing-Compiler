#!/usr/bin/env python3
"""
NEXORA Clothing Compiler CLI
Command-line interface for generating Roblox clothing templates.

Usage:
    python cli.py generate --spec '{"garment": {"type": "shirt", ...}}'
    python cli.py generate --spec-file spec.json
    python cli.py batch --specs-file specs.json
    python cli.py presets
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC, EXAMPLE_TSHIRT_SPEC, EXAMPLE_PANTS_SPEC
from main import compile_clothing
from batch_generate import BatchGenerator, BATCH_PRESETS


def load_spec_from_file(path: str) -> Dict[str, Any]:
    """Load spec from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def save_spec_to_file(spec: Dict[str, Any], path: str):
    """Save spec to JSON file."""
    with open(path, 'w') as f:
        json.dump(spec, f, indent=2)


def cmd_generate(args):
    """Generate a single template."""
    if args.spec:
        spec = json.loads(args.spec)
    elif args.spec_file:
        spec = load_spec_from_file(args.spec_file)
    elif args.preset:
        presets = {
            "shirt": EXAMPLE_SPEC,
            "tshirt": EXAMPLE_TSHIRT_SPEC,
            "pants": EXAMPLE_PANTS_SPEC,
        }
        spec = presets.get(args.preset)
        if not spec:
            print(f"Unknown preset: {args.preset}")
            print(f"Available: {list(presets.keys())}")
            return
    else:
        print("Provide --spec, --spec-file, or --preset")
        return
    
    output = args.output or "output/template.png"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    template = compile_clothing(spec, output)
    print(f"\nGenerated: {output} ({template.size[0]}x{template.size[1]})")


def cmd_batch(args):
    """Generate multiple templates."""
    if args.specs_file:
        specs = load_spec_from_file(args.specs_file)
    else:
        specs = BATCH_PRESETS
    
    generator = BatchGenerator(output_dir=args.output_dir)
    results = generator.generate_batch(specs)
    
    # Save results
    results_path = os.path.join(args.output_dir, "batch_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_path}")


def cmd_presets(args):
    """List available presets."""
    print("Available presets:")
    for name, spec in [("shirt", EXAMPLE_SPEC), ("tshirt", EXAMPLE_TSHIRT_SPEC), ("pants", EXAMPLE_PANTS_SPEC)]:
        print(f"  {name}: {spec['name']} ({spec['garment']['type']})")


def cmd_init(args):
    """Create a spec template file."""
    template = {
        "version": "1.0",
        "name": "My Design",
        "description": "Custom clothing design",
        "theme": "custom",
        "garment": {
            "type": "shirt",
            "fit": "regular",
            "hood": False,
            "sleeve_length": 1.0,
            "length": 1.0,
            "color": {
                "primary": "#111111",
                "secondary": "#222222",
                "accent": "#FFFFFF"
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
                "color": "#000000",
                "distance_from_edge": 3.0,
                "spacing": 2.0
            },
            "logo": {
                "style": "embroidery",
                "motif": "skull",
                "position": "left_chest",
                "scale": 0.3
            },
            "extras": []
        }
    }
    
    path = args.output or "my_spec.json"
    save_spec_to_file(template, path)
    print(f"Spec template saved to: {path}")


def main():
    parser = argparse.ArgumentParser(description="NEXORA Clothing Compiler CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a single template")
    gen_parser.add_argument("--spec", type=str, help="Spec as JSON string")
    gen_parser.add_argument("--spec-file", type=str, help="Path to spec JSON file")
    gen_parser.add_argument("--preset", type=str, choices=["shirt", "tshirt", "pants"], help="Use preset spec")
    gen_parser.add_argument("--output", "-o", type=str, help="Output file path")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Generate multiple templates")
    batch_parser.add_argument("--specs-file", type=str, help="Path to specs JSON array file")
    batch_parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    
    # Presets command
    subparsers.add_parser("presets", help="List available presets")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Create spec template")
    init_parser.add_argument("--output", "-o", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "presets":
        cmd_presets(args)
    elif args.command == "init":
        cmd_init(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
